import pandas as pd
import numpy as np
import joblib
import streamlit as st
from itertools import product

st.title("Waveform Settings Finder")
st.caption("Find the best V, F_r, dt2 settings for a given color and coverage level.")

@st.cache_data
def load_data():
    df = pd.read_parquet("data/processed/waveform_tuning_row_summary.parquet")
    condition_cols = ["Color$", "HeadIdx#", "V", "F_r", "dt2", "Coverage#"]
    agg = df.groupby(condition_cols)[["sd_std", "sd_mean"]].mean().reset_index()
    return agg.rename(columns={"sd_std": "sd_std_mean", "sd_mean": "sd_mean_mean"})

@st.cache_resource
def load_model():
    model    = joblib.load("models/rf_sd_std.pkl")
    features = joblib.load("models/rf_sd_std_features.pkl")
    return model, features

def build_features(grid, features):
    base = grid[["V", "F_r", "dt2", "Coverage#"]].copy()
    base["V_x_Fr"]         = grid["V"] * grid["F_r"]
    base["dt2_x_coverage"] = grid["dt2"] * grid["Coverage#"]
    base["V_sq"]           = grid["V"] ** 2
    base["Fr_sq"]          = grid["F_r"] ** 2
    dummies = pd.get_dummies(grid["Color$"], prefix="color")
    X = pd.concat([base, dummies], axis=1).reindex(columns=features, fill_value=0)
    return X

agg = load_data()
model, features = load_model()

# --- shared inputs ---
col1, col2 = st.columns(2)
with col1:
    color = st.selectbox("Color", ["C", "M", "Y", "K"])
with col2:
    coverage_options = sorted(agg["Coverage#"].unique().astype(int).tolist())
    coverage = st.selectbox("Coverage", coverage_options, index=coverage_options.index(10))

use_target = st.checkbox("Filter by target SD (ink density)")
target, tolerance = None, None
if use_target:
    col3, col4 = st.columns(2)
    with col3:
        target = st.slider("Target SD", 0.05, 0.85, 0.35, step=0.01)
    with col4:
        tolerance = st.slider("Tolerance ±", 0.01, 0.10, 0.02, step=0.01)

st.divider()
tab1, tab2 = st.tabs(["Measured — real data", "Predicted — untested settings"])

# --- tab 1: real data ---
with tab1:
    st.caption("Results from actual print experiments. Only tested settings are shown.")
    filtered = agg[(agg["Color$"] == color) & (agg["Coverage#"] == coverage)]
    if use_target:
        filtered = filtered[
            (filtered["sd_mean_mean"] >= target - tolerance) &
            (filtered["sd_mean_mean"] <= target + tolerance)
        ]
    if filtered.empty:
        st.warning("No conditions found for this selection.")
    else:
        best = (filtered.sort_values("sd_std_mean")
                .drop_duplicates(subset=["V", "F_r", "dt2"])
                .head(10).reset_index(drop=True))
        best.index += 1
        st.success(f"{len(filtered)} conditions found — top 10 by lowest std")
        st.dataframe(
            best[["V", "F_r", "dt2", "sd_mean_mean", "sd_std_mean"]]
            .rename(columns={"sd_mean_mean": "sd_mean", "sd_std_mean": "sd_std"}),
            use_container_width=True
        )

# --- tab 2: model predictions ---
with tab2:
    st.caption("Model predicts sd_std for all V × F_r × dt2 combinations — including untested ones.")
    st.warning(
        "These are model predictions, not real measurements. "
        "Combinations marked **tested: no** were never physically printed — "
        "the model interpolates based on patterns from similar tested settings. "
        "Treat these as suggestions worth verifying, not confirmed results."
    )

    V_vals   = sorted(agg["V"].unique().tolist())
    Fr_vals  = sorted(agg["F_r"].unique().tolist())
    dt2_vals = sorted(agg["dt2"].unique().tolist())

    grid = pd.DataFrame(
        list(product(V_vals, Fr_vals, dt2_vals)),
        columns=["V", "F_r", "dt2"]
    )
    grid["Coverage#"] = float(coverage)
    grid["Color$"]    = color

    X = build_features(grid, features)
    grid["predicted_sd_std"] = model.predict(X)

    if use_target:
        grid["predicted_sd_mean"] = model.predict(
            build_features(grid.assign(**{"Color$": color}), features)
        )

    result = grid.sort_values("predicted_sd_std").head(10).reset_index(drop=True)
    result.index += 1

    tested = set(zip(agg["V"], agg["F_r"], agg["dt2"]))
    result["tested"] = result.apply(lambda r: "yes" if (r["V"], r["F_r"], r["dt2"]) in tested else "no", axis=1)

    st.success(f"{len(grid)} combinations evaluated — top 10 by lowest predicted std")
    st.dataframe(
        result[["V", "F_r", "dt2", "predicted_sd_std", "tested"]]
        .rename(columns={"predicted_sd_std": "predicted sd_std"}),
        use_container_width=True
    )
