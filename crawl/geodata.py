import osmnx
import pandas
import geopandas


# 1. Enable console logging to see cache hits vs. Overpass HTTP requests
osmnx.settings.log_console = True

# 2. Explicitly enable caching and set an absolute directory path
# OSMnx caches raw Overpass/Nominatim responses on disk by default.
osmnx.settings.use_cache = True
osmnx.settings.cache_folder = "cache"
# osmnx.settings.overpass_rate_limit = False     # DANGER
# osmnx.settings.cache_folder = Path("/absolute/path/to/your/cache").resolve()


# Search settings
AMENITY_TAGS = {
    "amenity": [
        "bar",
        "biergarten",
        "brewery",
        "pub",
        "restaurant"
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
    if value is None or (not isinstance(value, str) and pandas.isna(value)):
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
    gdf["latitude"], gdf["longitude"] = points.y, points.x

    bars = []
    for (element, osm_id), row in gdf.iterrows():
        bar = {
            "id": f"{element}/{osm_id}", 
            "latitude": row["latitude"], 
            "longitude": row["longitude"]
        }
        for column, field in DETAIL_FIELDS.items():
            bar[field] = clean(row.get(column))
        bar["name"] = bar["name"] or "Unnamed " + (bar["type"] or "bar")
        bars.append(bar)
    return bars


def downloadPubsWithinCity(city: str) -> dict:
    gdf = osmnx.features.features_from_place(city, tags=AMENITY_TAGS)
    bars = gdf_to_bars(gdf)
    return bars


def downloadPubsNearby(lat: float, lon: float, radius: float) -> dict:
    try:
        # OSMnx queries a square bounding box around the point...
        gdf = osmnx.features.features_from_point((lat, lon), tags=AMENITY_TAGS, dist=radius)
        bars = gdf_to_bars(gdf)
        return bars
    except Exception as exc:
        if "no matching features" not in str(exc).lower():
            raise
        return []  # nothing mapped in this area is a valid, empty answer


def downloadPubsWithinArea(geojson) -> dict:
    if isinstance(geojson, str):
        geojson_str = geojson
    else:
        geojson_str = json.dumps(geojson)

    # 1. Load the GeoJSON file and ensure it uses WGS84 (EPSG:4326)
    boundary_gdf = geopandas.read_file(geojson_str).to_crs("EPSG:4326")

    # 2. Extract the Shapely Polygon/MultiPolygon
    # Use .union_all() (or .unary_union in older GeoPandas) if the GeoJSON has multiple features
    area = boundary_gdf.geometry.union_all()

    # 3. Download OSM features (e.g., all buildings and parks) inside the polygon
    gdf = osmnx.features_from_polygon(area, tags=AMENITY_TAGS)

    # Format results
    bars = gdf_to_bars(gdf)
    return bars

