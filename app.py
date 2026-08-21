import os

import requests
import streamlit as st
import folium

from dotenv import load_dotenv
from streamlit_folium import st_folium
from streamlit_searchbox import st_searchbox
from streamlit_geolocation import streamlit_geolocation


# ============================================================
# LOAD LOCAL .ENV
# ============================================================

load_dotenv()


# ============================================================
# IMPORT PROJECT MODULES
# ============================================================

try:
    from routing import get_routes
    from route_analysis import analyze_route

except ModuleNotFoundError:
    from core.routing import get_routes
    from core.route_analysis import analyze_route


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="SafeRoute AI",
    page_icon="🛡️",
    layout="wide"
)


# ============================================================
# CUSTOM THEME
# ============================================================

st.markdown(
    """
    <style>

    /* =========================================
       BACKGROUND
       ========================================= */

    .stApp {
        background: #fff0f6;
    }


    /* =========================================
       CONTENT
       ========================================= */

    .block-container {
        max-width: 1250px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }


    /* =========================================
       HEADINGS
       ========================================= */

    h1,
    h2,
    h3,
    h4,
    h5,
    h6 {
        color: #000000 !important;
        font-weight: 800 !important;
    }


    h1 {
        font-size: 3rem !important;
        text-align: center;
        margin-bottom: 0.4rem;
    }


    /* =========================================
       NORMAL TEXT
       ========================================= */

    p,
    label {
        color: #000000 !important;
    }


    [data-testid="stMarkdownContainer"] {
        color: #000000 !important;
    }


    /* =========================================
       NORMAL STREAMLIT BUTTONS
       ========================================= */

    .stButton > button {
        width: 100%;
        border-radius: 14px;
        border: none;
        background: #d85c91;
        color: #ffffff !important;
        font-weight: 700;
        padding: 0.8rem 1rem;
        transition: 0.2s;
    }


    .stButton > button:hover {
        background: #b94173;
        color: #ffffff !important;
    }


    /* =========================================
       LINK BUTTONS
       ========================================= */

    .stLinkButton > a {
        width: 100%;
        color: #ffffff !important;
        background: #d85c91 !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        text-decoration: none !important;
        border: none !important;
        padding: 0.8rem 1rem !important;
        transition: 0.2s;
    }


    .stLinkButton > a:hover {
        color: #ffffff !important;
        background: #b94173 !important;
        text-decoration: none !important;
    }


    /* =========================================
       METRIC CARDS
       ========================================= */

    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.94);
        border: 1px solid #f3c4d7;
        border-radius: 14px;
        padding: 1rem;
        box-shadow: 0 4px 12px rgba(130, 60, 90, 0.08);
    }


    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"],
    [data-testid="stMetricDelta"] {
        color: #000000 !important;
    }


    /* =========================================
       INPUTS
       ========================================= */

    input {
        color: #000000 !important;
        background: #ffffff !important;
        border-radius: 10px !important;
    }


    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SESSION STATE
# ============================================================

if "start_location" not in st.session_state:
    st.session_state.start_location = None


if "end_location" not in st.session_state:
    st.session_state.end_location = None


if "current_location" not in st.session_state:
    st.session_state.current_location = None


if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None


# ============================================================
# OPENROUTESERVICE API KEY
# ============================================================

def get_ors_key():

    # Local VS Code -> .env
    local_key = os.getenv("ORS_API_KEY")

    if local_key:
        return local_key.strip()


    # Streamlit Cloud -> Secrets
    try:

        cloud_key = st.secrets["ORS_API_KEY"]

        if cloud_key:
            return str(
                cloud_key
            ).strip()

    except Exception:
        pass


    return None


# ============================================================
# LIVE LOCATION SEARCH
# ============================================================

def search_places(searchterm):

    searchterm = searchterm.strip()


    if len(searchterm) < 2:
        return []


    api_key = get_ors_key()


    if not api_key:
        return []


    url = (
        "https://api.openrouteservice.org/"
        "geocode/search"
    )


    params = {
        "api_key": api_key,
        "text": searchterm,
        "size": 10,
        "boundary.country": "IND",

        # Bias results toward Bengaluru
        "focus.point.lat": 12.9716,
        "focus.point.lon": 77.5946,
    }


    headers = {
        "Accept": "application/json",
        "User-Agent": "SafeRouteAI/1.0"
    }


    try:

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )


        if response.status_code != 200:
            return []


        data = response.json()


    except (
        requests.RequestException,
        ValueError
    ):

        return []


    candidates = []


    for feature in data.get(
        "features",
        []
    ):

        properties = feature.get(
            "properties",
            {}
        )


        geometry = feature.get(
            "geometry",
            {}
        )


        coordinates = geometry.get(
            "coordinates"
        )


        if (
            not coordinates
            or len(coordinates) < 2
        ):
            continue


        label = properties.get(
            "label",
            ""
        )


        if not label:
            continue


        country = str(
            properties.get(
                "country",
                ""
            )
        ).lower()


        region = str(
            properties.get(
                "region",
                ""
            )
        ).lower()


        locality = str(
            properties.get(
                "locality",
                ""
            )
        ).lower()


        county = str(
            properties.get(
                "county",
                ""
            )
        ).lower()


        layer = str(
            properties.get(
                "layer",
                ""
            )
        ).lower()


        postcode = str(
            properties.get(
                "postalcode",
                ""
            )
        ).strip()


        # ============================================
        # INDIA ONLY
        # ============================================

        if country and country != "india":
            continue


        # ============================================
        # RANK BENGALURU RESULTS
        # ============================================

        score = 0


        if region == "karnataka":
            score += 50


        if "bangalore" in locality:
            score += 60


        if "bengaluru" in locality:
            score += 60


        if "bangalore" in county:
            score += 30


        if "bengaluru" in county:
            score += 30


        lower_label = label.lower()


        if "bangalore" in lower_label:
            score += 20


        if "bengaluru" in lower_label:
            score += 20


        if layer == "neighbourhood":
            score += 15


        elif layer == "locality":
            score += 12


        elif layer == "borough":
            score += 10


        elif layer == "street":
            score += 8


        elif layer == "venue":
            score += 5


        try:

            latitude = float(
                coordinates[1]
            )

            longitude = float(
                coordinates[0]
            )

        except (
            TypeError,
            ValueError
        ):

            continue


        candidates.append(
            {
                "score": score,
                "label": label,
                "postcode": postcode,
                "latitude": latitude,
                "longitude": longitude,
            }
        )


    # ================================================
    # SORT BEST RESULTS FIRST
    # ================================================

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True
    )


    suggestions = []


    seen = set()


    for item in candidates:

        unique_key = (
            item["label"],
            round(item["latitude"], 6),
            round(item["longitude"], 6)
        )


        if unique_key in seen:
            continue


        seen.add(unique_key)


        if item["postcode"]:

            display_text = (
                f"{item['label']} "
                f"• PIN {item['postcode']}"
            )

        else:

            display_text = item["label"]


        location_data = {
            "label": item["label"],
            "postcode": item["postcode"],
            "latitude": item["latitude"],
            "longitude": item["longitude"],
        }


        suggestions.append(
            (
                display_text,
                location_data
            )
        )


        if len(suggestions) >= 6:
            break


    return suggestions


# ============================================================
# HEADER
# ============================================================

st.title(
    "🛡️ SafeRoute AI"
)


st.subheader(
    "Smart Route Recommendation for Safer Journeys"
)


st.write(
    "Search for your starting point and destination. "
    "You can also use your current location as the source."
)


# ============================================================
# JOURNEY DETAILS
# ============================================================

st.subheader(
    "📍 Journey Details"
)


source_col, destination_col = st.columns(2)


# ============================================================
# SOURCE / STARTING POINT
# ============================================================

with source_col:

    st.markdown(
        "### Starting Point"
    )


    start_location = st_searchbox(
        search_places,
        placeholder="Start typing a place or area...",
        label=None,
        key="start_search",
        debounce=500,
        clear_on_submit=False,
        edit_after_submit="option",
    )


    if start_location is not None:

        st.session_state.start_location = (
            start_location
        )


    if st.session_state.start_location:

        st.success(
            f"Source: "
            f"{st.session_state.start_location['label']}"
        )


        if st.session_state.start_location.get(
            "postcode"
        ):

            st.caption(
                "PIN Code: "
                + st.session_state.start_location[
                    "postcode"
                ]
            )


    # ========================================================
    # CURRENT LOCATION
    # ========================================================

    st.markdown(
        "### 📍 Use My Current Location"
    )


    st.caption(
        "Allow your browser to access your location "
        "to use it as the starting point."
    )


    # IMPORTANT:
    # streamlit-geolocation 0.0.10 does NOT accept key=.
    current_location_data = (
        streamlit_geolocation()
    )


    if current_location_data:

        latitude = current_location_data.get(
            "latitude"
        )

        longitude = current_location_data.get(
            "longitude"
        )


        if (
            latitude is not None
            and longitude is not None
        ):

            st.session_state.current_location = {
                "latitude": float(latitude),
                "longitude": float(longitude)
            }


            st.success(
                "📍 Current location detected."
            )


            st.caption(
                f"Lat: {latitude:.6f} | "
                f"Lon: {longitude:.6f}"
            )


            if st.button(
                "📍 Use Current Location as Start",
                key="use_current_start",
                use_container_width=True
            ):

                st.session_state.start_location = {
                    "label": "📍 My Current Location",
                    "postcode": "",
                    "latitude": float(latitude),
                    "longitude": float(longitude)
                }


                st.success(
                    "Source: 📍 My Current Location"
                )


# ============================================================
# DESTINATION
# ============================================================

with destination_col:

    st.markdown(
        "### Destination"
    )


    # --------------------------------------------------------
    # KEEP DESTINATION SEARCH UNCHANGED
    # --------------------------------------------------------

    end_location = st_searchbox(
        search_places,
        placeholder="Start typing a destination...",
        label=None,
        key="end_search",
        debounce=500,
        clear_on_submit=False,
        edit_after_submit="option",
    )


    if end_location is not None:

        st.session_state.end_location = (
            end_location
        )


    if st.session_state.end_location:

        st.success(
            "Destination selected."
        )


        st.caption(
            st.session_state.end_location[
                "label"
            ]
        )


        if st.session_state.end_location.get(
            "postcode"
        ):

            st.caption(
                "PIN Code: "
                + st.session_state.end_location[
                    "postcode"
                ]
            )


# ============================================================
# FIND SAFEST ROUTE
# ============================================================

st.divider()


if st.button(
    "🛡️ FIND SAFEST ROUTE",
    use_container_width=True
):

    if not st.session_state.start_location:

        st.error(
            "Please select a starting point "
            "or use your current location."
        )

        st.stop()


    if not st.session_state.end_location:

        st.error(
            "Please select a destination "
            "from the suggestions."
        )

        st.stop()


    try:

        st.info(
            "Generating and analyzing available routes..."
        )


        start = (
            st.session_state.start_location
        )


        end = (
            st.session_state.end_location
        )


        start_lat = start[
            "latitude"
        ]


        start_lon = start[
            "longitude"
        ]


        end_lat = end[
            "latitude"
        ]


        end_lon = end[
            "longitude"
        ]


        # ====================================================
        # GET ROUTES
        # ====================================================

        route_data = get_routes(
            start_lon,
            start_lat,
            end_lon,
            end_lat
        )


        routes = route_data.get(
            "features",
            []
        )


        if not routes:

            st.error(
                "No routes were returned by "
                "the routing service."
            )


            st.session_state.analysis_results = None

            st.stop()


        results = []


        # ====================================================
        # ANALYZE EACH ROUTE
        # ====================================================

        for index, route in enumerate(
            routes
        ):

            summary = (
                route[
                    "properties"
                ][
                    "summary"
                ]
            )


            distance_km = (
                summary[
                    "distance"
                ]
                / 1000
            )


            duration_min = (
                summary[
                    "duration"
                ]
                / 60
            )


            safety = analyze_route(
                route
            )


            # ================================================
            # DISTANCE SCORE
            # ================================================

            distance_score = max(
                0,
                min(
                    100,
                    100
                    - distance_km * 3
                )
            )


            # ================================================
            # TIME SCORE
            # ================================================

            time_score = max(
                0,
                min(
                    100,
                    100
                    - duration_min * 2
                )
            )


            # ================================================
            # FINAL SCORE
            # ================================================

            final_score = (
                safety[
                    "safety_score"
                ]
                * 0.80

                +

                time_score
                * 0.10

                +

                distance_score
                * 0.10
            )


            results.append(
                {
                    "route_number":
                        index + 1,

                    "route":
                        route,

                    "distance":
                        round(
                            distance_km,
                            2
                        ),

                    "duration":
                        round(
                            duration_min,
                            2
                        ),

                    "safety_score":
                        round(
                            safety[
                                "safety_score"
                            ],
                            2
                        ),

                    "crime_safety_score":
                        round(
                            safety[
                                "crime_safety_score"
                            ],
                            2
                        ),

                    "police_score":
                        round(
                            safety[
                                "police_score"
                            ],
                            2
                        ),

                    "hospital_score":
                        round(
                            safety[
                                "hospital_score"
                            ],
                            2
                        ),

                    "average_police_distance":
                        round(
                            safety[
                                "average_police_distance"
                            ],
                            3
                        ),

                    "average_hospital_distance":
                        round(
                            safety[
                                "average_hospital_distance"
                            ],
                            3
                        ),

                    "worst_police_distance":
                        round(
                            safety[
                                "worst_police_distance"
                            ],
                            3
                        ),

                    "worst_hospital_distance":
                        round(
                            safety[
                                "worst_hospital_distance"
                            ],
                            3
                        ),

                    "risk":
                        safety[
                            "risk"
                        ],

                    "crime_risk":
                        safety.get(
                            "crime_risk"
                        ),

                    "final_score":
                        round(
                            final_score,
                            2
                        ),

                    "points_analyzed":
                        safety.get(
                            "points_analyzed",
                            0
                        )
                }
            )


        # ====================================================
        # RANK ROUTES
        # ====================================================

        results.sort(
            key=lambda item:
                item[
                    "final_score"
                ],
            reverse=True
        )


        st.session_state.analysis_results = (
            results
        )


        st.success(
            f"✅ {len(results)} route(s) "
            f"analyzed successfully."
        )


    except Exception as error:

        st.session_state.analysis_results = None


        st.error(
            "❌ Route analysis failed."
        )


        st.code(
            str(error)
        )


# ============================================================
# RESULTS
# ============================================================

if st.session_state.analysis_results:

    results = (
        st.session_state.analysis_results
    )


    recommended = results[0]


    # ========================================================
    # RECOMMENDED ROUTE
    # ========================================================

    st.subheader(
        "⭐ Safest Recommended Route"
    )


    st.success(
        f"Route {recommended['route_number']} "
        f"has the highest comparative safety score."
    )


    c1, c2, c3, c4 = st.columns(4)


    with c1:

        st.metric(
            "Safety Score",
            f"{recommended['safety_score']}/100"
        )


    with c2:

        st.metric(
            "Risk Level",
            recommended["risk"]
        )


    with c3:

        st.metric(
            "Distance",
            f"{recommended['distance']} km"
        )


    with c4:

        st.metric(
            "Travel Time",
            f"{recommended['duration']} min"
        )


    # ========================================================
    # SAFETY ANALYSIS
    # ========================================================

    st.subheader(
        "🛡️ Safety Analysis"
    )


    s1, s2, s3, s4 = st.columns(4)


    with s1:

        st.metric(
            "Crime Safety",
            f"{recommended['crime_safety_score']}/100"
        )


    with s2:

        st.metric(
            "Police Proximity",
            f"{recommended['average_police_distance']} km"
        )


    with s3:

        st.metric(
            "Hospital Proximity",
            f"{recommended['average_hospital_distance']} km"
        )


    with s4:

        st.metric(
            "Final Score",
            f"{recommended['final_score']}/100"
        )


    # ========================================================
    # MAP
    # ========================================================

    st.subheader(
        "🗺️ Interactive Route Map"
    )


    first_route = results[0][
        "route"
    ]


    first_coordinates = (
        first_route[
            "geometry"
        ][
            "coordinates"
        ]
    )


    first_point = [
        first_coordinates[0][1],
        first_coordinates[0][0]
    ]


    m = folium.Map(
        location=first_point,
        zoom_start=14,
        tiles="OpenStreetMap",
        control_scale=True
    )


    all_points = []


    for index, item in enumerate(
        results
    ):


        coordinates = (
            item[
                "route"
            ][
                "geometry"
            ][
                "coordinates"
            ]
        )


        points = [
            [
                point[1],
                point[0]
            ]
            for point in coordinates
        ]


        all_points.extend(
            points
        )


        if index == 0:

            route_color = "green"
            route_weight = 8
            route_opacity = 0.95


        else:

            if item["risk"] == "High":

                route_color = "red"

            elif item["risk"] == "Medium":

                route_color = "orange"

            else:

                route_color = "blue"


            route_weight = 5
            route_opacity = 0.55


        popup = (
            f"<b>Route {item['route_number']}</b><br>"
            f"Safety: {item['safety_score']}/100<br>"
            f"Crime: {item['crime_safety_score']}/100<br>"
            f"Risk: {item['risk']}<br>"
            f"Police: {item['average_police_distance']} km<br>"
            f"Hospital: {item['average_hospital_distance']} km<br>"
            f"Distance: {item['distance']} km<br>"
            f"Time: {item['duration']} min<br>"
            f"Final Score: {item['final_score']}/100"
        )


        folium.PolyLine(
            points,
            color=route_color,
            weight=route_weight,
            opacity=route_opacity,
            popup=popup,
            tooltip=(
                f"Route {item['route_number']} "
                f"• Score {item['final_score']}"
            )
        ).add_to(m)


    # ========================================================
    # START MARKER
    # ========================================================

    folium.Marker(

        [
            start_lat,
            start_lon
        ],

        tooltip="START",

        popup=(
            "Starting Point<br>"
            + start["label"]
        ),

        icon=folium.Icon(
            color="green",
            icon="play"
        )
    ).add_to(m)


    # ========================================================
    # DESTINATION MARKER
    # ========================================================

    folium.Marker(

        [
            end_lat,
            end_lon
        ],

        tooltip="DESTINATION",

        popup=(
            "Destination<br>"
            + end["label"]
        ),

        icon=folium.Icon(
            color="red",
            icon="flag"
        )
    ).add_to(m)


    if all_points:

        m.fit_bounds(
            all_points
        )


    st_folium(
        m,
        width=1200,
        height=600,
        returned_objects=[]
    )


    # ========================================================
    # ROUTE COMPARISON
    # ========================================================

    st.subheader(
        "📊 Route Comparison"
    )


    for index, item in enumerate(
        results
    ):


        if index == 0:

            st.markdown(
                f"### ⭐ Route {item['route_number']} — Recommended"
            )

        else:

            st.markdown(
                f"### Route {item['route_number']}"
            )


        r1, r2, r3, r4, r5, r6 = (
            st.columns(6)
        )


        with r1:

            st.metric(
                "Safety",
                f"{item['safety_score']}/100"
            )


        with r2:

            st.metric(
                "Crime",
                f"{item['crime_safety_score']}/100"
            )


        with r3:

            st.metric(
                "Police",
                f"{item['average_police_distance']} km"
            )


        with r4:

            st.metric(
                "Hospital",
                f"{item['average_hospital_distance']} km"
            )


        with r5:

            st.metric(
                "Distance",
                f"{item['distance']} km"
            )


        with r6:

            st.metric(
                "Time",
                f"{item['duration']} min"
            )


        st.caption(
            f"Final Score: {item['final_score']}/100 | "
            f"Police Score: {item['police_score']}/100 | "
            f"Hospital Score: {item['hospital_score']}/100 | "
            f"{item['points_analyzed']} route points analyzed"
        )


        st.divider()


# ============================================================
# EMERGENCY SUPPORT
# ============================================================

st.subheader(
    "🚨 Emergency Support"
)


st.caption(
    "Quick access to police, nearby hospitals, "
    "and your optional emergency contact."
)


em1, em2, em3 = st.columns(3)


# ============================================================
# POLICE
# ============================================================

with em1:

    st.markdown(
        "### 👮 Police"
    )


    st.write(
        "Police assistance"
    )


    st.link_button(
        "📞 CALL POLICE — 100",
        "tel:100",
        use_container_width=True
    )


# ============================================================
# HOSPITAL
# ============================================================

with em2:

    st.markdown(
        "### 🏥 Hospital"
    )


    st.write(
        "Find hospitals near your location"
    )


    hospital_search_url = (
        "https://www.google.com/maps/search/"
        "?api=1&query=hospitals+near+me"
    )


    st.link_button(
        "🏥 FIND NEARBY HOSPITAL",
        hospital_search_url,
        use_container_width=True
    )


# ============================================================
# OPTIONAL EMERGENCY CONTACT
# ============================================================

with em3:

    st.markdown(
        "### 🚨 My Emergency Contact"
    )


    emergency_number = st.text_input(
        "Emergency contact number",
        placeholder="Enter number",
        key="emergency_contact"
    )


    if emergency_number.strip():

        st.link_button(
            "📞 CALL EMERGENCY CONTACT",
            f"tel:{emergency_number.strip()}",
            use_container_width=True
        )


# ============================================================
# SHARE CURRENT LOCATION
# ============================================================

st.subheader(
    "📤 Share Current Location"
)


if st.session_state.current_location:

    current_lat = (
        st.session_state.current_location[
            "latitude"
        ]
    )


    current_lon = (
        st.session_state.current_location[
            "longitude"
        ]
    )


    maps_link = (
        "https://www.google.com/maps/search/"
        "?api=1"
        f"&query={current_lat},{current_lon}"
    )


    st.text_input(
        "Location Link",
        value=maps_link,
        key="location_link"
    )


    st.link_button(
        "📍 OPEN CURRENT LOCATION",
        maps_link,
        use_container_width=True
    )


    st.caption(
        "This creates a shareable snapshot of your current "
        "location. It does not continuously track movement."
    )


else:

    st.info(
        "Detect your current location above to create "
        "a location-sharing link."
    )


# ============================================================
# DISCLAIMER
# ============================================================

st.caption(
    "Safety scores are comparative estimates and do not "
    "guarantee personal safety. Crime information is currently "
    "based on aggregate data; police and hospital proximity "
    "are calculated geographically."
)
