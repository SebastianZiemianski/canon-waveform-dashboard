import os
import joblib
import pandas as pd
import numpy as np
import streamlit as st
from itertools import product
from sklearn.ensemble import RandomForestRegressor

st.set_page_config(
    page_title="Canon Waveform Tuning",
    layout="wide"
)

COLORS     = ['C', 'M', 'Y', 'K']
COLOR_NAME = {'C': 'Cyan', 'M': 'Magenta', 'Y': 'Yellow', 'K': 'Black'}
DT2_VALS   = [-1100, -900, -700, -500, -300]

MODEL_INFO = {
    'sd_std':          ('Within-chip uniformity',  'Nozzle variability within one chip — lower = more consistent', 'Model 1', 0.782),
    'sd_mean':         ('Within-chip SD level',    'Average ink density on one chip — match to target',           'Model 3', 0.995),
    'cross_chip_std':  ('Cross-chip consistency',  'How much chips differ from each other — lower = more uniform','Model 2', 0.998),
    'cross_chip_mean': ('Cross-chip SD level',     'Average ink density across all 30 chips',                     'Model 4', 0.998),
}

FEATURE_COLS = [
    'V', 'F_r', 'dt2', 'Coverage#',
    'V_x_Fr', 'dt2_x_coverage', 'V_sq', 'Fr_sq',
    'color_C', 'color_M', 'color_Y', 'color_K',
]

# ── Features ──────────────────────────────────────────────────────────────────
def build_features(df):
    out = pd.DataFrame(index=df.index)
    out['V']               = df['V'].astype(float)
    out['F_r']             = df['F_r'].astype(float)
    out['dt2']             = df['dt2'].astype(float)
    out['Coverage#']       = df['Coverage#'].astype(float)
    out['V_x_Fr']          = out['V'] * out['F_r']
    out['dt2_x_coverage']  = out['dt2'] * out['Coverage#']
    out['V_sq']            = out['V'] ** 2
    out['Fr_sq']           = out['F_r'] ** 2
    for c in COLORS:
        out[f'color_{c}']  = (df['Color$'] == c).astype(float)
    return out[FEATURE_COLS]


# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_parquet('data/processed/waveform_tuning_row_summary.parquet')
    cond_chip = ['Color$', 'HeadIdx#', 'V', 'F_r', 'dt2', 'Coverage#']
    agg = (df.groupby(cond_chip)[['sd_std', 'sd_mean']]
             .mean().reset_index()
             .rename(columns={'sd_std': 'sd_std_mean', 'sd_mean': 'sd_mean_mean'}))

    cond_only = ['Color$', 'V', 'F_r', 'dt2', 'Coverage#']
    cross = (agg.groupby(cond_only)
                .agg(cross_chip_std=('sd_mean_mean', 'std'),
                     cross_chip_mean=('sd_mean_mean', 'mean'),
                     sd_std_mean=('sd_std_mean', 'mean'),
                     sd_mean_mean=('sd_mean_mean', 'mean'))
                .reset_index())

    V_range  = (float(agg['V'].min()),   float(agg['V'].max()))
    Fr_range = (float(agg['F_r'].min()), float(agg['F_r'].max()))
    return agg, cross, V_range, Fr_range


# ── Models ────────────────────────────────────────────────────────────────────
@st.cache_resource
def load_or_train(_agg, _cross):
    os.makedirs('models', exist_ok=True)
    specs = {
        'rf_sd_std':     ('sd_std_mean',    _agg),
        'rf_sd_mean':    ('sd_mean_mean',   _agg),
        'rf_cross_std':  ('cross_chip_std', _cross),
        'rf_cross_mean': ('cross_chip_mean',_cross),
    }
    out = {}
    for name, (target, data) in specs.items():
        path = f'models/{name}.pkl'
        if os.path.exists(path):
            out[name] = joblib.load(path)
        else:
            with st.spinner(f'Training {name} (first run only)...'):
                rf = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
                rf.fit(build_features(data), data[target].fillna(0))
                joblib.dump(rf, path)
                out[name] = rf
    return out


