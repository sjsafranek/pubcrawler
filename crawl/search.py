# from pathlib import Path
from math import asin, cos, radians, sin, sqrt

import osmnx as ox
import pandas as pd

# 1. Enable console logging to see cache hits vs. Overpass HTTP requests
ox.settings.log_console = True

# 2. Explicitly enable caching and set an absolute directory path
# OSMnx caches raw Overpass/Nominatim responses on disk by default.
ox.settings.use_cache = True
ox.settings.cache_folder = "cache"
# ox.settings.overpass_rate_limit = False     # DANGER
# ox.settings.cache_folder = Path("/absolute/path/to/your/cache").resolve()

# In-memory caches so repeat searches are instant.
_city_cache: dict[str, dict] = {}
_nearby_cache: dict[tuple, dict] = {}


# Search settings
AMENITY_TAGS = {
    "amenity": [
        "bar",
        "biergarten",
        "brewery",
        "pub"
        # "restaurant"
    ]
}

DETAIL_FIELDS = {
    "name": "name",
    "amenity": "type",
    "opening_hours": "hours",
    "website": "website",
    "phone": "phone",
    "addr:housenumber": "housenumber",
    "addr:street": "street",
    "addr:city": "city",
    "addr:postcode": "postcode"
}


def clean(value):
    """Return a plain string, or None for NaN/empty values."""
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return None
    value = str(value).strip()
    return value or None


def gdf_to_bars(gdf) -> list[dict]:
    """Convert an OSMnx features GeoDataFrame into a list of plain dicts."""
    gdf = gdf[gdf.geometry.notna()].copy()
    if gdf.empty:
        return []

    # Features can be points, polygons (buildings), etc. Use a point that is
    # guaranteed to lie within each geometry so every bar can go on the map.
    points = gdf.geometry.representative_point()
    gdf["lat"], gdf["lon"] = points.y, points.x

    bars = []
    for (element, osm_id), row in gdf.iterrows():
        bar = {"id": f"{element}/{osm_id}", "lat": row["lat"], "lon": row["lon"]}
        for column, field in DETAIL_FIELDS.items():
            bar[field] = clean(row.get(column))

        street = " ".join(p for p in (bar["housenumber"], bar["street"]) if p)
        bar["address"] = street or None
        bar["name"] = bar["name"] or "Unnamed " + (bar["type"] or "bar")
        bars.append(bar)
    return bars


def fetch_bars(city: str) -> dict:
    key = city.strip().lower()
    if key in _city_cache:
        return _city_cache[key]

    gdf = ox.features.features_from_place(city, tags=AMENITY_TAGS)
    bars = sorted(gdf_to_bars(gdf), key=lambda b: b["name"].lower())

    result = {"city": city.strip(), "count": len(bars), "bars": bars}
    _city_cache[key] = result
    return result
