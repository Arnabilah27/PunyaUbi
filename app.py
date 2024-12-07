from flask import Flask, render_template, request, redirect, url_for
import folium
from pyproj import Geod
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

app = Flask(__name__)

# Initialize the geolocator
geolocator = Nominatim(user_agent="geo_app")

# Function to geocode city names to coordinates
def geocode_location(location_name):
    try:
        location = geolocator.geocode(location_name)
        if location:
            return location.latitude, location.longitude
    except GeocoderTimedOut:
        pass
    return None, None

# Function to create a map with optional markers and GCD path
def create_map(lat1=None, lon1=None, lat2=None, lon2=None):
    m = folium.Map(location=[0, 0], zoom_start=2, tiles='OpenStreetMap')
    if lat1 is not None and lon1 is not None and lat2 is not None and lon2 is not None:
        coords1 = (lat1, lon1)
        coords2 = (lat2, lon2)

        # Add markers
        folium.Marker(coords1, popup="Location 1", icon=folium.Icon(color="blue")).add_to(m)
        folium.Marker(coords2, popup="Location 2", icon=folium.Icon(color="red")).add_to(m)

        # Add Great Circle path
        geod = Geod(ellps="WGS84")
        points = geod.npts(lon1, lat1, lon2, lat2, 100)  # 100 intermediate points
        path_points = [(lat1, lon1)] + [(p[1], p[0]) for p in points] + [(lat2, lon2)]
        folium.PolyLine(path_points, color="blue", weight=2.5).add_to(m)

        # Calculate the distance
        _, _, distance = geod.inv(lon1, lat1, lon2, lat2)
        distance /= 1000  # Convert from meters to kilometers

        # Set the map view to fit the bounds of the two points
        southwest = [min(lat1, lat2), min(lon1, lon2)]
        northeast = [max(lat1, lat2), max(lon1, lon2)]
        m.fit_bounds([southwest, northeast])

        return m, distance
    return m, None

@app.route("/", methods=["GET", "POST"])
def index():
    # Initialize input coordinates and distance to None
    city1 = city2 = None
    lat1 = lon1 = lat2 = lon2 = None
    distance = None

    if request.method == "POST":
        # Check if the reset button was clicked
        if 'reset' in request.form:
            return redirect(url_for('index'))  # Redirect to clear the form and map

        # Get city names from the form
        city1 = request.form.get("city1")
        city2 = request.form.get("city2")

        if city1 and city2:
            # Geocode the city names to get coordinates
            lat1, lon1 = geocode_location(city1)
            lat2, lon2 = geocode_location(city2)

            if lat1 and lon1 and lat2 and lon2:
                gcd_map, distance = create_map(lat1, lon1, lat2, lon2)
            else:
                gcd_map = folium.Map(location=[0, 0], zoom_start=2, tiles='OpenStreetMap')
        else:
            gcd_map = folium.Map(location=[0, 0], zoom_start=2, tiles='OpenStreetMap')

    else:
        # Reset input values on GET request
        gcd_map, _ = create_map()

    map_html = gcd_map._repr_html_() if gcd_map else ""

    return render_template(
        "index.html", 
        map_html=map_html,
        city1=city1, city2=city2,
        lat1=lat1, lon1=lon1,
        lat2=lat2, lon2=lon2,
        distance=distance
    )

if __name__ == "__main__":
    app.run(debug=True)