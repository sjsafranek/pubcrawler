"""Bar Finder: look up bars and pubs in any city, or around a point, using OpenStreetMap data (via OSMnx)."""
import logging
from logging.config import dictConfig

from flask import Flask, jsonify, render_template, request

from bars import fetch_bars
from bars import fetch_bars_nearby

app = Flask(__name__, template_folder='templates', static_url_path='/static')
logging.basicConfig(level=logging.DEBUG)


DEFAULT_RADIUS_M = 1000
MAX_RADIUS_M = 10_000


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/bars")
def api_bars():
    city = request.args.get("city", "").strip()
    if not city:
        return jsonify(error="Enter a city, for example “Portland, Oregon”."), 400

    try:
        return jsonify(fetch_bars(city))
    except Exception as exc:  # OSMnx raises several error types (geocoding, no data, timeouts)
        app.logger.exception("Lookup failed for %r", city)
        message = str(exc)
        if "geocode" in message.lower() or "nominatim" in message.lower():
            message = f"Couldn’t find a place called “{city}”. Try adding the state or country."
        elif "no matching features" in message.lower():
            message = f"No bars or pubs are mapped in “{city}”."
        return jsonify(error=message), 502


@app.get("/api/bars/nearby")
def api_bars_nearby():
    """Bars and pubs within `radius` meters of a point.

    Query params: lat, lon (required), radius in meters (optional, default 1000, max 10000).
    Example: /api/bars/nearby?lat=45.5231&lon=-122.6765&radius=800
    """
    try:
        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
        radius = float(request.args.get("radius", DEFAULT_RADIUS_M))
    except KeyError as missing:
        return jsonify(error=f"Missing required parameter: {missing.args[0]}."), 400
    except ValueError:
        return jsonify(error="lat, lon and radius must be numbers."), 400

    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return jsonify(error="lat must be between -90 and 90, and lon between -180 and 180."), 400
    if not (0 < radius <= MAX_RADIUS_M):
        return jsonify(error=f"radius must be greater than 0 and at most {MAX_RADIUS_M} meters."), 400

    app.logger.debug(f'fetch_bars_nearby lat={lat} lon={lon} radius={radius}')
    try:
        return jsonify(fetch_bars_nearby(lat, lon, radius))
    except Exception as exc:
        app.logger.exception("Nearby lookup failed for (%s, %s, %s)", lat, lon, radius)
        return jsonify(error=str(exc)), 502


if __name__ == "__main__":
    app.run(debug=True)

