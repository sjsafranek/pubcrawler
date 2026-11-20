from math import asin
from math import cos
from math import radians
from math import sin
from math import sqrt


def haversine(lat1, lon1, lat2, lon2) -> float:
    """Great-circle distance in meters between two lat/lon points."""
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * 6_371_000 * asin(sqrt(a))

