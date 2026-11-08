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
- `src/utils/train_model.py`: the training pipeline. Self-contained: `train()` reads `data/cycling_tests.csv`, splits, one-hot encodes, fits, evaluates, keeps only the columns in its `FEATURES` list, writes `src/utils/model.bin`. Run from `src/`: `../.venv/bin/python -m utils.train_model`.
- `src/service/`: FastAPI prediction service (`app.py`). `POST /predict` takes a metric ride summary, estimates power with `utils.power_estimation` and applies the model from `src/utils/model.bin`; `GET /health`; docs at `/docs`. Run it from `src/` so `utils` imports.
- `src/web/`: Django site (`config/` settings, `predictor/` app), the form only: it validates, converts imperial to metric and POSTs to the service at `VO2MAX_SERVICE_URL` (default `http://127.0.0.1:8001`). No database, stores nothing. CSS is built with `django-tailwind-cli` and served by WhiteNoise in production.
- `render.yaml`: Render Blueprint with two free web services, `cyclingml-api` and `cyclingml-web`. Custom subdomain: add it to the web service in the Render dashboard, CNAME it to `cyclingml-web.onrender.com`, and add it to `DJANGO_ALLOWED_HOSTS` / `DJANGO_CSRF_TRUSTED_ORIGINS`.
- `build/` and `config.codekit3`: these appear to be CodeKit output and config. Edit `src/`, not `build/`.

## Commands

```bash
python3 -m venv .venv && .venv/bin/pip install pandas openpyxl scikit-learn matplotlib django django-tailwind-cli gunicorn whitenoise fastapi "uvicorn[standard]"
.venv/bin/python data/utils/build_cycling_csv.py data/xlsx -o data/cycling_tests.csv
.venv/bin/python data/utils/build_cycling_csv.py data/xlsx --stages -o data/cycling_stages.csv
.venv/bin/python data/utils/plot_cycling_stages.py --csv data/cycling_tests.csv [--x age] [-o out.png]
cd src && ../.venv/bin/python -m utils.train_model                       # train, writes src/utils/model.bin
cd src && ../.venv/bin/uvicorn service.app:app --port 8001 --reload   # API, http://127.0.0.1:8001/docs
cd src/web && ../../.venv/bin/python manage.py runserver               # page, http://127.0.0.1:8000
```

## Model contract (service ↔ training)

`src/service/app.py` loads `src/utils/model.bin` (override with `VO2MAX_MODEL_PATH`) and reloads it when the file changes, so no restart is needed after a new export. It is a joblib dump of `(dv, model)`: a fitted `DictVectorizer` and the regression. The service does no training. For Render, commit `model.bin`.

The service passes `dv.transform` a dict with these keys, in the same names and units as `cycling_tests.csv`. `dv` ignores keys it wasn't fit on, so any subset works:

| Feature | Value |
|---|---|
| `gender` | `"F"` or `"M"` (one-hot encoded by `dv`) |
| `age` | years |
| `height` | m |
| `weight` | kg |
| `mean_hr` | bpm |
| `mean_power_per_kg` | W/kg |

Without `model.bin`, `/predict` returns the power with `vo2max: null` and a notice, which the page shows.

`utils.train_model.FEATURES` selects the training columns, so other CSV columns (`test_id`, `hrmax`, `hr_rest`) are ignored without being deleted. Keep it in sync with this table.

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
