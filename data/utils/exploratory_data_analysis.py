#!/usr/bin/env python3
"""Scatter plots of the cycling tests, coloured by gender.

Usage
-----
  python3 exploratory_data_analysis.py                         # VO2max of every test against W/kg
  python3 exploratory_data_analysis.py --x age                 # VO2max against any per-test column
  python3 exploratory_data_analysis.py --stages                # every stage: VO2 against power
  python3 exploratory_data_analysis.py --stages --y hr         # every stage: heart rate against power
  python3 exploratory_data_analysis.py -o plot.png             # save instead of showing

The default view shows one point per test (data/cycling_tests.csv), so each
VO2max appears once. --stages shows one point per stage (data/cycling_stages.csv).
Build the CSVs first with:
  python data/build_cycling_csv.py data -o data/cycling_tests.csv
  python data/build_cycling_csv.py data --stages -o data/cycling_stages.csv
Requirements: pip install pandas matplotlib
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

DATA = Path(__file__).parent / "data"
TESTS_CSV = DATA / "cycling_tests.csv"
STAGES_CSV = DATA / "cycling_stages.csv"

TEST_LABELS = {
    "vo2max": "VO2max (mL/kg/min)",
    "mean_power_per_kg": "Mean power (W/kg)",
    "mean_hr": "Mean heart rate (bpm)",
    "hrmax": "Max heart rate (bpm)",
    "hr_rest": "Resting heart rate (bpm)",
    "age": "Age (years)",
    "height": "Height (m)",
    "weight": "Weight (kg)",
}
STAGE_LABELS = {
    "actual_power": "Power (W)",
    "hr": "Heart rate (bpm)",
    "vo2": "VO2 (mL/kg/min)",
    "bla": "Blood lactate (mmol/L)",
    "sr_cadence": "Cadence (rpm)",
    "vo2max": "VO2max (mL/kg/min)",
}

# colour plus marker shape, so the groups stay apart without colour vision
GROUPS = {
    "M": {"label": "Male", "color": "#2a78d6", "marker": "o"},
    "F": {"label": "Female", "color": "#eb6e1f", "marker": "^"},
}

def explore_data(data, column):
  print(len(data))
  print(data.head())
  
  # plt.figure(figsize=(6, 4))
  
  # sns.histplot(data[column], bins=40, color='black', alpha=1)
  # plt.xlabel(column)
  # plt.title(column)
  
  # plt.show()
  
  print(f"min: {data[column].min()} max: {data[column].max()}")

def scatter(df: pd.DataFrame, x: str, y: str, labels: dict, per_stage: bool, title: str):
    fig, ax = plt.subplots(figsize=(9, 6))
    for gender, style in GROUPS.items():
        part = df[df["gender"] == gender]
        if per_stage:
            count = f"{part['test_id'].nunique()} tests, {len(part)} stages"
        else:
            count = f"{len(part)} tests, mean {y} {part[y].mean():.1f}"
        ax.scatter(
            part[x], part[y],
            s=22 if per_stage else 36, alpha=0.6 if per_stage else 0.75,
            color=style["color"], marker=style["marker"],
            edgecolors="white", linewidths=0.5,
            label=f"{style['label']} ({count})",
        )

    ax.set_xlabel(labels[x])
    ax.set_ylabel(labels[y])
    ax.set_title(title, loc="left")
    ax.grid(True, color="#e4e3df", linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(frameon=False)
    fig.tight_layout()
    return fig

def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Plot the cycling tests by gender.")
    ap.add_argument("--stages", action="store_true",
                    help="plot every stage instead of one VO2max point per test")
    ap.add_argument("--csv", type=Path, help=f"input CSV (default: {TESTS_CSV.name}, or {STAGES_CSV.name} with --stages)")
    ap.add_argument("--x", help="x axis column (default: mean_power_per_kg, or actual_power with --stages)")
    ap.add_argument("--y", help="y axis column (default: vo2max, or vo2 with --stages)")
    ap.add_argument("--include-rest", action="store_true", help="--stages: keep the 0 W resting stage")
    ap.add_argument("-o", "--output", help="save the plot to this file instead of showing it")
    args = ap.parse_args(argv)

    if args.stages:
        labels, csv = STAGE_LABELS, args.csv or STAGES_CSV
        x, y = args.x or "actual_power", args.y or "vo2"
    else:
        labels, csv = TEST_LABELS, args.csv or TESTS_CSV
        x, y = args.x or "mean_power_per_kg", args.y or "vo2max"
    for col in (x, y):
        if col not in labels:
            ap.error(f"unknown column {col!r}; choose from {', '.join(labels)}")

    df = pd.read_csv(csv, sep=None, engine="python").dropna(subset=[x, y, "gender"])  # , or ;
    if args.stages and not args.include_rest:
        df = df[df["actual_power"] > 0]

    kind = "stages" if args.stages else "one point per test"
    fig = scatter(df, x, y, labels, args.stages, f"Cycling tests ({kind}): {labels[y]} vs {labels[x]}")
    if args.output:
        fig.savefig(args.output, dpi=150)
        print(f"saved: {args.output}")
    else:
        plt.show()

if __name__ == "__main__":
    main()
