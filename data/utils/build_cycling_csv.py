#!/usr/bin/env python3
"""Merge every cycling test of the Trinity College Dublin graded incremental
test dataset (Zenodo) into a single CSV for a VO2max regression.

Usage
-----
  python build_cycling_csv.py data/                 # -> cycling_tests.csv (one row per test)
  python build_cycling_csv.py data.zip              # also works on the Zenodo zip
  python build_cycling_csv.py data/ --stages        # -> cycling_stages.csv (one row per test stage)

Options: -o/--output FILE.
Requirements: pip install pandas openpyxl

Only values a user can also enter on the web form after a ride are kept:

  vo2max             target, mL/kg/min (Sheet3 "VO2max")
  gender             M / F
  age                years at the test date
  height, weight     m, kg
  hrmax              maximal heart rate (Sheet3 "Hrmax")
  hr_rest            heart rate of the 0 W stage, a stand-in for resting HR
  mean_hr            mean heart rate over the loaded stages
  mean_power_per_kg  mean power over the same stages / weight, W/kg

The means assume every stage lasts the same time; the files do not say.

Layout of the dataset (one workbook per test, named A<id>.xlsx):
  * Sheet1  athlete info as label/value pairs: Name:, Gender:, Test:, Test Date:,
            DOB:, Height, Weight, ...
  * Sheet2  the step test, one row per stage: Actual Power, HR, VO2, Bla, SR/Cadence
  * Sheet3  derived metrics as label/value pairs: VO2max, Hrmax, ...
  * Data_Summary.xlsx  one row per file with its sport, used when a workbook
            has no "Test:" value

A test counts as cycling when its "Test:" field is "Cycling". Athlete names are
never written to the output.
"""
from __future__ import annotations

import argparse
import io
import re
import sys
import warnings
import zipfile
from pathlib import Path, PurePosixPath

import pandas as pd
from openpyxl import load_workbook

# openpyxl complains about an Excel extension in every file; it is harmless
warnings.filterwarnings("ignore", message="Unknown extension", module="openpyxl")

SPORT = "cycling"
TEST_FILE_RE = re.compile(r"A\d+", re.I)
SUMMARY_FILE = "Data_Summary.xlsx"
COLUMNS = ["test_id", "vo2max", "gender", "age", "height", "weight",
           "hrmax", "hr_rest", "mean_hr", "mean_power_per_kg"]


def warn(msg: str) -> None:
    print(f"warning: {msg}", file=sys.stderr)


def die(msg: str) -> None:
    raise SystemExit(f"error: {msg}")


def snake(label) -> str:
    """'%VO2max @ Tlac' -> 'pct_vo2max_at_tlac', 'Bla @ 160 bpm' -> 'bla_at_160bpm'."""
    s = str(label).strip().lower()
    s = re.sub(r"\s+", " ", s).replace("%", "pct ").replace("@", " at ")
    s = re.sub(r"(\d)\s*bpm", r"\1bpm", s)
    return re.sub(r"[^0-9a-z]+", "_", s).strip("_")


def to_number(v):
    """Numbers stay numbers; numeric text is converted; blanks and text -> None."""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return v
    try:
        return float(str(v).strip().replace(",", "."))
    except ValueError:
        return None


def to_date(v):
    """Excel dates arrive as datetimes, serial numbers or 'dd/mm/yyyy' text."""
    if v is None or (isinstance(v, str) and not v.strip()):
        return pd.NaT
    if isinstance(v, (int, float)):
        return pd.Timestamp("1899-12-30") + pd.Timedelta(days=v)
    return pd.to_datetime(v, dayfirst=True, errors="coerce")


def clean_text(v):
    if v is None:
        return None
    s = str(v).strip()
    return s or None


# --------------------------------------------------------------------------- reading

class Source:
    """The Zenodo zip archive, or the folder it was unzipped to."""

    def __init__(self, path: Path):
        if path.is_dir():
            self._zip = None
            self.root = path
            names = [p.relative_to(path).as_posix() for p in path.rglob("*.xlsx")]
        elif zipfile.is_zipfile(path):
            self._zip = zipfile.ZipFile(path)
            names = [n for n in self._zip.namelist() if n.lower().endswith(".xlsx")]
        else:
            die(f"{path} is neither a zip file nor a folder")
        self.names = sorted(n for n in names
                            if "__MACOSX" not in n and not PurePosixPath(n).name.startswith(("._", "~$")))

    def read(self, name: str) -> bytes:
        return self._zip.read(name) if self._zip else (self.root / name).read_bytes()

    def test_files(self) -> dict[str, str]:
        """{'A1080': 'A1080.xlsx', ...}"""
        out = {}
        for n in self.names:
            stem = PurePosixPath(n).stem
            if TEST_FILE_RE.fullmatch(stem):
                out[stem.upper()] = n
        return out

    def summary_sports(self) -> dict[str, str]:
        """Sport per test ID from Data_Summary.xlsx, or {} if it is missing."""
        name = next((n for n in self.names if PurePosixPath(n).name == SUMMARY_FILE), None)
        if name is None:
            return {}
        df = pd.read_excel(io.BytesIO(self.read(name)))
        if not {"file", "sport"} <= set(df.columns):
            warn(f"{SUMMARY_FILE} has no 'file'/'sport' columns; ignoring it")
            return {}
        return {PurePosixPath(str(f)).stem.upper(): str(s).strip()
                for f, s in zip(df["file"], df["sport"]) if pd.notna(f) and pd.notna(s)}


def label_values(ws) -> dict[str, object]:
    """Read a two-column label/value sheet into {snake(label): value}."""
    out = {}
    for row in ws.iter_rows(values_only=True):
        if not row or row[0] is None or not str(row[0]).strip():
            continue
        out[snake(str(row[0]).rstrip().rstrip(":"))] = row[1] if len(row) > 1 else None
    return out


