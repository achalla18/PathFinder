"""Fine-tune Tile2Net's released model on Maryland chips (protocol: docs/PROGRESS.md, 2026-10-17).

Used by retrain_colab.ipynb on a GPU, and smoke-tested on the CPU before any training.
Labels (masks/<chip>.png) come from OSM alone: 0 sidewalk, 1 not sidewalk, 255 ignored.
Only the sidewalk output (Tile2Net class 0) is trained, with a class-balanced binary loss.
"""

from __future__ import annotations

import hashlib
import io
import random
import time
from pathlib import Path

import numpy as np
import requests
import torch
import torch.nn.functional as F
from PIL import Image

IMG = "https://mdgeodata.md.gov/imagery/rest/services/SixInch/SixInchImagery2023_2024_2025/MapServer/export"
SIDEWALK, NOT_SIDEWALK, IGNORE = 0, 1, 255
MEAN, STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)  # Tile2Net's input normalization
OCR_ALPHA = 0.4  # Tile2Net's weight on the auxiliary head

# Fixed by the protocol before training.
BASE_LR, MOMENTUM, WEIGHT_DECAY, POLY_POWER, MAX_EPOCHS = 1e-3, 0.9, 1e-4, 0.9, 15


def fetch_chip(chip, path: Path, tries: int = 8) -> bool:
    """One 1024 px export per chip from MD iMAP (matches 16 stitched zoom-19 tiles)."""
    if path.exists():
        return True
    p = {"bbox": f"{chip['xmin']:.3f},{chip['ymin']:.3f},{chip['xmax']:.3f},{chip['ymax']:.3f}",
         "bboxSR": 3857, "imageSR": 3857, "size": "1024,1024", "format": "png24",
         "transparent": "false", "f": "image"}
    for k in range(tries):
        try:
            im = Image.open(io.BytesIO(requests.get(IMG, params=p, timeout=90).content)).convert("RGB")
            if np.asarray(im).std() > 8:  # the service sometimes returns blank images
                path.parent.mkdir(parents=True, exist_ok=True)
                im.save(path)
                return True
        except Exception as exc:  # network errors: retry
            print("retry", chip["name"], exc)
        time.sleep(2 + 2 * k)
    return False


def build_model(weights_dir: Path):
    """Tile2Net's MscaleOCR (HRNet-W48) with the released satellite_2021 weights, every tensor loaded."""
    from tile2net.tileseg.config import cfg, torch_version_float
    cfg.immutable(False)
    cfg.OPTIONS.TORCH_VERSION = torch_version_float()  # as Tile2Net's assert_and_infer_cfg sets
    cfg.MODEL.BNFUNC = torch.nn.BatchNorm2d
    cfg.DATASET.NUM_CLASSES = 4
    cfg.MODEL.MSCALE = True
    cfg.MODEL.HRNET_CHECKPOINT = ""  # no ImageNet init: replaced below by the full released weights
    from tile2net.tileseg.network.ocrnet import MscaleOCR
    net = MscaleOCR(4, trunk="hrnetv2", criterion=sidewalk_loss)
    ck = torch.load(weights_dir / "satellite_2021.pth", map_location="cpu", weights_only=False)
    sd = {k.removeprefix("module."): v for k, v in ck["state_dict"].items()}
    missing, unexpected = net.load_state_dict(sd, strict=False)
    if missing:
        raise RuntimeError(f"weights missing for {len(missing)} tensors, e.g. {missing[:3]}")
    print(f"loaded all {len(net.state_dict())} tensors; {len(unexpected)} unused keys in the checkpoint")
    return net


def freeze_batchnorm(net):
    """Batches of 1-2 chips give useless batch statistics; keep the released ones."""
    for m in net.modules():
        if isinstance(m, torch.nn.BatchNorm2d):
            m.eval()
            for p in m.parameters():
                p.requires_grad_(False)


def sidewalk_loss(logits, gts, do_rmi=None):
    """Class-balanced binary loss on P(sidewalk); the other three classes only share 1 - P."""
    if logits.shape[-2:] != gts.shape[-2:]:
        logits = F.interpolate(logits, size=gts.shape[-2:], mode="bilinear", align_corners=False)
    lsm = torch.log_softmax(logits.float(), dim=1)
    log_p = lsm[:, SIDEWALK]
    log_not = torch.logsumexp(lsm[:, 1:], dim=1)
    pos, neg = gts == SIDEWALK, gts == NOT_SIDEWALK
    terms = []
    if pos.any():
        terms.append(-log_p[pos].mean())
    if neg.any():
        terms.append(-log_not[neg].mean())
    return sum(terms) / max(len(terms), 1)


def to_tensor(rgb: np.ndarray) -> torch.Tensor:
    x = torch.from_numpy(rgb).float().permute(2, 0, 1) / 255.0
    return (x - torch.tensor(MEAN)[:, None, None]) / torch.tensor(STD)[:, None, None]


