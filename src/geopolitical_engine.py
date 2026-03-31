"""
geopolitical_engine.py - Geopolitical Context Engine for TerraScout AI

Provides deep geopolitical intelligence for any coordinate on Earth by
combining reverse geocoding, country metadata, World Bank development
indicators, nearby Wikipedia context, and a composite risk/stability score.

All data comes from free, open APIs with no API keys required:
  - Nominatim (OpenStreetMap reverse geocoding)
  - REST Countries v3.1
  - World Bank Indicators API v2
  - Wikipedia GeoSearch API

Author: TerraScout AI Platform
"""

import logging
import math
import requests
import streamlit as st

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_NOMINATIM_REVERSE_URL = (
    "https://nominatim.openstreetmap.org/reverse"
    "?lat={lat}&lon={lon}&format=json&zoom=3"
)

_REST_COUNTRIES_URL = (
    "https://restcountries.com/v3.1/alpha/{code}"
    "?fields=name,capital,region,subregion,population,area,"
    "languages,currencies,borders,timezones,flags,gini,car,"
    "demonyms,latlng,landlocked,unMember"
)

_WORLD_BANK_URL = (
    "https://api.worldbank.org/v2/country/{code}/indicator/{indicator}"
    "?format=json&date=2018:2024&per_page=1"
)

_WIKIPEDIA_GEOSEARCH_URL = (
    "https://en.wikipedia.org/w/api.php"
    "?action=query&list=geosearch"
    "&gsradius={radius_m}&gscoord={lat}|{lon}"
    "&gslimit=10&format=json"
)

_REQUEST_HEADERS = {"User-Agent": "TerraScout-AI/2.0"}

# World Bank indicator codes and their human-readable names
_WB_INDICATORS = {
    "NY.GDP.PCAP.CD":  "gdp_per_capita_usd",
    "SP.DYN.LE00.IN":  "life_expectancy",
    "SE.ADT.LITR.ZS":  "adult_literacy_pct",
    "EG.ELC.ACCS.ZS":  "electricity_access_pct",
    "SH.H2O.BASW.ZS":  "basic_water_access_pct",
    "IT.NET.USER.ZS":  "internet_users_pct",
    "SI.POV.DDAY":     "poverty_headcount_pct",
    "EN.ATM.CO2E.PC":  "co2_per_capita",
}


