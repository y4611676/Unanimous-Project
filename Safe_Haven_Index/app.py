"""Streamlit dashboard for the Safe Haven Index.

Run::

    streamlit run app.py

The sidebar exposes one slider per indicator — move them and the ranking
+ world map update live.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.indicators import INDICATOR_FUNCS, INDICATOR_LABELS, build_all
from src.scoring import compute_index


ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Safe Haven Index",
    page_icon="🌍",
    layout="wide",
)


@st.cache_data(show_spinner="Computing indicators...")
def load_base() -> pd.DataFrame:
    """Indicator table — expensive to compute, cache across slider changes."""
    return build_all(live=False)


# ─── Header ─────────────────────────────────────────────────────────────────

st.title("🌍 Safe Haven Index")
st.caption(
    "Composite score of six indicators per country — political stability, energy "
    "self-sufficiency, healthcare, immigration friendliness, English prevalence, and "
    "distance from conflict hotspots. Adjust the weights in the sidebar to see how "
    "your priorities reshape the ranking."
)

base = load_base()

# ─── Sidebar: weight sliders ────────────────────────────────────────────────

st.sidebar.header("⚖️  指標權重")
st.sidebar.caption("Drag the sliders — total is auto-normalised.")

weights: dict[str, float] = {}
for name in INDICATOR_FUNCS:
    label = f"{INDICATOR_LABELS[name]} · {name}"
    weights[name] = st.sidebar.slider(label, 0.0, 5.0, 1.0, 0.1)

st.sidebar.divider()
preset = st.sidebar.radio(
    "Preset",
    ["Custom", "Equal (reset)", "Security-focused", "Lifestyle-focused", "Economic-focused"],
    index=0,
)
if preset != "Custom":
    presets = {
        "Equal (reset)": {k: 1.0 for k in INDICATOR_FUNCS},
        "Security-focused": {
            "political_stability": 3.0, "conflict_distance": 3.0,
            "energy_self_sufficiency": 2.0, "healthcare_quality": 1.0,
            "immigration_friendliness": 0.5, "english_prevalence": 0.5,
        },
        "Lifestyle-focused": {
            "healthcare_quality": 3.0, "english_prevalence": 2.5,
            "immigration_friendliness": 2.0, "political_stability": 1.5,
            "conflict_distance": 0.5, "energy_self_sufficiency": 0.5,
        },
        "Economic-focused": {
            "energy_self_sufficiency": 3.0, "political_stability": 2.5,
            "healthcare_quality": 1.0, "immigration_friendliness": 1.0,
            "english_prevalence": 1.0, "conflict_distance": 1.0,
        },
    }
    weights = presets[preset]
    st.sidebar.caption("📌 Using preset — reset to Custom to edit sliders.")

# ─── Compute + display ──────────────────────────────────────────────────────

ranked = compute_index(base, weights)

col1, col2, col3 = st.columns(3)
col1.metric("Countries ranked", len(ranked))
col2.metric("Top country", ranked.iloc[0]["country"], f"{ranked.iloc[0]['safe_haven_score']:.1f}")
total_weight = sum(max(0, w) for w in weights.values())
col3.metric("Active weight", f"{total_weight:.1f}")

tab1, tab2, tab3, tab4 = st.tabs(
    ["🏆 Rankings", "🗺️ Map", "📊 Indicator profile", "ℹ️ About"]
)

# Tab 1: ranked table ---------------------------------------------------------
with tab1:
    display_cols = ["rank", "country", "region", "safe_haven_score"] + list(INDICATOR_FUNCS) + [
        "data_completeness"
    ]
    display_cols = [c for c in display_cols if c in ranked.columns]
    renamed = ranked[display_cols].rename(columns={**INDICATOR_LABELS, "safe_haven_score": "Score"})
    st.dataframe(
        renamed.style.background_gradient(
            subset=[c for c in renamed.columns if c in INDICATOR_LABELS.values()] + ["Score"],
            cmap="RdYlGn",
        ).format({c: "{:.1f}" for c in renamed.columns if c in INDICATOR_LABELS.values()} | {
            "Score": "{:.1f}", "data_completeness": "{:.0%}"
        }),
        use_container_width=True,
        height=700,
    )

# Tab 2: world map ------------------------------------------------------------
with tab2:
    try:
        import plotly.express as px
        fig = px.choropleth(
            ranked,
            locations="iso3",
            color="safe_haven_score",
            hover_name="country",
            hover_data={
                "rank": True,
                "safe_haven_score": ":.1f",
                "iso3": False,
                **{c: ":.0f" for c in INDICATOR_FUNCS if c in ranked.columns},
            },
            color_continuous_scale="RdYlGn",
            range_color=[0, 100],
        )
        fig.update_layout(
            margin={"r": 0, "t": 20, "l": 0, "b": 0},
            coloraxis_colorbar_title="Score",
            geo=dict(showframe=False, showcoastlines=True, projection_type="natural earth"),
        )
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.warning("`plotly` not installed — run `pip install plotly` to see the world map.")

# Tab 3: single-country profile ----------------------------------------------
with tab3:
    country = st.selectbox("Country", ranked["country"].tolist())
    row = ranked[ranked["country"] == country].iloc[0]
    st.metric(f"{country}", f"#{row['rank']} — {row['safe_haven_score']:.1f}")

    indicator_scores = {
        INDICATOR_LABELS[name]: row[name]
        for name in INDICATOR_FUNCS if name in ranked.columns
    }
    profile = pd.DataFrame({
        "indicator": list(indicator_scores.keys()),
        "score": list(indicator_scores.values()),
    })

    try:
        import plotly.express as px
        fig = px.bar_polar(
            profile, r="score", theta="indicator",
            color="score", color_continuous_scale="RdYlGn",
            range_color=[0, 100],
        )
        fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])), height=500)
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.bar_chart(profile.set_index("indicator"))

    st.caption(f"Data completeness: {row['data_completeness']:.0%}")

# Tab 4: methodology ---------------------------------------------------------
with tab4:
    st.markdown(
        """
        ### Methodology

        Each of the six indicators is normalized to a 0–100 score (higher = safer /
        more desirable for "safe haven" framing). The composite score is the
        weight-normalised average.

        | Indicator | Source | Raw unit |
        |---|---|---|
        | Political stability | World Bank — `PV.EST` | -2.5 .. +2.5 |
        | Energy self-sufficiency | World Bank — derived from `EG.IMP.CONS.ZS` | -% imports |
        | Healthcare quality | World Bank — life expectancy × health spend | composite |
        | Immigration friendliness | World Bank — net migration per 1,000 | rate |
        | English prevalence | EF English Proficiency Index + native flag | 30–100 |
        | Distance from conflict | Haversine from capital to 14 hotspots | km (log) |

        Missing values are imputed with the global median so a single gap doesn't
        disqualify a country. The `data_completeness` column shows what fraction
        of the six indicators were actually observed for each row.

        **Not a geopolitical forecast.** This is a back-of-the-envelope
        relocation-optionality index — useful for conversations, not decisions.
        """
    )
