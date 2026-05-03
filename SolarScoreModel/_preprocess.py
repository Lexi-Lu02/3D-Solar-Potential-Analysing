"""共享的预处理 + 特征清单。

train.py / evaluate.py / infer.py 都从本模块 import，
确保 joblib pickle 在反序列化时能找到自定义函数。
"""

from __future__ import annotations

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.feature_selection import VarianceThreshold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler


NUMERIC_FEATURES: list[str] = [
    "roof_area_m2",
    "roof_perimeter_m",
    "roof_compactness",
    "building_height_m",
    "roof_top_elevation_m",
    "roof_aspect_deg",
    "roof_elongation",
    "lat",
    "lng",
    "annual_solar_kwh_m2",
    "winter_solar_kwh_m2_day",
    "summer_solar_kwh_m2_day",
    "solar_seasonality",
]
CATEGORICAL_FEATURES: list[str] = ["suburb"]
TARGET: str = "solar_score_avg"

RANDOM_STATE: int = 42
TEST_SIZE: float = 0.2
CV_FOLDS: int = 5


def safe_log1p(x: np.ndarray) -> np.ndarray:
    """log1p with negative inputs clipped to 0; avoids RuntimeWarning."""
    return np.log1p(np.clip(x, a_min=0, a_max=None))


def make_preprocessor() -> ColumnTransformer:
    numeric_pipe = Pipeline(
        steps=[
            (
                "log1p",
                FunctionTransformer(
                    safe_log1p, validate=False, feature_names_out="one-to-one"
                ),
            ),
            ("var", VarianceThreshold(threshold=0.0)),
            ("scale", StandardScaler()),
        ]
    )
    cat_pipe = Pipeline(
        steps=[
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, NUMERIC_FEATURES),
            ("cat", cat_pipe, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
