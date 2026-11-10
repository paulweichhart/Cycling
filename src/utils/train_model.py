"""Train the VO2max linear regression and export it to src/utils/model.bin.

Run from src/:  python -m utils.train_model

The export is a joblib dump of (dv, model), which service/app.py loads. `model` is a
Pipeline(StandardScaler, LinearRegression), so the service scales inputs itself and the
coefficients are per standard deviation (comparable across features).
"""
from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import KFold
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "cycling_tests.csv"
MODEL_PATH = Path(__file__).resolve().parent / "model.bin"
TARGET = "vo2max"

# columns the model is trained on; every other column (test_id, hrmax, hr_rest, ...) is ignored
FEATURES = ["gender", "age", "weight", "mean_hr", "mean_power_per_kg"]

def explore_data(data: pd.DataFrame, column: str) -> None:
    print(len(data))
    print(data.head())
    print(f"min: {data[column].min()} max: {data[column].max()}")

def encode(df: pd.DataFrame, dv: DictVectorizer, fit: bool):
    records = df[FEATURES].to_dict(orient="records")
    return dv.fit_transform(records) if fit else dv.transform(records)


def evaluate(y, y_pred) -> tuple[float, float]:
    return mean_squared_error(y, y_pred), r2_score(y, y_pred)


def store_model(dv: DictVectorizer, model: Pipeline, model_path: Path) -> None:
    joblib.dump((dv, model), model_path)


def make_model() -> Pipeline:
    return make_pipeline(StandardScaler(), LinearRegression())


def train(data_path: Path = DATA_PATH, model_path: Path = MODEL_PATH,
          n_splits: int = 5, seed: int = 42) -> dict:
    """5-fold cross-validation for the scores, then a final fit on all the data for the export."""
    data = pd.read_csv(data_path, sep=None, engine="python")
    data = data.dropna(subset=FEATURES + [TARGET]).reset_index(drop=True)
    explore_data(data, TARGET)

    mses, r2s = [], []
    for df_train_idx, df_val_idx in KFold(n_splits=n_splits, shuffle=True, random_state=seed).split(data):
        df_train, df_val = data.iloc[df_train_idx], data.iloc[df_val_idx]
        dv = DictVectorizer(sparse=False)
        X_train = encode(df_train, dv, fit=True)
        X_val = encode(df_val, dv, fit=False)

        model = make_model()
        model.fit(X_train, df_train[TARGET].values)
        mse, r2 = evaluate(df_val[TARGET].values, model.predict(X_val))
        mses.append(mse)
        r2s.append(r2)

    dv = DictVectorizer(sparse=False)
    X = encode(data, dv, fit=True)
    model = make_model()
    model.fit(X, data[TARGET].values)
    store_model(dv, model, model_path)
    coef = dict(zip(dv.get_feature_names_out(), model[-1].coef_.round(3)))

    return {
        "mse": float(np.mean(mses)), 
        "mse_std": float(np.std(mses)),
        "r2": float(np.mean(r2s)),
        "r2_std": float(np.std(r2s)),
        "coef": coef,
    }

if __name__ == "__main__":
    print(train())
