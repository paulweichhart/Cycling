"""Train the VO2max linear regression and export it to src/utils/model.bin.

Run from src/:  python -m utils.train_model

The export is a joblib dump of (dv, model), which service/app.py loads. `model` is a
Pipeline(StandardScaler, LinearRegression), so the service scales inputs itself and the
coefficients are per standard deviation (comparable across features).
"""
from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
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

def split_data(data: pd.DataFrame, seed: int = 42):
    df_full_train, df_test = train_test_split(data, test_size=0.2, random_state=seed)
    df_train, df_val = train_test_split(df_full_train, test_size=0.25, random_state=seed)
    return (df_full_train.reset_index(drop=True), df_train.reset_index(drop=True),
            df_val.reset_index(drop=True), df_test.reset_index(drop=True))


def encode(df: pd.DataFrame, dv: DictVectorizer, fit: bool):
    records = df[FEATURES].to_dict(orient="records")
    return dv.fit_transform(records) if fit else dv.transform(records)


def evaluate(y, y_pred) -> tuple[float, float]:
    return mean_squared_error(y, y_pred), r2_score(y, y_pred)


def store_model(dv: DictVectorizer, model: Pipeline, model_path: Path) -> None:
    joblib.dump((dv, model), model_path)


def train(data_path: Path = DATA_PATH, model_path: Path = MODEL_PATH) -> dict:
    data = pd.read_csv(data_path, sep=None, engine="python")
    data = data.dropna(subset=FEATURES + [TARGET])
    explore_data(data, TARGET)

    _, df_train, df_val, _ = split_data(data)

    dv = DictVectorizer(sparse=False)
    X_train = encode(df_train, dv, fit=True)
    X_val = encode(df_val, dv, fit=False)

    model = make_pipeline(StandardScaler(), LinearRegression())
    model.fit(X_train, df_train[TARGET].values)

    mse, r2 = evaluate(df_val[TARGET].values, model.predict(X_val))
    store_model(dv, model, model_path)
    coef = dict(zip(dv.get_feature_names_out(), model[-1].coef_.round(3)))

    return { "mse": mse, "r2": r2, "coef": coef }

if __name__ == "__main__":
    print(train())
