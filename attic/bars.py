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

        street = " ".join(p for p in (bar.pop("housenumber"), bar.pop("street")) if p)
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


def haversine_m(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance in meters between two lat/lon points."""
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * 6_371_000 * asin(sqrt(a))


def fetch_bars_nearby(lat: float, lon: float, radius: float) -> dict:
    key = (round(lat, 5), round(lon, 5), round(radius))
    print(key)
    if key in _nearby_cache:
        return _nearby_cache[key]

    try:
        # OSMnx queries a square bounding box around the point...
        gdf = ox.features.features_from_point((lat, lon), tags=AMENITY_TAGS, dist=radius)
        bars = gdf_to_bars(gdf)
    except Exception as exc:
        if "no matching features" not in str(exc).lower():
            raise
        bars = []  # nothing mapped in this area is a valid, empty answer

    # ...so trim to a true circle and sort nearest-first.
    for bar in bars:
        bar["distance_m"] = round(haversine_m(lat, lon, bar["lat"], bar["lon"]))
    bars = sorted((b for b in bars if b["distance_m"] <= radius), key=lambda b: b["distance_m"])

    result = {
        "center": {"lat": lat, "lon": lon},
        "radius_m": radius,
        "count": len(bars),
        "bars": bars,
    }
    _nearby_cache[key] = result
    return result
