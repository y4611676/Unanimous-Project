# Where Should You Move (or Relocate Staff, or Place Capital) — and Why?

An interactive tool that ranks **61 countries across six indicators of stability** — and lets the person making the decision set the weights themselves. Because "safe" means different things depending on whether you're an HR lead, a family considering immigration, or an investor assessing country risk.

## This analysis is for you if:

- You're making a high-stakes location decision (relocation, office expansion, capital allocation) and country rankings from the news don't match your actual priorities
- You need to justify a country choice to a board, a partner, or a family — and you want a defensible, transparent score instead of "I read it on a blog"
- You suspect the standard "safe country" list has blind spots for your situation (e.g., English fluency matters to you but nobody weights it)

---

## What We Found (And Why the Defaults Might Not Be Your Answer)

The headline rankings hide something important: **the "top safe country" changes based on what you actually care about.** That's the entire point of the tool — not to give you one answer, but to let you see how fragile or robust any ranking is.

### Finding 1: Australia is structurally #1 — not because of one strength

Under **every preset** — equal weights, security-focused, lifestyle-focused, economic — Australia stays at #1. Why? All six indicator scores are ≥65. No weak dimension.

**What this tells you:** Countries that win on diversification beat countries that win on one axis. If you're making a multi-year commitment, "no weak spot" matters more than "great at one thing."

### Finding 2: Top 5 and bottom 5 tell opposite stories

- **Top 5** (equal weights): Australia, Canada, New Zealand, Norway, Ireland — all high stability, English-speaking, geographically far from conflict zones
- **Bottom**: Ukraine (24.9), Pakistan (36.5), Egypt (44.3), Bangladesh (45.3), Nigeria (47.2) — concentrated in South Asia and active conflict regions

**What this tells you:** The safety premium isn't evenly distributed. The gap between top-10 and mid-pack countries is much smaller than the gap between mid-pack and bottom-10 — which is where the real risk lives.

### Finding 3: Singapore, UAE, and Norway move dramatically based on weights

- **Singapore** and **UAE**: top-10 under lifestyle/economic presets, drop out under security-focused
- **Norway**: #4 at equal weights, jumps to #2 under security-focused (100% energy self-sufficiency + top stability)

**What this tells you:** If your decision is **security-driven** (e.g., capital protection, family with young children), your shortlist should look different from someone optimizing for **lifestyle** (e.g., climate, English, immigration ease). Using a generic "top 10 safest countries" list blends both audiences and serves neither.

---

## What You Get

A conversation tool, not a forecast. You move the weights based on *your* priorities and the ranking updates instantly:

| Feature | What It Helps You Decide |
|---------|-------------------------|
| Sortable ranking with heat-map overlay | See the top 10 at a glance under any weighting |
| Interactive world map | Spot regional clusters (Scandinavia, Oceania, South Asia) |
| Per-country radar chart | Understand *why* a country ranks where it does |
| Four presets (Equal / Security / Lifestyle / Economic) | Quickly test scenarios without manual weight-tuning |
| Six weight sliders | Customize to your exact priorities |
| Data transparency column | See which indicators are measured vs. imputed for each country |

Six indicators: political stability, energy self-sufficiency, healthcare quality, immigration friendliness, English prevalence, and distance from conflict zones.

---

## Want the Same Analysis on Your Data or Decision?

The same pattern — weighted composite scoring across multiple indicators, with user-adjustable priorities — applies to almost any multi-criteria decision:

- **Vendor selection** (cost, reliability, geography, compliance)
- **Market entry prioritization** (demand, competition, regulation, logistics)
- **Real estate or office location** (rent, access, talent, safety)
- **Portfolio allocation** (risk, return, liquidity, correlation)

**What we need from you:**
- Your candidates (countries, vendors, markets, properties — whatever you're comparing)
- The indicators that matter in your context (we can help identify them)
- Rough data sources (we can help find free public ones if needed)

**What you get back:**
- A shipped interactive tool (Streamlit, web-hosted, or standalone) where the decision-maker can set weights and see results in real time
- Transparent scoring so the ranking can be explained, defended, and revised
- Preset views tuned to the most likely scenarios

Reach out through the portfolio main page.

---

## For Technical Readers

Interactive Streamlit dashboard that scores countries on six global indicators and lets the user adjust weights in real time.

### Screenshots

> Run `streamlit run app.py` and open http://localhost:8501

- **Rankings tab**: sortable table with red-yellow-green heat map overlay
- **Map tab**: Plotly choropleth world map coloured by composite score
- **Indicator profile tab**: polar / radar chart for any single country across all six dimensions
- **Similar countries tab**: k-means clustering (scikit-learn) — pick an anchor country and see the 5 closest profile neighbours plus the full cluster map. Rankings change when you move the sliders; clustering doesn't, which makes it the right lens for "find countries that behave like this one."
- **Sidebar**: six weight sliders + 4 presets (Equal / Security / Lifestyle / Economic)

### Quick start

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

### The Six Indicators

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

### How the Composite Score Is Computed

```
normalised_weight_i = max(0, w_i) / Σ max(0, w_j)
safe_haven_score    = Σ normalised_weight_i × indicator_score_i
```

Missing values are imputed with the **global median** of that indicator, but the `data_completeness` column makes this transparent — it shows how many of the six indicators were actually observed for each row.

### Folder Structure

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
    ├── scoring.py              # Weighted composite + ranking
    └── clustering.py           # K-means clusters + nearest-profile lookup
```

### Design Trade-offs

- **Why these six indicators?** They cover the standard "safe haven" conversation: institutions (political stability), self-reliance (energy), survival (healthcare), integration (English, immigration), geography (conflict distance).
- **Why World Bank as the primary source?** Free, key-less, decades of history, 180+ country coverage. English prevalence and conflict distance aren't in WB, so those use third-party reference data shipped in the repo.
- **Why ship a snapshot?** Anyone cloning the repo can `streamlit run app.py` immediately — no API setup, no download wait. `--live` is there when you want fresh data.
- **When does this score mislead?** When a user cranks a single weight to the maximum. If you push English prevalence to 5 and zero everything else, the Philippines jumps high — but that doesn't make it a safe haven. The whole point of a composite is diversification; reading a single dimension as the answer defeats the exercise.
- **This is not a geopolitical forecast.** It's a conversation tool, not a relocation decision.

### Possible Extensions

- Add a time dimension (slide 2010 → 2024) to see how each country's score has shifted
- Add an "issue filter" layer (climate vulnerability, internet freedom, press freedom)
- Run `--live` once and expand snapshot coverage to all 200+ countries
- Make presets shareable via query-string URLs (weights encoded in the link)
