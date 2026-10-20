"""PathFinder: fine-tune Tile2Net on Maryland sidewalks, on a Kaggle GPU (protocol: docs/PROGRESS.md, 2026-10-17).

The attached private dataset holds chips.csv, OSM-only masks, the public MD iMAP chip images and
retrain_lib.py (the same file as tools/tile2net_pilot/retrain_lib.py). Output: /kaggle/working/out/best.pth.
"""
import glob, json, subprocess, sys
from pathlib import Path

COMMIT = "c737a4e8c8b907ee3c80739673c67140ce95483d"
sh = lambda c: subprocess.run(c, shell=True, check=True)
sh("nvidia-smi --query-gpu=name,memory.total --format=csv")
sh(f"git clone -q https://github.com/VIDA-NYU/tile2net.git /kaggle/tmp/tile2net && cd /kaggle/tmp/tile2net && git checkout -q {COMMIT}")
# No dependency resolution: keep Kaggle's own torch build; add only what the model code imports.
sh("pip install -q --no-deps /kaggle/tmp/tile2net && pip install -q argh==0.29.4 tabulate toolz more-itertools")

print(subprocess.run("find /kaggle/input -maxdepth 3 | head -20", shell=True, capture_output=True, text=True).stdout)
DS = Path(glob.glob("/kaggle/input/**/chips.csv", recursive=True)[0]).parent
sys.path.insert(0, str(DS))
import zipfile
def folder(name):
    """The uploaded img/ and masks/ folders, wherever Kaggle unpacked them (or unzipped here)."""
    hits = [Path(p).parent for p in glob.glob(f"/kaggle/input/**/{name}/*.png", recursive=True)]
    if hits:
        return hits[0]
    z = next(Path("/kaggle/input").rglob(f"{name}.zip"))
    zipfile.ZipFile(z).extractall(f"/kaggle/tmp/{name}_x")
    return Path(glob.glob(f"/kaggle/tmp/{name}_x/**/*.png", recursive=True)[0]).parent
IMG, MASKS = folder("img"), folder("masks")
print("images", IMG, "masks", MASKS)
import pandas as pd, torch
import retrain_lib as L
from tile2net.raster.weights import ensure_weights, weights_directory

print("retrain_lib sha256", L.sha256(DS / "retrain_lib.py"))
ensure_weights()  # downloads and checks the released checkpoints
chips = pd.read_csv(DS / "chips.csv")
missing = [n for n in chips["name"] if not (IMG / f"{n}.png").exists()]
if missing:
    raise SystemExit(f"images missing for {missing}")
train_names, val_names = L.split_names(chips)
print(len(train_names), "train,", len(val_names), "validation")

OUT = Path("/kaggle/working/out")
dev = torch.device("cuda")
log_f = open("/kaggle/working/train_log.txt", "a")
def log(s):
    print(s, flush=True); log_f.write(s + "\n"); log_f.flush()

net = L.build_model(weights_directory())
try:
    hist = L.train(net, train_names, val_names, IMG, MASKS, OUT, dev,
                   crop=768, batch=2, accumulate=1, log=log)
except torch.OutOfMemoryError:
    log("out of GPU memory at batch 2; same effective batch as 1 x 2 accumulated")
    del net; torch.cuda.empty_cache()
    for f in OUT.glob("*"):
        f.unlink()
    net = L.build_model(weights_directory())
    hist = L.train(net, train_names, val_names, IMG, MASKS, OUT, dev,
                   crop=768, batch=1, accumulate=2, log=log)
pd.DataFrame(hist).to_csv(OUT / "history.csv", index=False)
(OUT / "last.pt").unlink(missing_ok=True)  # optimizer state; not needed and doubles the download
ck = torch.load(OUT / "best.pth", map_location="cpu", weights_only=False)
log(f"best epoch {ck['epoch']} {json.dumps(ck['val'])}")
log(f"best.pth sha256 {L.sha256(OUT / 'best.pth')}")
