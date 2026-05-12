"""Shared feature lists + preprocessor. Imported by train/evaluate/infer.

Keep functions importable so joblib pickle resolves them at load time.
"""

from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.feature_selection import VarianceThreshold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# roof geometry — no lat/lng (no physical meaning at CBD scale; pure spatial overfit proxy)
GEOMETRY_FEATURES: list[str] = [
    "roof_area_m2",
    "roof_perimeter_m",
    "roof_compactness",
    "building_height_m",
    "roof_top_elevation_m",
    "roof_aspect_deg",
    "roof_elongation",
]
# neighbour shading proxy at 50m / 100m
NEIGHBOUR_FEATURES: list[str] = [
    "nbr_count_50m",
    "nbr_max_height_50m",
    "nbr_mean_height_50m",
    "nbr_taller_count_50m",
    "nbr_shading_index_50m",
    "nbr_count_100m",
    "nbr_max_height_100m",
    "nbr_mean_height_100m",
    "nbr_taller_count_100m",
    "nbr_shading_index_100m",
]
NUMERIC_FEATURES: list[str] = GEOMETRY_FEATURES + NEIGHBOUR_FEATURES
# 2015 footprint.suburb at train; precincts.name lookup at infer (same 14 strings)
CATEGORICAL_FEATURES: list[str] = ["suburb"]
TARGET: str = "solar_score_avg"

RANDOM_STATE: int = 42
TEST_SIZE: float = 0.2
CV_FOLDS: int = 5


def make_preprocessor() -> ColumnTransformer:
    """LightGBM-friendly minimal preprocessor.

    numeric: VarianceThreshold(0) only — drops constant columns (irradiance).
        no log1p: tree splits scale-invariant; old log1p+clip silently dropped lat.
        no StandardScaler: no effect on tree splits.
    categorical: OneHotEncoder(handle_unknown='ignore').
    """
    numeric_pipe = Pipeline(
        steps=[
            ("var", VarianceThreshold(threshold=0.0)),
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
