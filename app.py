import streamlit as st
import datetime
from pystac_client import Client
from shapely.geometry import Point
import folium
from streamlit_folium import st_folium

# --------------------------------------------------
# Page config
# --------------------------------------------------
st.set_page_config(
    page_title="Satellite Imagery Search",
    layout="centered"
)

st.title("Sentinel-2 Satellite Imagery Finder")
st.markdown(
    "Satellite images appear below once the selected location and dates "
    "match available Sentinel-2 acquisitions."
)

# --------------------------------------------------
# Initialise session state FIRST (critical)
# --------------------------------------------------
if "lat" not in st.session_state:
    st.session_state.lat = 37.8199
    st.session_state.lon = -122.4783

# --------------------------------------------------
# Map selector
# --------------------------------------------------
st.subheader("Select location on map (zoom + click)")

map_center = [st.session_state.lat, st.session_state.lon]

m = folium.Map(
    location=map_center,
    zoom_start=12,
    tiles="OpenStreetMap"
)

folium.Marker(
    map_center,
    tooltip="Selected location"
).add_to(m)

map_data = st_folium(
    m,
    height=450,
    width=700
)

# Update session state on map click
if map_data and map_data.get("last_clicked"):
    st.session_state.lat = map_data["last_clicked"]["lat"]
    st.session_state.lon = map_data["last_clicked"]["lng"]

    st.success(
        f"Selected coordinates: "
        f"{st.session_state.lat:.6f}, {st.session_state.lon:.6f}"
    )

# --------------------------------------------------
# Coordinate inputs (synced with map)
# --------------------------------------------------
st.subheader("Fine-tune coordinates")

lat = st.number_input(
    "Latitude",
    value=st.session_state.lat,
    format="%.6f",
    key="lat_input"
)

lon = st.number_input(
    "Longitude",
    value=st.session_state.lon,
    format="%.6f",
    key="lon_input"
)

# Keep session state in sync with manual edits
st.session_state.lat = lat
st.session_state.lon = lon

# --------------------------------------------------
# Satellite search function
# --------------------------------------------------
def search_satellite_imagery(lat, lon, start_date, end_date, location_name):
    st.subheader(f"Searching imagery for {location_name}")

    st.write(f"Coordinates: {lat}, {lon}")
    st.write(f"Date range: {start_date} to {end_date}")

    api_url = "https://earth-search.aws.element84.com/v1"
    client = Client.open(api_url)

    point = Point(lon, lat)

    search = client.search(
        collections=["sentinel-2-l2a"],
        intersects=point.__geo_interface__,
        datetime=f"{start_date}/{end_date}",
        query={"eo:cloud_cover": {"lt": 15}}
    )

    items = list(search.get_items())
    st.write(f"Found {len(items)} matching scenes")

    if not items:
        st.warning("No images found for the selected parameters.")
        return None

    best_item = sorted(
        items,
        key=lambda x: x.properties.get("eo:cloud_cover", 100)
    )[0]

    st.success("Best available image")
    st.write(f"Scene ID: {best_item.id}")
    st.write(f"Acquisition time: {best_item.datetime}")
    st.write(f"Cloud cover: {best_item.properties['eo:cloud_cover']:.2f}%")

    if "thumbnail" in best_item.assets:
        st.image(
            best_item.assets["thumbnail"].href,
            caption="Sentinel-2 thumbnail"
        )

    return best_item

# --------------------------------------------------
# Search form
# --------------------------------------------------
st.subheader("Search parameters")

with st.form("search_form"):
    location_name = st.text_input(
        "Location name",
        value="Input location name"
    )

    start_date = st.date_input(
        "Start date",
        value=datetime.date(2025, 12, 1)
    )

    end_date = st.date_input(
        "End date",
        value=datetime.date(2025, 12, 31)
    )

    submitted = st.form_submit_button("Search imagery")

if submitted:
    search_satellite_imagery(
        st.session_state.lat,
        st.session_state.lon,
        start_date.isoformat(),
        end_date.isoformat(),
        location_name
    )