def predict_row(V, Fr, dt2, cov, color, mdls):
    row = pd.DataFrame([{
        'V': float(V), 'F_r': float(Fr), 'dt2': float(dt2),
        'Coverage#': float(cov), 'Color$': color,
    }])
    X = build_features(row)
    return {
        'sd_std':          max(0.0, mdls['rf_sd_std'].predict(X)[0]),
        'sd_mean':         max(0.0, mdls['rf_sd_mean'].predict(X)[0]),
        'cross_chip_std':  max(0.0, mdls['rf_cross_std'].predict(X)[0]),
        'cross_chip_mean': max(0.0, mdls['rf_cross_mean'].predict(X)[0]),
    }


# ── Bootstrap ─────────────────────────────────────────────────────────────────
agg, cross, V_range, Fr_range = load_data()
mdls = load_or_train(agg, cross)

V_min, V_max   = V_range
Fr_min, Fr_max = Fr_range

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Waveform Settings")

    color    = st.selectbox("Ink color", COLORS, format_func=lambda x: COLOR_NAME[x])
    coverage = st.slider("Coverage", 2, 31, 15)
    st.divider()

    V   = st.slider("Voltage (V)",       float(V_min), float(V_max), float((V_min + V_max) / 2), step=0.5)
    Fr  = st.slider("Flank ratio (F_r)", float(Fr_min), float(Fr_max), float((Fr_min + Fr_max) / 2), step=0.01)
    dt2 = st.select_slider("dt2", options=DT2_VALS, value=-700)

    out_of_range = False  # sliders are now clamped to training range

    st.divider()
    with st.expander("Model reference"):
        for key, (title, desc, ref, r2) in MODEL_INFO.items():
            st.markdown(f"**{title}** ({ref})  \n{desc}  \nR²={r2}")
            st.divider()


# ── Main ──────────────────────────────────────────────────────────────────────
st.title("Canon Waveform Tuning Assistant")
st.caption("Predict print quality metrics and find optimal waveform settings using Random Forest models trained on Canon printhead measurement data.")