# ---------------------------------------------------------------------------
# 1. Country Context (Nominatim + REST Countries)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def fetch_country_context(lat: float, lon: float) -> dict:
    """Reverse-geocode a coordinate to its country and fetch rich metadata.

    Uses Nominatim to resolve the ISO alpha-2 country code, then queries
    REST Countries v3.1 for comprehensive country-level data.

    Parameters
    ----------
    lat : float
        Latitude in decimal degrees.
    lon : float
        Longitude in decimal degrees.

    Returns
    -------
    dict
        Country metadata including name, capital, region, population,
        area, languages, currencies, borders, timezones, driving side,
        Gini index, flag URL, and more.  Returns an empty dict on failure.
    """

    # --- Step 1: Reverse geocode to get the country code ----------------
    country_code = None
    try:
        nominatim_url = _NOMINATIM_REVERSE_URL.format(lat=lat, lon=lon)
        resp = requests.get(nominatim_url, headers=_REQUEST_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        address = data.get("address", {})
        country_code = (address.get("country_code") or "").upper()
    except Exception as exc:
        logger.warning("Nominatim reverse geocode failed for (%.4f, %.4f): %s",
                       lat, lon, exc)
        return {}

    if not country_code or len(country_code) != 2:
        logger.warning("No valid country code found for (%.4f, %.4f)", lat, lon)
        return {}

    # --- Step 2: Fetch country details from REST Countries --------------
    try:
        rc_url = _REST_COUNTRIES_URL.format(code=country_code)
        resp = requests.get(rc_url, timeout=10)
        resp.raise_for_status()
        c = resp.json()  # single dict for /alpha/{code} with fields param
    except Exception as exc:
        logger.warning("REST Countries lookup failed for %s: %s",
                       country_code, exc)
        return {"country_code": country_code}

    # --- Step 3: Parse into a normalized dict ----------------------------
    # Name
    name_block = c.get("name", {})
    country_name = name_block.get("common", name_block.get("official", ""))

    # Capital (list in REST Countries v3.1)
    capitals = c.get("capital", [])
    capital = capitals[0] if capitals else ""

    # Languages — {"eng": "English", "fra": "French"} -> list of names
    lang_dict = c.get("languages", {})
    languages = list(lang_dict.values()) if isinstance(lang_dict, dict) else []

    # Currencies — {"USD": {"name": "US Dollar", "symbol": "$"}} -> list
    cur_raw = c.get("currencies", {})
    currencies = []
    if isinstance(cur_raw, dict):
        for code, info in cur_raw.items():
            if isinstance(info, dict):
                currencies.append({
                    "code": code,
                    "name": info.get("name", ""),
                    "symbol": info.get("symbol", ""),
                })

    # Population & area
    population = c.get("population", 0) or 0
    area_km2 = c.get("area", 0.0) or 0.0
    population_density = (population / area_km2) if area_km2 > 0 else 0.0

    # Gini index — {"2019": 34.8} -> take most recent value
    gini_raw = c.get("gini", {})
    gini_index = None
    if isinstance(gini_raw, dict) and gini_raw:
        latest_year = max(gini_raw.keys())
        gini_index = gini_raw.get(latest_year)

    # Driving side
    car_block = c.get("car", {})
    driving_side = car_block.get("side", "unknown") if isinstance(car_block, dict) else "unknown"

    # Flag URL (SVG)
    flags_block = c.get("flags", {})
    flag_url = flags_block.get("svg", flags_block.get("png", "")) if isinstance(flags_block, dict) else ""

    # Center coordinates
    center_latlng = c.get("latlng", [0, 0])

    return {
        "country_name":       country_name,
        "country_code":       country_code,
        "capital":            capital,
        "region":             c.get("region", ""),
        "subregion":          c.get("subregion", ""),
        "population":         population,
        "area_km2":           area_km2,
        "population_density": round(population_density, 2),
        "languages":          languages,
        "currencies":         currencies,
        "borders":            c.get("borders", []),
        "timezones":          c.get("timezones", []),
        "landlocked":         c.get("landlocked", False),
        "un_member":          c.get("unMember", False),
        "driving_side":       driving_side,
        "gini_index":         gini_index,
        "flag_url":           flag_url,
        "center_latlng":      center_latlng,
    }


# ---------------------------------------------------------------------------
# 2. World Bank Development Indicators
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def _fetch_single_wb_indicator(country_code: str, indicator_code: str) -> float | None:
    """Fetch a single World Bank indicator value for a country.

    Queries the most recent data between 2018-2024 and returns the first
    non-null value found.

    Parameters
    ----------
    country_code : str
        ISO 3166-1 alpha-2 country code.
    indicator_code : str
        World Bank indicator code (e.g. ``NY.GDP.PCAP.CD``).

    Returns
    -------
    float or None
        The indicator value, or None if unavailable.
    """
    try:
        url = _WORLD_BANK_URL.format(code=country_code, indicator=indicator_code)
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        payload = resp.json()

        # World Bank response: [{paging}, [{record}, ...]]
        if not isinstance(payload, list) or len(payload) < 2:
            return None

        records = payload[1]
        if not isinstance(records, list):
            return None

        # Return the first non-null value (most recent year first)
        for record in records:
            if isinstance(record, dict):
                value = record.get("value")
                if value is not None:
                    return float(value)

        return None

    except Exception as exc:
        logger.warning("World Bank indicator %s for %s failed: %s",
                       indicator_code, country_code, exc)
        return None


@st.cache_data(ttl=3600)
def fetch_world_bank_indicators(country_code: str) -> dict:
    """Fetch a suite of development indicators from the World Bank API.

    Fetches GDP per capita, life expectancy, literacy, electricity/water
    access, internet penetration, poverty rate, and CO2 emissions per
    capita.  Each indicator is fetched independently so that failures in
    one do not block the others.

    Parameters
    ----------
    country_code : str
        ISO 3166-1 alpha-2 country code (e.g. ``US``, ``DE``, ``BR``).

    Returns
    -------
    dict
        Mapping of human-readable indicator names to float values.
        Indicators that could not be retrieved are omitted.
    """
    if not country_code:
        return {}

    results = {}
    for wb_code, friendly_name in _WB_INDICATORS.items():
        value = _fetch_single_wb_indicator(country_code, wb_code)
        if value is not None:
            results[friendly_name] = round(value, 4)

    return results


# ---------------------------------------------------------------------------
# 3. Nearby Wikipedia Articles
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def fetch_nearby_wikipedia(lat: float, lon: float, radius_km: float = 10) -> list:
    """Fetch Wikipedia articles geotagged near a coordinate.

    Uses the MediaWiki GeoSearch API to find up to 10 articles within
    *radius_km* of the given point.

    Parameters
    ----------
    lat : float
        Latitude in decimal degrees.
    lon : float
        Longitude in decimal degrees.
    radius_km : float, optional
        Search radius in kilometres (default 10, max 10).

    Returns
    -------
    list of dict
        Each dict contains ``title``, ``distance_m``, ``lat``, ``lon``,
        and ``pageid`` for a nearby Wikipedia article.  Returns an empty
        list on failure.
    """
    # Wikipedia geosearch accepts radius in metres, max 10 000
    radius_m = int(min(radius_km * 1000, 10000))
    if radius_m < 10:
        radius_m = 10

    try:
        url = _WIKIPEDIA_GEOSEARCH_URL.format(
            radius_m=radius_m, lat=lat, lon=lon
        )
        resp = requests.get(url, headers=_REQUEST_HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("Wikipedia geosearch failed for (%.4f, %.4f): %s",
                       lat, lon, exc)
        return []

    raw_results = (
        data.get("query", {}).get("geosearch", [])
        if isinstance(data, dict) else []
    )

    articles = []
    for item in raw_results:
        if not isinstance(item, dict):
            continue
        articles.append({
            "title":      item.get("title", ""),
            "distance_m": item.get("dist", 0.0),
            "lat":        item.get("lat", 0.0),
            "lon":        item.get("lon", 0.0),
            "pageid":     item.get("pageid", 0),
        })

    return articles


# ---------------------------------------------------------------------------
# 4. Geopolitical Risk / Stability Score
# ---------------------------------------------------------------------------

def compute_geopolitical_risk_score(
    country_context: dict,
    world_bank: dict,
) -> dict:
    """Compute a composite geopolitical stability score from 0 to 100.

    The score starts at a neutral baseline of 50 and is adjusted up or
    down based on socio-economic indicators, UN membership, landlocked
    status, inequality (Gini), and population density.

    Parameters
    ----------
    country_context : dict
        Output of :func:`fetch_country_context`.
    world_bank : dict
        Output of :func:`fetch_world_bank_indicators`.

    Returns
    -------
    dict
        ``"geopolitical_score"`` (float, 0-100) and ``"factors"`` (list
        of dicts with ``name``, ``impact``, and ``detail``).
    """
    score = 50.0
    factors: list[dict] = []

    def _apply(name: str, impact: float, detail: str):
        nonlocal score
        score += impact
        factors.append({"name": name, "impact": impact, "detail": detail})

    # -- GDP per capita --------------------------------------------------
    gdp = world_bank.get("gdp_per_capita_usd")
    if gdp is not None:
        if gdp > 30000:
            _apply("GDP per capita", 15,
                   f"${gdp:,.0f} — high-income economy")
        elif gdp > 10000:
            _apply("GDP per capita", 8,
                   f"${gdp:,.0f} — upper-middle income")
        elif gdp > 3000:
            _apply("GDP per capita", 3,
                   f"${gdp:,.0f} — lower-middle income")
        else:
            _apply("GDP per capita", -10,
                   f"${gdp:,.0f} — low-income economy")

    # -- Life expectancy -------------------------------------------------
    life_exp = world_bank.get("life_expectancy")
    if life_exp is not None:
        if life_exp > 75:
            _apply("Life expectancy", 10,
                   f"{life_exp:.1f} years — above global average")
        elif life_exp > 65:
            _apply("Life expectancy", 5,
                   f"{life_exp:.1f} years — moderate")
        else:
            _apply("Life expectancy", -10,
                   f"{life_exp:.1f} years — below global average")

    # -- Adult literacy --------------------------------------------------
    literacy = world_bank.get("adult_literacy_pct")
    if literacy is not None:
        if literacy > 95:
            _apply("Adult literacy", 5,
                   f"{literacy:.1f}% — near-universal literacy")
        elif literacy > 80:
            _apply("Adult literacy", 2,
                   f"{literacy:.1f}% — moderate literacy")
        else:
            _apply("Adult literacy", -8,
                   f"{literacy:.1f}% — low literacy rate")

    # -- Electricity access ----------------------------------------------
    elec = world_bank.get("electricity_access_pct")
    if elec is not None:
        if elec > 95:
            _apply("Electricity access", 5,
                   f"{elec:.1f}% — near-universal access")
        elif elec > 70:
            _apply("Electricity access", 2,
                   f"{elec:.1f}% — moderate access")
        else:
            _apply("Electricity access", -8,
                   f"{elec:.1f}% — limited access")

    # -- Basic water access ----------------------------------------------
    water = world_bank.get("basic_water_access_pct")
    if water is not None:
        if water > 95:
            _apply("Basic water access", 5,
                   f"{water:.1f}% — near-universal access")
        elif water > 70:
            _apply("Basic water access", 2,
                   f"{water:.1f}% — moderate access")
        else:
            _apply("Basic water access", -8,
                   f"{water:.1f}% — limited access")

    # -- Internet users --------------------------------------------------
    internet = world_bank.get("internet_users_pct")
    if internet is not None:
        if internet > 70:
            _apply("Internet penetration", 5,
                   f"{internet:.1f}% — well-connected population")
        elif internet > 40:
            _apply("Internet penetration", 2,
                   f"{internet:.1f}% — moderate connectivity")
        else:
            _apply("Internet penetration", -5,
                   f"{internet:.1f}% — low connectivity")

    # -- Poverty headcount -----------------------------------------------
    poverty = world_bank.get("poverty_headcount_pct")
    if poverty is not None:
        if poverty < 5:
            _apply("Poverty rate", 5,
                   f"{poverty:.1f}% — low extreme poverty")
        elif poverty < 15:
            _apply("Poverty rate", 2,
                   f"{poverty:.1f}% — moderate poverty")
        else:
            _apply("Poverty rate", -10,
                   f"{poverty:.1f}% — high extreme poverty")

    # -- UN Membership ---------------------------------------------------
    un_member = country_context.get("un_member", False)
    if un_member:
        _apply("UN membership", 3,
               "Full UN member state")

    # -- Landlocked status -----------------------------------------------
    landlocked = country_context.get("landlocked", False)
    if landlocked:
        _apply("Landlocked", -3,
               "No direct ocean access — trade constraints")

    # -- Gini index (inequality) -----------------------------------------
    gini = country_context.get("gini_index")
    if gini is not None:
        if gini > 50:
            _apply("Income inequality (Gini)", -5,
                   f"Gini {gini:.1f} — very high inequality")
        elif gini > 40:
            _apply("Income inequality (Gini)", -2,
                   f"Gini {gini:.1f} — moderate inequality")
        elif gini < 30:
            _apply("Income inequality (Gini)", 3,
                   f"Gini {gini:.1f} — low inequality")

    # -- Population density ----------------------------------------------
    pop_density = country_context.get("population_density", 0)
    if pop_density > 1000:
        _apply("Population density", -3,
               f"{pop_density:.0f}/km2 — overcrowded")
    elif pop_density < 2:
        _apply("Population density", -2,
               f"{pop_density:.1f}/km2 — extremely remote")
    elif 10 <= pop_density <= 300:
        _apply("Population density", 2,
               f"{pop_density:.1f}/km2 — balanced density")

    # -- Clamp to [0, 100] -----------------------------------------------
    score = max(0.0, min(100.0, score))

    return {
        "geopolitical_score": round(score, 1),
        "factors": factors,
    }


# ---------------------------------------------------------------------------
# 5. Complete Geopolitical Profile (Master Function)
# ---------------------------------------------------------------------------

def _score_to_grade(score: float) -> str:
    """Convert a numeric geopolitical score to a letter grade.

    Parameters
    ----------
    score : float
        Score between 0 and 100.

    Returns
    -------
    str
        One of ``A``, ``B``, ``C``, ``D``, ``F``.
    """
    if score >= 80:
        return "A"
    if score >= 65:
        return "B"
    if score >= 50:
        return "C"
    if score >= 35:
        return "D"
    return "F"


def fetch_complete_geopolitical_profile(lat: float, lon: float) -> dict:
    """Build a full geopolitical intelligence profile for a coordinate.

    Orchestrates all four sub-functions:

    1. **Country context** — name, capital, population, currencies, etc.
    2. **World Bank indicators** — GDP, life expectancy, literacy, etc.
    3. **Nearby Wikipedia** — geotagged articles within 10 km.
    4. **Geopolitical score** — composite stability index 0-100 with
       breakdown of contributing factors.

    Parameters
    ----------
    lat : float
        Latitude in decimal degrees.
    lon : float
        Longitude in decimal degrees.

    Returns
    -------
    dict
        Unified profile with keys ``country``, ``indicators``,
        ``nearby_wikipedia``, ``geopolitical_score``,
        ``geopolitical_factors``, and ``geopolitical_grade``.
        Returns a minimal dict with empty values if the coordinate
        cannot be resolved to a country.
    """
    # --- Country context -------------------------------------------------
    country_ctx = fetch_country_context(lat, lon)
    if not country_ctx:
        logger.warning(
            "Could not resolve country for (%.4f, %.4f) — "
            "returning empty profile.",
            lat, lon,
        )
        return {
            "country":              {},
            "indicators":           {},
            "nearby_wikipedia":     [],
            "geopolitical_score":   0.0,
            "geopolitical_factors": [],
            "geopolitical_grade":   "F",
        }

    country_code = country_ctx.get("country_code", "")

    # --- World Bank indicators -------------------------------------------
    wb_indicators = fetch_world_bank_indicators(country_code)

    # --- Nearby Wikipedia articles ---------------------------------------
    wiki_articles = fetch_nearby_wikipedia(lat, lon, radius_km=10)

    # --- Geopolitical risk score -----------------------------------------
    score_result = compute_geopolitical_risk_score(country_ctx, wb_indicators)
    geo_score = score_result["geopolitical_score"]
    geo_factors = score_result["factors"]
    geo_grade = _score_to_grade(geo_score)

    return {
        "country":              country_ctx,
        "indicators":           wb_indicators,
        "nearby_wikipedia":     wiki_articles,
        "geopolitical_score":   geo_score,
        "geopolitical_factors": geo_factors,
        "geopolitical_grade":   geo_grade,
    }
