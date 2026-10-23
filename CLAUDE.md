# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository state

This is an example repository for an ML course. The goal is a linear regression that predicts VO2max for cycling, served on a web page where Apple Watch users type in a ride summary.

The user trains the model themselves to learn. Do not write training code or train models unless explicitly asked.

The data is the "Graded Incremental Test Data" study (Trinity College Dublin, Zenodo). The repository is not under git and has no tests or lint config.

## Layout

- `data/xlsx/`: 835 per-test workbooks (`A<id>.xlsx`) plus `Data_Summary.xlsx`, which has one row per file with its sport.
- `data/utils/build_cycling_csv.py`: builds `data/cycling_tests.csv`, one row per cycling test. The user has edited that CSV by hand: it is `;`-separated and the VO2max outlier was removed. Read it with `sep=None, engine="python"`, and don't overwrite it without asking.
- `data/utils/plot_cycling_stages.py`: matplotlib scatter plots by gender. By default it plots per-test VO2max; `--stages` plots per-stage data from `data/cycling_stages.csv`. Its default CSV paths assume the script sits in the repository root, so pass `--csv` if they no longer resolve.
- `src/utils/power_estimation.py`: `estimate_mean_power()` / `estimate_mean_power_per_kg()` turn distance, duration, ascent and weight into watts using a physics model (climbing + rolling resistance + air drag).
- `src/utils/linear_regression.py` and `src/training/`: the user's own training code.
- `src/web/`: Django site (`config/` settings, `predictor/` app) styled with Tailwind via the Play CDN. It has no database and stores nothing. `config/settings.py` puts `src/` on `sys.path`, so the views import `utils.power_estimation`.
- `build/` and `config.codekit3`: these appear to be CodeKit output and config. Edit `src/`, not `build/`.

## Commands

```bash
python3 -m venv .venv && .venv/bin/pip install pandas openpyxl scikit-learn matplotlib django
.venv/bin/python data/utils/build_cycling_csv.py data/xlsx -o data/cycling_tests.csv
.venv/bin/python data/utils/build_cycling_csv.py data/xlsx --stages -o data/cycling_stages.csv
.venv/bin/python data/utils/plot_cycling_stages.py --csv data/cycling_tests.csv [--x age] [-o out.png]
cd src/web && ../../.venv/bin/python manage.py runserver   # http://127.0.0.1:8000
```

## Model contract (web ↔ training)

`src/web/predictor/ml.py` reads `src/web/predictor/model.json` on every request, so there's no need to restart the server after a new export. The file has this format:

```json
{"intercept": number, "coefficients": {feature: number}, "mae": number (optional), "ranges": {feature: [min, max]} (optional)}
```

Allowed feature names, in the same units as `cycling_tests.csv`:

| Feature | Unit |
|---|---|
| `male` | 1 or 0 |
| `age` | years |
| `height` | m |
| `weight` | kg |
| `mean_hr` | bpm |
| `mean_power_per_kg` | W/kg |

Without `model.json`, the page shows only the estimated power, plus a notice. The view computes `mean_power_per_kg` with `power_estimation.estimate_mean_power`, and `web/config/settings.py` adds the repo root to `sys.path` so that import works.

Features must be things a user can enter after a ride (no power meter, no time series). Don't add lab-only measurements (stage VO2, lactate, Sheet3 threshold metrics).

## Data layout (`data/xlsx/A<id>.xlsx`)

The workbooks have three unnamed sheets, so the structure is positional:

- **Sheet1**: label/value pairs: `Name:`, `Gender:`, `Event:`, `Test:`, `Test Date:`, `DOB:`, `Height`, `Weight`, body composition and blood values.
  - `Test Date` is an Excel serial number or a date.
  - `DOB` is often `dd/mm/yyyy` text.
  - `Name:` is identifying information and must never be written to outputs.
- **Sheet2**: one row per stage: `Actual Power` (`Velocity` for running), `HR`, `VO2`, `Bla`, `SR/Cadence`.
  - Stage 1 is a 0 W rest measurement.
  - Stages are power steps of 20–40 W. Stage duration isn't recorded.
- **Sheet3**: label/value metrics: `VO2max` (the target, mL/kg/min), `VO2max (absolute)`, `Hrmax`, and threshold values (`@ Tlac`, `@ 2mmol`, `@ 160 bpm`).

A test counts as cycling when its `Test:` field is `Cycling` (285 tests); `Event` can differ, e.g. triathletes. Values are hand-entered, so expect blanks holding a single space, trailing spaces in `Gender`, and occasional implausible values.
