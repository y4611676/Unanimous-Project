"""World Bank API client with disk caching and offline-snapshot fallback.

The World Bank Open Data API is free and key-less::

    https://api.worldbank.org/v2/country/all/indicator/{code}?format=json&per_page=20000&date=2018:2023

Each call returns ``[metadata, [ {country: {...}, value, date, ...}, ... ] ]``.

Strategy:
* ``fetch_indicator(code, live=True)`` — hit the API, cache to ``data/raw/``
* ``fetch_indicator(code, live=False)`` — read only from cache
* If the live call fails (e.g. GitHub Codespaces with egress blocked), we
  silently fall back to the shipped snapshot in ``data/snapshot/countries.csv``
  so the pipeline + app still work out of the box.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
SNAPSHOT = ROOT / "data" / "snapshot" / "countries.csv"

# Indicator codes used by the Safe Haven Index.
# The snapshot CSV is organised so each column maps to one of these, meaning
# the offline fallback and the live API can be exchanged seamlessly.
INDICATORS = {
    "PV.EST":          "political_stability",     # Political Stability & Absence of Violence
    "EG.IMP.CONS.ZS":  "energy_imports_pct",      # Energy imports, net (% of energy use)
    "SP.DYN.LE00.IN":  "life_expectancy",         # Life expectancy at birth
    "SH.XPD.CHEX.PC.CD": "health_exp_per_capita_usd",  # Health expenditure per capita (USD)
    "SM.POP.NETM":     "net_migration_abs",       # Net migration (absolute, 5y window)
}


def _api_url(code: str, date: str = "2018:2023") -> str:
    return (
        f"https://api.worldbank.org/v2/country/all/indicator/{code}"
        f"?format=json&per_page=20000&date={date}"
    )


def _http_get(url: str, timeout: int = 20) -> Any:
    """Minimal GET that doesn't drag in the ``requests`` dependency for the
    base case. Falls through to ``urllib`` so the package has zero extras."""
    import urllib.request
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_indicator_live(code: str, date: str = "2018:2023") -> pd.DataFrame:
    """Fetch one indicator from WB API, return tidy DataFrame ``iso3,year,value``.

    Keeps the most recent non-null observation per country because many WB
    indicators are published with 1–2 year lag.
    """
    data = _http_get(_api_url(code, date))
    if not isinstance(data, list) or len(data) < 2 or data[1] is None:
        return pd.DataFrame(columns=["iso3", "year", "value"])
    rows = []
    for rec in data[1]:
        iso3 = rec.get("countryiso3code") or ""
        value = rec.get("value")
        year = rec.get("date")
        if not iso3 or value is None:
            continue
        rows.append((iso3, int(year), float(value)))
    df = pd.DataFrame(rows, columns=["iso3", "year", "value"])
    # Keep most recent year per country.
    df = df.sort_values(["iso3", "year"]).drop_duplicates("iso3", keep="last")
    return df.reset_index(drop=True)


def cache_path(code: str) -> Path:
    return RAW_DIR / f"{code.replace('.', '_')}.csv"


def fetch_indicator(code: str, live: bool = False) -> pd.DataFrame:
    """Return an indicator series ``iso3,value`` from cache or API."""
    cache = cache_path(code)
    if live:
        try:
            df = fetch_indicator_live(code)
            RAW_DIR.mkdir(parents=True, exist_ok=True)
            df.to_csv(cache, index=False)
            return df
        except Exception as e:  # pragma: no cover — network failures
            print(f"  ⚠️  live fetch failed for {code}: {e}", file=sys.stderr)
            print(f"      falling back to cache / snapshot", file=sys.stderr)

    if cache.exists():
        return pd.read_csv(cache)

    # Fallback: derive the series from the shipped snapshot.
    return _from_snapshot(code)


def _from_snapshot(code: str) -> pd.DataFrame:
    """Extract one indicator column from ``data/snapshot/countries.csv``."""
    if not SNAPSHOT.exists():
        return pd.DataFrame(columns=["iso3", "value"])
    snap = pd.read_csv(SNAPSHOT)
    col = INDICATORS.get(code)
    if col is None or col not in snap.columns:
        return pd.DataFrame(columns=["iso3", "value"])
    return snap[["iso3", col]].rename(columns={col: "value"})


def load_snapshot() -> pd.DataFrame:
    """Load the shipped snapshot (used by indicators that don't live on WB)."""
    return pd.read_csv(SNAPSHOT)


def load_english_proficiency() -> pd.DataFrame:
    return pd.read_csv(ROOT / "data" / "reference" / "english_proficiency.csv")


def load_conflict_zones() -> pd.DataFrame:
    return pd.read_csv(ROOT / "data" / "reference" / "conflict_zones.csv")
