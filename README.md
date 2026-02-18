## Project Overview

This is a Streamlit web application that allows users to search for and preview **Sentinel-2 satellite imagery** via an interactive map interface. Users can click a location on a Folium map, set a date range, and retrieve the lowest-cloud-cover Sentinel-2 scene for that location using the AWS Element84 STAC API.

## Repository Structure

```
geospatialexercise/
├── app.py            # Entire application – single-file Streamlit app
├── requirements.txt  # Python dependencies (no pinned versions)
└── README.md         # Minimal project description
```

There is no package directory, build system, test suite, or configuration files beyond the above.

## Dependencies

| Package | Role |
|---|---|
| `streamlit` | Web UI framework – renders all widgets, state, and layout |
| `folium` | Leaflet.js-based interactive map |
| `streamlit-folium` | Embeds Folium maps inside Streamlit via `st_folium` |
| `pystac-client` | Python client for STAC APIs; used to query the Element84 catalog |
| `shapely` | Converts lat/lon coordinates to GeoJSON geometry (`Point`) |
| `requests` | Listed as a dependency; used transitively by pystac-client |

## Running the Application

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app will open in a browser at `http://localhost:8501` by default.

No environment variables, API keys, or configuration files are required. The STAC API at `https://earth-search.aws.element84.com/v1` is publicly accessible.

## Application Architecture

The app is a single-file Streamlit script executed top-to-bottom on every user interaction. The flow is:

1. **Page config** – Sets title and layout via `st.set_page_config`.
2. **Session state initialization** – `st.session_state.lat` / `st.session_state.lon` default to Golden Gate Bridge coordinates (37.8199, -122.4783) on first load.
3. **Interactive map** – A `folium.Map` is rendered via `st_folium`. Click events update `st.session_state.lat` and `st.session_state.lon`.
4. **Coordinate inputs** – `st.number_input` widgets allow manual fine-tuning; they are kept in sync with session state.
5. **Search form** – A `st.form` collects `location_name`, `start_date`, and `end_date`. Submission triggers `search_satellite_imagery`.
6. **`search_satellite_imagery` function** – Queries the STAC API, selects the scene with the lowest cloud cover, and renders the result (scene ID, acquisition time, cloud cover %, thumbnail image).

## Key Conventions

### Streamlit patterns used
- Session state (`st.session_state`) is initialised with `if "key" not in st.session_state` guards to avoid resetting on reruns.
- The map widget returns interaction data via `st_folium(...)` return value (`map_data["last_clicked"]`).
- All output within `search_satellite_imagery` uses Streamlit display calls (`st.write`, `st.success`, `st.image`, etc.) rather than returning values to be rendered elsewhere.
- A `st.form` wraps the search inputs so the STAC query only fires on explicit form submission, not on every widget change.

### STAC API usage
- API endpoint: `https://earth-search.aws.element84.com/v1`
- Collection searched: `sentinel-2-l2a` (Sentinel-2 Level-2A, atmospherically corrected)
- Cloud cover filter: `{"eo:cloud_cover": {"lt": 15}}` — scenes with ≥15% cloud cover are excluded
- Scene selection: the scene with the lowest `eo:cloud_cover` property is chosen from results
- Geometry: a single `shapely.geometry.Point` converted via `.__geo_interface__` to GeoJSON

### Coordinate convention
- Shapely `Point` takes `(lon, lat)` order (x, y).
- Folium and `st.number_input` widgets use `(lat, lon)` order.
- `map_data["last_clicked"]` returns keys `"lat"` and `"lng"`.

## Development Notes

- **No tests exist.** When adding features, manually test by running the app and exercising the UI.
- **No linter or formatter is configured.** The existing code uses 4-space indentation; maintain that style.
- **Dependencies are unpinned** in `requirements.txt`. If reproducibility matters, pin them with `pip freeze > requirements.txt` after installing.
- **Single-file design**: keep the app in `app.py` unless there is a strong reason to split it. Utility functions can be extracted to a separate module if complexity grows, but the Streamlit entry point must remain `app.py`.
- **Streamlit reruns**: every widget interaction causes a full top-to-bottom re-execution of `app.py`. Expensive operations (e.g., STAC searches) must be placed inside form submit handlers or guarded with `st.cache_data` / `st.cache_resource` to avoid unintended repeated calls.
- **No `.gitignore`**: avoid committing `__pycache__/`, `.venv/`, or similar artifacts.

## Modifying the STAC Search

The search logic lives entirely in `search_satellite_imagery` (`app.py:89–130`). Key parameters to adjust:

- **Cloud cover threshold**: change `{"lt": 15}` in the `query` argument (`app.py:104`).
- **Date range**: passed in as ISO-format strings from the form inputs.
- **Collection**: replace `"sentinel-2-l2a"` with another STAC collection name to search a different dataset.
- **Geometry**: currently a single point; can be replaced with a polygon for area-based searches using `shapely.geometry.Polygon` or a bounding box via the `bbox` parameter instead of `intersects`.
