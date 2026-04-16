# 🌍 Safe Haven Index

> What does a "safe haven" mean to *you*? Drag the weights and the answer changes.

Interactive Streamlit dashboard that ranks 61 countries on six global indicators — political stability, energy self-sufficiency, healthcare quality, immigration friendliness, English prevalence, and distance from active conflict hotspots. **You** decide the weights: move the sidebar sliders to see how the ranking reshapes around your priorities.

## Key Findings (equal-weight defaults)

- **Top 5**: Australia, Canada, New Zealand, Norway, Ireland — all combine high political stability, English fluency, and geographic distance from conflict zones
- **Australia stays #1 under every preset** — all six indicator scores ≥65, no weak dimension (structurally safe rather than relying on a single strength)
- **Singapore / UAE ranks are weight-sensitive**: strong on English (SG) or immigration (UAE) but drop out of the top 10 under the security-focused preset
- **Bottom concentrated in South Asia + active conflict zones**: Ukraine (24.9), Pakistan (36.5), Egypt (44.3), Bangladesh (45.3), Nigeria (47.2)
- **Norway jumps to #2 under the security-focused preset** (from #4 at equal weights) — 100% energy self-sufficient plus top-tier stability, just held back on immigration when everything is equally weighted

*(61 major countries, World Bank 2022–2023 data + EF English Proficiency Index)*

## Screenshots

> Run `streamlit run app.py` and open http://localhost:8501

- **Rankings tab**: sortable table with red-yellow-green heat map overlay
- **Map tab**: Plotly choropleth world map coloured by composite score
- **Indicator profile tab**: polar / radar chart for any single country across all six dimensions
- **Sidebar**: six weight sliders + 4 presets (Equal / Security / Lifestyle / Economic)

## Quick start

```bash
pip install -r requirements.txt
python build_index.py          # compute the ranking from the shipped snapshot
streamlit run app.py           # launch the interactive dashboard
```

Refresh from the live World Bank API:

```bash
python build_index.py --live   # hits the WB API, caches to data/raw/
```

The offline snapshot at `data/snapshot/countries.csv` is shipped in the repo, so `streamlit run app.py` works out of the box — no API key, no network required.

## The six indicators

| Indicator | Source | Raw unit | Normalisation |
|---|---|---|---|
| `political_stability` | World Bank `PV.EST` (WGI) | -2.5 .. +2.5 | Clip to theoretical range, linear scale to 0–100 |
| `energy_self_sufficiency` | Derived from WB `EG.IMP.CONS.ZS` | % imports | `100 - imports%`, negative values (net exporters) preserved |
| `healthcare_quality` | WB `SP.DYN.LE00.IN` + `SH.XPD.CHEX.PC.CD` | years × USD | 70% life expectancy + 30% log(spend per capita) |
| `immigration_friendliness` | Net migration rate (per 1,000) | rate | Linear scale over a -10..+15 plausible band |
| `english_prevalence` | EF EPI + native/official language flag | 30–100 | Direct scale |
| `conflict_distance` | Haversine from capital to 14 hotspots (minimum) | km | `log(1 + km)` so "very far" vs. "extremely far" doesn't dominate |

Conflict hotspots list (`data/reference/conflict_zones.csv`, editable):
Ukraine, Gaza, Syria, Yemen, Sudan, Myanmar, Haiti, Somalia, Afghanistan, Taiwan Strait, South China Sea, Korean DMZ, Kashmir, Ethiopia/Tigray.

## How the composite score is computed

```
normalised_weight_i = max(0, w_i) / Σ max(0, w_j)
safe_haven_score    = Σ normalised_weight_i × indicator_score_i
```

Missing values are imputed with the **global median** of that indicator, but the `data_completeness` column makes this transparent — it shows how many of the six indicators were actually observed for each row.

## Folder structure

```
Safe_Haven_Index/
├── README.md
├── requirements.txt
├── build_index.py              # CLI: compute indicators + default ranking
├── app.py                      # Streamlit dashboard
├── data/
│   ├── snapshot/
│   │   └── countries.csv       # Shipped 61-country snapshot (offline fallback)
│   ├── reference/
│   │   ├── conflict_zones.csv  # 14 hotspot coordinates
│   │   └── english_proficiency.csv  # EF EPI + native/official language flag
│   ├── raw/                    # `--live` mode caches WB API responses here
│   └── safe_haven_index.csv    # build_index.py output
└── src/
    ├── fetch.py                # WB API client + offline fallback
    ├── indicators.py           # 6 indicators with 0-100 normalisation
    └── scoring.py              # Weighted composite + ranking
```

## Design trade-offs

- **Why these six indicators?** They were specified by the brief, and they do cover the standard "safe haven" conversation: institutions (political stability), self-reliance (energy), survival (healthcare), integration (English, immigration), geography (conflict distance).
- **Why World Bank as the primary source?** Free, key-less, decades of history, and covers 180+ countries for most indicators. English prevalence and conflict distance aren't in WB, so those use third-party reference data shipped in the repo.
- **Why ship a snapshot?** So anyone cloning the repo can `streamlit run app.py` and immediately see results — no API setup, no download wait. `--live` is there when you want fresh data.
- **When does this score mislead?** When a user cranks a single weight to the maximum. If you push English prevalence to 5 and zero everything else, the Philippines jumps high — but that doesn't make it a safe haven. The whole point of a composite is diversification; reading a single dimension as the answer defeats the exercise.
- **This is not a geopolitical forecast.** It's a conversation tool, not a relocation decision.

## Possible extensions

- Add a time dimension (slide 2010 → 2024) to see how each country's score has shifted
- Add an "issue filter" layer (climate vulnerability, internet freedom, press freedom)
- Run `--live` once and expand snapshot coverage to all 200+ countries
- Make presets shareable via query-string URLs (weights encoded in the link)
