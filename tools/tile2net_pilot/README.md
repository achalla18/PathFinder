# Tile2Net sidewalk detection pilot (Frederick)

Tests whether sidewalks detected in aerial imagery are accurate enough to fill street sides that
no survey or OSM records. The pass mark, decision rule and pilot cells were fixed in
`docs/PROGRESS.md` (Decisions log, 2026-10-16) before anything was run.

- `frederick_pilot.ipynb` runs [Tile2Net](https://github.com/VIDA-NYU/tile2net) (BSD-3) on a
  Google Colab GPU. This laptop has no NVIDIA GPU, which Tile2Net needs.
  - **Input:** MD iMAP six-inch imagery (2023–25), exported per zoom-19 tile, for three 1 km
    cells.
  - **What goes to Colab:** only public imagery and the cell bounds. The City of Frederick
    survey (internal use only) and the scoring stay on this machine.
  - **To run:** open it in Colab, choose a T4 GPU runtime, run all, and keep the downloaded
    `frederick_pilot_results.zip`.
- **Result (2026-10-17):** run on this laptop's CPU instead (about 20 min per cell, patched to
  skip its CUDA check); it **failed the bar**: "sidewalk" answers 85.7% correct and "no
  sidewalk" answers 83.7%, against 95% needed. See `docs/PROGRESS.md`. Tile2Net 0.5 writes
  polygons as parquet; repack them as GeoPackage before running `score.py`.
- **Retraining (protocol fixed 2026-10-17 in `docs/PROGRESS.md`):**
  - `retrain_lib.py` holds the fine-tuning code. `retrain_colab.ipynb` embeds it; the notebook is
    built from it by a scratch script, so edit the library, not the notebook.
  - Upload `labels_for_colab.zip`: chip bounds and OSM-only masks. The surveys only picked the chips.
  - In Colab: T4 GPU, Run all, then download `MyDrive/pathfinder_retrain/out/best.pth`.
  - Locally, run inference on the three cells with `T2N_SNAPSHOT=<best.pth>`, then score once with
    the frozen `score.py`.
  - `train_kaggle.py` is the version that ran on Kaggle; the dataset it reads holds the chip images too.
  - **Result (2026-10-19):** trained on a Kaggle T4 (same library and protocol), scored once: it
    **failed the bar**. "Sidewalk" answers were 80.9% correct; "no sidewalk" answers were 100% correct,
    but there were only 26 of them. Not used; the test set is spent. See `docs/PROGRESS.md`.
- Scoring happens locally against `pilot/testset.parquet`: 60 sides where the survey and OSM
  agree there is a sidewalk, plus hand-labelled sides with none.