def stage_table(ws) -> pd.DataFrame:
    """Sheet2: header row, then one row per stage. Only the named columns are kept."""
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return pd.DataFrame()
    header = [snake(h) if h is not None and str(h).strip() else None for h in rows[0]]
    keep = [(i, h) for i, h in enumerate(header) if h]
    records = []
    for row in rows[1:]:
        values = {h: to_number(row[i]) if i < len(row) else None for i, h in keep}
        if any(v is not None for v in values.values()):
            records.append(values)
    return pd.DataFrame(records, columns=[h for _, h in keep])


# --------------------------------------------------------------------------- build

def read_test(src: Source, name: str):
    """(sheet1, stages, sheet3) of one workbook, or None if it is not laid out as expected."""
    wb = load_workbook(io.BytesIO(src.read(name)), read_only=True, data_only=True)
    try:
        if len(wb.worksheets) < 3:
            warn(f"{name}: expected 3 sheets, found {len(wb.worksheets)}; skipped")
            return None
        return label_values(wb.worksheets[0]), stage_table(wb.worksheets[1]), label_values(wb.worksheets[2])
    finally:
        wb.close()


def test_row(test_id: str, info: dict, stages: pd.DataFrame, metrics: dict) -> dict:
    """The model's columns for one test."""
    gender = clean_text(info.get("gender"))
    dob, test_date = to_date(info.get("dob")), to_date(info.get("test_date"))
    weight = to_number(info.get("weight"))
    row = {
        "test_id": test_id,
        "vo2max": to_number(metrics.get("vo2max")),
        "gender": gender.upper() if gender else None,
        "age": round((test_date - dob).days / 365.25, 1) if pd.notna(dob) and pd.notna(test_date) else None,
        "height": to_number(info.get("height")),
        "weight": weight,
        "hrmax": to_number(metrics.get("hrmax")),
        "hr_rest": None,
        "mean_hr": None,
        "mean_power_per_kg": None,
    }
    if stages.empty or not {"actual_power", "hr"} <= set(stages.columns):
        return row
    rest = stages[(stages["actual_power"] == 0) & stages["hr"].notna()]
    if len(rest):
        row["hr_rest"] = rest["hr"].iloc[0]
    # the same stages for both means, so power and HR describe the same effort
    loaded = stages[(stages["actual_power"] > 0) & stages["hr"].notna()]
    if len(loaded):
        row["mean_hr"] = round(loaded["hr"].mean(), 1)
        if weight:
            row["mean_power_per_kg"] = round(loaded["actual_power"].mean() / weight, 3)
    return row


def build(src: Source, output: str, per_stage: bool) -> None:
    files = src.test_files()
    if not files:
        die("no test files named like A123.xlsx found")
    summary = src.summary_sports()

    rows, stage_frames = [], []
    sports_seen: dict[str, int] = {}
    unknown, mismatched = [], []
    for test_id in sorted(files, key=lambda t: int(t[1:])):
        result = read_test(src, files[test_id])
        if result is None:
            continue
        info, stages, metrics = result
        test = clean_text(info.get("test"))
        sport = test or summary.get(test_id)
        if sport is None:
            unknown.append(test_id)
            continue
        if test and test_id in summary and summary[test_id].lower() != test.lower():
            mismatched.append(f"{test_id} ({test} vs {summary[test_id]})")
        sports_seen[sport] = sports_seen.get(sport, 0) + 1
        if sport.lower() != SPORT:
            continue

        row = test_row(test_id, info, stages, metrics)
        rows.append(row)
        if per_stage:
            st = stages.copy()
            st.insert(0, "stage", range(1, len(st) + 1))
            st.insert(0, "test_id", test_id)
            st.insert(1, "gender", row["gender"])
            st["vo2max"] = row["vo2max"]
            stage_frames.append(st)

    if not rows:
        die("no cycling tests found")
    out = pd.concat(stage_frames, ignore_index=True) if per_stage else pd.DataFrame(rows, columns=COLUMNS)
    out.to_csv(output, index=False)

    print(f"tests by sport:          {dict(sorted(sports_seen.items(), key=lambda kv: -kv[1]))}")
    print(f"cycling tests written:   {len(rows)}")
    if unknown:
        print(f"tests without a sport:   {len(unknown)} ({', '.join(unknown[:5])})")
    if mismatched:
        print(f"Test: field disagrees with {SUMMARY_FILE}: {', '.join(mismatched[:5])}")
    print(f"rows x columns:          {out.shape[0]} x {out.shape[1]} "
          f"({'one per stage' if per_stage else 'one per test'})")
    missing = out.isna().sum()
    missing = missing[missing > 0]
    if len(missing):
        print("missing values:          " + ", ".join(f"{c} {n}" for c, n in missing.items()))
    print(f"saved: {output}")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(
        description="Merge all cycling tests of the TCD graded incremental test dataset into one CSV.")
    ap.add_argument("source", help="the data folder, or data.zip from Zenodo")
    ap.add_argument("-o", "--output",
                    help="output CSV (default: cycling_tests.csv, or cycling_stages.csv with --stages)")
    ap.add_argument("--stages", action="store_true",
                    help="one row per test stage instead of one row per test (used by plot_cycling_stages.py)")
    args = ap.parse_args(argv)
    source = Path(args.source)
    if not source.exists():
        die(f"{source} not found")
    output = args.output or ("cycling_stages.csv" if args.stages else "cycling_tests.csv")
    build(Source(source), output, args.stages)


if __name__ == "__main__":
    main()
