import json


def getGeoJSONFromGeoDataFrame(gdf):
    geojson_str = gdf.to_json(to_wgs84=True, na="drop")
    return json.loads(geojson_str)