tab1, tab2, tab3, tab4 = st.tabs(["Predict a setting", "Find best settings", "Measured data", "Printhead map"])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — PREDICT
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    preds = predict_row(V, Fr, dt2, coverage, color, mdls)

    st.subheader(
        f"{COLOR_NAME[color]}  |  Coverage {coverage}  |  "
        f"V={V}  |  F_r={Fr:.2f}  |  dt2={dt2}"
    )

    key_map = {
        'sd_std':          'sd_std_mean',
        'sd_mean':         'sd_mean_mean',
        'cross_chip_std':  'cross_chip_std',
        'cross_chip_mean': 'cross_chip_mean',
    }
    avg = cross[cross['Color$'] == color][list(key_map.values())].mean()

    # lower is better for uniformity/consistency metrics → invert delta color
    lower_is_better = {'sd_std', 'cross_chip_std'}

    c1, c2, c3, c4 = st.columns(4)
    for col_ui, (key, (title, desc, ref, r2)) in zip([c1, c2, c3, c4], MODEL_INFO.items()):
        avg_val  = float(avg[key_map[key]])
        pred_val = preds[key]
        delta    = pred_val - avg_val
        with col_ui:
            st.metric(
                label=title,
                value=f"{pred_val:.5f}",
                delta=f"{delta:+.5f} vs avg",
                delta_color="inverse" if key in lower_is_better else "normal",
                help=f"{desc}\n\n{ref}  |  R²={r2}",
            )

    st.divider()

    rows = []
    for key, (title, _, ref, _) in MODEL_INFO.items():
        avg_val  = float(avg[key_map[key]])
        pred_val = preds[key]
        delta_pct = (pred_val - avg_val) / avg_val * 100 if avg_val else 0.0
        rows.append({
            'Metric':                    title,
            'This setting':              f"{pred_val:.5f}",
            f'{COLOR_NAME[color]} avg':  f"{avg_val:.5f}",
            'vs avg':                    f"{delta_pct:+.1f}%",
            'Model':                     ref,
        })

    st.subheader(f"vs {COLOR_NAME[color]} dataset average")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — FIND BEST
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Find settings that hit a target ink density with the most uniform nozzles")

    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        color_s = st.selectbox("Color", COLORS, key='s_col', format_func=lambda x: COLOR_NAME[x])
    with col_b:
        target_sd = st.slider("Target sd_mean", 0.05, 0.85, 0.35, step=0.01)
    with col_c:
        tol = st.slider("Tolerance ±", 0.005, 0.10, 0.02, step=0.005)
    with col_d:
        cov_s = st.slider("Coverage", 2, 31, 15, key='s_cov')

    use_predicted = st.toggle(
        "Include predicted combinations (untested V x F_r x dt2)",
        help="Uses Model 3 to predict sd_mean and Model 1 for sd_std across all tested V and F_r values.",
    )

    if use_predicted:
        V_vals  = sorted(agg['V'].unique())
        Fr_vals = sorted(agg['F_r'].unique())
        grid = pd.DataFrame(list(product(V_vals, Fr_vals, DT2_VALS)), columns=['V', 'F_r', 'dt2'])
        grid['Coverage#'] = float(cov_s)
        grid['Color$']    = color_s
        X_grid = build_features(grid)
        grid['sd_mean']         = mdls['rf_sd_mean'].predict(X_grid)
        grid['sd_std']          = mdls['rf_sd_std'].predict(X_grid)
        grid['cross_chip_std']  = mdls['rf_cross_std'].predict(X_grid)
        grid['cross_chip_mean'] = mdls['rf_cross_mean'].predict(X_grid)
        grid['source'] = 'predicted'
        search_df = grid
    else:
        search_df = (cross[(cross['Color$'] == color_s) & (cross['Coverage#'] == cov_s)]
                     .rename(columns={'sd_std_mean': 'sd_std', 'sd_mean_mean': 'sd_mean'})
                     .copy())
        search_df['source'] = 'measured'

    filtered = search_df[
        (search_df['sd_mean'] >= target_sd - tol) &
        (search_df['sd_mean'] <= target_sd + tol)
    ]

    if filtered.empty:
        st.warning(f"No settings found with sd_mean = {target_sd:.2f} ± {tol:.3f}")
        rng = search_df['sd_mean']
        st.info(f"Available sd_mean range for {COLOR_NAME[color_s]}: {rng.min():.3f} – {rng.max():.3f}")
    else:
        best = (filtered
                .sort_values('sd_std')
                .drop_duplicates(subset=['V', 'F_r', 'dt2'])
                .head(10)
                .reset_index(drop=True))
        best.index += 1
        st.success(f"{len(filtered)} matching combinations — top 10 by lowest sd_std (most uniform nozzles)")
        display = [c for c in ['V', 'F_r', 'dt2', 'sd_mean', 'sd_std', 'cross_chip_std', 'source'] if c in best.columns]
        st.dataframe(best[display], use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — MEASURED
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Actual measurements from Canon print experiments")
    st.caption("Direct lookup — no model involved. Only settings that were physically tested appear here.")

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        color_m = st.selectbox("Color", COLORS, key='m_col', format_func=lambda x: COLOR_NAME[x])
    with col_m2:
        cov_opts = sorted(agg['Coverage#'].unique().astype(int).tolist())
        cov_m    = st.selectbox("Coverage", cov_opts, index=cov_opts.index(10), key='m_cov')
    with col_m3:
        sort_by = st.selectbox("Sort by", ['sd_std_mean (uniformity)', 'sd_mean_mean (density)'])

    sort_col = 'sd_std_mean' if 'std' in sort_by else 'sd_mean_mean'

    meas = (cross[(cross['Color$'] == color_m) & (cross['Coverage#'] == cov_m)]
            .sort_values(sort_col)
            .reset_index(drop=True))
    meas.index += 1

    if meas.empty:
        st.warning("No data for this selection.")
    else:
        st.success(f"{len(meas)} tested settings for {COLOR_NAME[color_m]}, Coverage={cov_m}")
        st.dataframe(
            meas[['V', 'F_r', 'dt2', 'sd_mean_mean', 'sd_std_mean', 'cross_chip_mean', 'cross_chip_std']]
            .rename(columns={'sd_mean_mean': 'sd_mean', 'sd_std_mean': 'sd_std'}),
            use_container_width=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — PRINTHEAD MAP
# ═══════════════════════════════════════════════════════════════════════════════
NOZZLE_COLOR_MAP = {'Y': 1, 'M': 2, 'C': 3, 'K': 4}  # Color$ stored as 1-4 in extended parquet (Y=lowest SD, K=highest)
N_NOZZLES = 1120
N_CHIPS   = 30

@st.cache_resource
def load_nozzle_models():
    rf_path       = 'models/rf_nozzle_sd.pkl'
    rf_small_path = 'models/rf_nozzle_sd_small.pkl'
    mlp_path      = 'models/mlp_nozzle_sd.pkl'
    if os.path.exists(rf_path):
        rf_m = joblib.load(rf_path)
    elif os.path.exists(rf_small_path):
        rf_m = joblib.load(rf_small_path)
    else:
        rf_m = None
    mlp_m = joblib.load(mlp_path) if os.path.exists(mlp_path) else None
    return rf_m, mlp_m

def nozzle_features_rf(V, Fr, dt2, cov, color_enc, chip):
    noz = np.arange(N_NOZZLES, dtype=np.float32)
    n   = N_NOZZLES
    return np.column_stack([
        np.full(n, V),   np.full(n, Fr), np.full(n, dt2), np.full(n, cov),
        np.full(n, color_enc),
        np.full(n, V * Fr), np.full(n, dt2 * cov),
        np.full(n, V**2), np.full(n, Fr**2),
        np.full(n, chip), noz,
    ]).astype(np.float32)

def nozzle_features_mlp(V, Fr, dt2, cov, color_enc, chip):
    noz = np.arange(N_NOZZLES, dtype=np.float32)
    n   = N_NOZZLES
    return np.column_stack([
        np.full(n, V),   np.full(n, Fr), np.full(n, dt2), np.full(n, cov),
        np.full(n, color_enc),
        np.full(n, V * Fr), np.full(n, dt2 * cov),
        np.full(n, chip), noz,
    ]).astype(np.float32)

with tab4:
    st.subheader("Predicted SD for every nozzle — per chip")
    st.caption(
        "Model 6 (RF, R²=0.9534) works within the tested range. "
        "Model 7 (MLP, R²=0.9705) can extrapolate beyond tested voltage/F_r values."
    )

    rf_nozzle, mlp_nozzle = load_nozzle_models()
    models_available = [m for m, obj in [("Model 6 — RF", rf_nozzle), ("Model 7 — MLP", mlp_nozzle)] if obj is not None]

    if not models_available:
        st.warning(
            "Nozzle models not found. Run the save cell in each notebook first:\n\n"
            "- `notebooks/04-modeling/model-6-nozzle-sd.ipynb` (run the new save cell after the training cell)\n"
            "- `notebooks/04-modeling/model-7-nozzle-mlp.ipynb` (same)\n\n"
            "This creates `models/rf_nozzle_sd.pkl` and `models/mlp_nozzle_sd.pkl`."
        )
    else:
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            nozzle_model_choice = st.selectbox("Model", models_available)
        with col_p2:
            view_mode = st.selectbox("View", ["Single chip — nozzle profile", "All 30 chips — heatmap"])
        with col_p3:
            chip_sel = st.slider("Chip", 1, N_CHIPS, 5)

        use_mlp   = "MLP" in nozzle_model_choice
        model_obj = mlp_nozzle if use_mlp else rf_nozzle
        color_enc = NOZZLE_COLOR_MAP[color]

        # Extrapolation only available for MLP
        V_noz  = V
        Fr_noz = Fr
        if use_mlp:
            extrapolate = st.toggle(
                "Extrapolation mode — extend beyond tested voltage / F_r range",
                help="Only available for the Neural Network (Model 7). RF clips to the training boundary.",
            )
            if extrapolate:
                col_ev, col_efr = st.columns(2)
                with col_ev:
                    V_noz  = st.slider("Voltage (V) — extended", float(V_min - 4), float(V_max + 6), float(V), step=0.5, key='v_extrap')
                with col_efr:
                    Fr_noz = st.slider("Flank ratio (F_r) — extended", float(Fr_min), float(Fr_max + 0.2), float(Fr), step=0.01, key='fr_extrap')
                if V_noz > V_max or V_noz < V_min or Fr_noz > Fr_max:
                    st.warning(f"Outside training range (V: {V_min:.0f}–{V_max:.0f}, F_r: {Fr_min:.2f}–{Fr_max:.2f}) — MLP extrapolates, treat as estimate.")

        if use_mlp:
            X_noz = nozzle_features_mlp(V_noz, Fr_noz, dt2, coverage, color_enc, chip_sel)
            preds_noz = np.clip(model_obj.predict(X_noz), 0, None)
        else:
            X_noz = nozzle_features_rf(V_noz, Fr_noz, dt2, coverage, color_enc, chip_sel)
            preds_noz = model_obj.predict(X_noz)

        if "heatmap" in view_mode:
            # predict all chips
            all_chips = np.zeros((N_CHIPS, N_NOZZLES), dtype=np.float32)
            for c_idx in range(1, N_CHIPS + 1):
                if use_mlp:
                    Xc = nozzle_features_mlp(V_noz, Fr_noz, dt2, coverage, color_enc, c_idx)
                    all_chips[c_idx - 1] = np.clip(model_obj.predict(Xc), 0, None)
                else:
                    Xc = nozzle_features_rf(V_noz, Fr_noz, dt2, coverage, color_enc, c_idx)
                    all_chips[c_idx - 1] = model_obj.predict(Xc)

            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(14, 5))
            vmin = np.percentile(all_chips, 2)
            vmax = np.percentile(all_chips, 98)
            im = ax.imshow(all_chips, aspect='auto', cmap='RdYlGn_r', vmin=vmin, vmax=vmax)
            ax.set_xlabel('Nozzle position (0–1119)')
            ax.set_ylabel('Chip (1–30)')
            ax.set_yticks(range(N_CHIPS))
            ax.set_yticklabels(range(1, N_CHIPS + 1), fontsize=7)
            ax.set_title(
                f'Predicted SD — all 30 chips  |  {COLOR_NAME[color]}, Coverage={coverage}, '
                f'V={V}, F_r={Fr:.2f}, dt2={dt2}  |  {nozzle_model_choice}'
            )
            plt.colorbar(im, ax=ax, label='Predicted SD')
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

            chip_means = all_chips.mean(axis=1)
            worst = int(chip_means.argmax()) + 1
            best  = int(chip_means.argmin()) + 1
            c1m, c2m = st.columns(2)
            c1m.metric("Highest mean SD (worst chip)", f"Chip {worst}", f"{chip_means[worst-1]:.5f}")
            c2m.metric("Lowest mean SD (best chip)",   f"Chip {best}",  f"{chip_means[best-1]:.5f}")

        else:
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(14, 4))
            ax.plot(np.arange(N_NOZZLES), preds_noz, linewidth=0.8, color='#00b4d8', alpha=0.9)
            ax.axhline(preds_noz.mean(), color='#e74c3c', linewidth=1.5, linestyle='--',
                       label=f'Chip mean = {preds_noz.mean():.5f}')
            ax.set_xlabel('Nozzle index (0–1119)')
            ax.set_ylabel('Predicted SD')
            ax.set_title(
                f'Nozzle profile — Chip {chip_sel}  |  {COLOR_NAME[color]}, Coverage={coverage}, '
                f'V={V}, F_r={Fr:.2f}, dt2={dt2}  |  {nozzle_model_choice}'
            )
            ax.legend()
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

            c1n, c2n, c3n = st.columns(3)
            c1n.metric("Mean SD (chip)",   f"{preds_noz.mean():.5f}")
            c2n.metric("Std (nozzle spread)", f"{preds_noz.std():.5f}")
            c3n.metric("Max SD (worst nozzle)", f"{preds_noz.max():.5f}")