def augment(rgb: np.ndarray, mask: np.ndarray, crop: int, rng: random.Random):
    """Random crop, flips, quarter turns and mild brightness/contrast change."""
    h, w = mask.shape
    y, x = rng.randint(0, h - crop), rng.randint(0, w - crop)
    rgb, mask = rgb[y:y + crop, x:x + crop], mask[y:y + crop, x:x + crop]
    k = rng.randint(0, 3)
    rgb, mask = np.rot90(rgb, k), np.rot90(mask, k)
    if rng.random() < 0.5:
        rgb, mask = rgb[:, ::-1], mask[:, ::-1]
    a, b = rng.uniform(0.85, 1.15), rng.uniform(-15, 15)
    rgb = np.clip(rgb.astype(np.float32) * a + b, 0, 255).astype(np.uint8)
    return np.ascontiguousarray(rgb), np.ascontiguousarray(mask)


def load_pair(img_dir: Path, mask_dir: Path, name: str):
    return (np.array(Image.open(img_dir / f"{name}.png").convert("RGB")),
            np.array(Image.open(mask_dir / f"{name}.png")))


@torch.no_grad()
def validate(net, names, img_dir, mask_dir, device) -> dict:
    """Sidewalk precision, recall and F1 over non-ignored pixels, full chips, as at inference."""
    net.eval()
    tp = fp = fn = 0
    for n in names:
        rgb, m = load_pair(img_dir, mask_dir, n)
        with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
            out = net({"images": to_tensor(rgb)[None].to(device)})["pred"]
        pred = out.argmax(1)[0].cpu().numpy() == SIDEWALK
        lab = m != IGNORE
        tp += int((pred & (m == SIDEWALK)).sum())
        fp += int((pred & (m == NOT_SIDEWALK)).sum())
        fn += int((~pred & (m == SIDEWALK) & lab).sum())
    prec = tp / max(tp + fp, 1)
    rec = tp / max(tp + fn, 1)
    return {"precision": prec, "recall": rec, "f1": 2 * prec * rec / max(prec + rec, 1e-9)}


def train(net, train_names, val_names, img_dir, mask_dir, out_dir: Path, device,
          crop=768, batch=2, accumulate=1, max_epochs=MAX_EPOCHS, seed=0, log=print):
    """SGD with poly decay; keeps the epoch with the best validation F1 (and resumes from last.pt)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    net.to(device)
    params = [p for p in net.parameters() if p.requires_grad]
    opt = torch.optim.SGD(params, lr=BASE_LR, momentum=MOMENTUM, weight_decay=WEIGHT_DECAY)
    scaler = torch.amp.GradScaler(enabled=device.type == "cuda")
    steps_per_epoch = max(len(train_names) // (batch * accumulate), 1)
    total = steps_per_epoch * max_epochs
    start, best, history = 0, -1.0, []
    last = out_dir / "last.pt"
    if last.exists():
        ck = torch.load(last, map_location="cpu", weights_only=False)
        net.load_state_dict(ck["model"]); opt.load_state_dict(ck["opt"])
        start, best, history = ck["epoch"] + 1, ck["best"], ck["history"]
        log(f"resumed after epoch {ck['epoch']}")
    if start == 0:
        v = validate(net, val_names, img_dir, mask_dir, device)
        history.append({"epoch": -1, **v}); log(f"released weights: val {v}")
        best = v["f1"]; save_best(net, out_dir, -1, v)
    for epoch in range(start, max_epochs):
        rng = random.Random(seed * 1000 + epoch)
        order = train_names[:]; rng.shuffle(order)
        net.train(); freeze_batchnorm(net)
        t0, losses = time.time(), []
        for s in range(steps_per_epoch):
            it = epoch * steps_per_epoch + s
            for g in opt.param_groups:
                g["lr"] = BASE_LR * (1 - it / total) ** POLY_POWER
            opt.zero_grad(set_to_none=True)
            for a in range(accumulate):
                chunk = order[(s * accumulate + a) * batch:(s * accumulate + a + 1) * batch]
                if not chunk:
                    continue
                pairs = [augment(*load_pair(img_dir, mask_dir, n), crop, rng) for n in chunk]
                x = torch.stack([to_tensor(r) for r, _ in pairs]).to(device)
                y = torch.stack([torch.from_numpy(m.astype(np.int64)) for _, m in pairs]).to(device)
                with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                    loss = net({"images": x, "gts": y}) / accumulate
                scaler.scale(loss).backward()
                losses.append(float(loss) * accumulate)
            scaler.step(opt); scaler.update()
        v = validate(net, val_names, img_dir, mask_dir, device)
        history.append({"epoch": epoch, "loss": float(np.mean(losses)), **v})
        log(f"epoch {epoch}: loss {np.mean(losses):.4f}, val {v}, {time.time() - t0:.0f} s")
        if v["f1"] > best:
            best = v["f1"]; save_best(net, out_dir, epoch, v)
        torch.save({"model": net.state_dict(), "opt": opt.state_dict(), "epoch": epoch,
                    "best": best, "history": history}, last)
    return history


def save_best(net, out_dir: Path, epoch: int, v: dict):
    """In Tile2Net's checkpoint format ('module.' keys), so its inference can load it."""
    sd = {"module." + k: t.detach().cpu() for k, t in net.state_dict().items()}
    torch.save({"state_dict": sd, "epoch": epoch, "val": v}, out_dir / "best.pth")


def split_names(chips):
    return ([c for c, s in zip(chips["name"], chips["split"]) if s == "train"],
            [c for c, s in zip(chips["name"], chips["split"]) if s == "val"])


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()
