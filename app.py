import streamlit as st
import folium
from streamlit_folium import st_folium

from routing import get_routes
from route_analysis import analyze_route


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="SafeRoute AI",
    page_icon="🛡️",
    layout="wide"
)


# ==================================================
# BABY-PINK THEME + BLACK TEXT
# ==================================================

st.markdown(
    """
    <style>

    /* ==============================================
       MAIN BACKGROUND
       ============================================== */

    .stApp {
        background: #fff0f6;
    }


    /* ==============================================
       CONTENT WIDTH / SPACING
       ============================================== */

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }


    /* ==============================================
       ALL MAIN TEXT
       ============================================== */

    body,
    p,
    label,
    span,
    div {
        color: #000000;
    }


    /* ==============================================
       HEADINGS
       ============================================== */

    h1,
    h2,
    h3,
    h4,
    h5,
    h6 {
        color: #000000 !important;
        font-weight: 800 !important;
    }


    /* ==============================================
       MAIN TITLE
       ============================================== */

    h1 {
        font-size: 3rem !important;
        text-align: center;
        margin-bottom: 0.3rem;
    }


    /* ==============================================
       BUTTON
       ============================================== */

    .stButton > button {
        width: 100%;
        border-radius: 14px;
        border: none;
        padding: 0.8rem 1rem;
        font-size: 1.05rem;
        font-weight: 700;
        background: #d85c91;
        color: #ffffff !important;
        transition: 0.2s;
    }


    .stButton > button:hover {
        background: #b94173;
        color: #ffffff !important;
    }


    /* ==============================================
       METRIC CARDS
       ============================================== */

    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.92);
        padding: 1rem;
        border-radius: 14px;
        border: 1px solid #f3c4d7;
        box-shadow: 0 4px 12px rgba(130, 60, 90, 0.08);
    }


    [data-testid="stMetricLabel"] {
        color: #000000 !important;
    }


    [data-testid="stMetricValue"] {
        color: #000000 !important;
    }


    [data-testid="stMetricDelta"] {
        color: #000000 !important;
    }


    /* ==============================================
       INPUT LABELS
       ============================================== */

    .stNumberInput label {
        color: #000000 !important;
        font-weight: 600;
    }


    /* ==============================================
       INPUT BOXES
       ============================================== */

    input {
        border-radius: 10px !important;
        color: #000000 !important;
        background: #ffffff !important;
    }


    /* ==============================================
       INPUT VALUE
       ============================================== */

    input[type="number"] {
        color: #000000 !important;
    }


    /* ==============================================
       ALERTS
       ============================================== */

    [data-testid="stAlert"] {
        border-radius: 12px;
    }


    /* ==============================================
       DIVIDERS
       ============================================== */

    hr {
        margin-top: 1.5rem;
        margin-bottom: 1.5rem;
    }


    /* ==============================================
       CAPTIONS
       ============================================== */

    .stCaption {
        color: #000000 !important;
    }


    /* ==============================================
       MARKDOWN TEXT
       ============================================== */

    [data-testid="stMarkdownContainer"] {
        color: #000000 !important;
    }


    </style>
    """,
    unsafe_allow_html=True
)


# ==================================================
# SESSION STATE
# ==================================================

if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None


# ==================================================
# HEADER
# ==================================================

st.title("🛡️ SafeRoute AI")

st.subheader(
    "Smart Route Recommendation for Safer Journeys"
)

st.write(
    "Compare alternative routes using crime risk, "
    "police proximity, hospital proximity, distance, "
    "and travel time."
)


# ==================================================
# JOURNEY DETAILS
# ==================================================

st.subheader("📍 Journey Details")

col1, col2 = st.columns(2)


# ==================================================
# STARTING POINT
# ==================================================

with col1:

    st.markdown("### Starting Point")

    start_lat = st.number_input(
        "Start Latitude",
        value=12.9784,
        format="%.6f"
    )

    start_lon = st.number_input(
        "Start Longitude",
        value=77.5696,
        format="%.6f"
    )


# ==================================================
# DESTINATION
# ==================================================

with col2:

    st.markdown("### Destination")

    end_lat = st.number_input(
        "Destination Latitude",
        value=12.9756,
        format="%.6f"
    )

    end_lon = st.number_input(
        "Destination Longitude",
        value=77.6069,
        format="%.6f"
    )


# ==================================================
# FIND SAFEST ROUTE
# ==================================================

if st.button(
    "🛡️ FIND SAFEST ROUTE",
    use_container_width=True
):

    try:

        st.info(
            "Generating and analyzing available routes..."
        )


        # ----------------------------------------------
        # GET ROUTES
        # ----------------------------------------------

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
                "No routes were returned by the routing service."
            )

            st.session_state.analysis_results = None

            st.stop()


        results = []


        # ==================================================
        # ANALYZE EACH ROUTE
        # ==================================================

        for index, route in enumerate(routes):

            summary = route[
                "properties"
            ][
                "summary"
            ]


            # ------------------------------------------
            # DISTANCE
            # ------------------------------------------

            distance = (
                summary["distance"] / 1000
            )


            # ------------------------------------------
            # TRAVEL TIME
            # ------------------------------------------

            duration = (
                summary["duration"] / 60
            )


            # ------------------------------------------
            # SAFETY ANALYSIS
            # ------------------------------------------

            safety = analyze_route(
                route
            )


            # ==================================================
            # DISTANCE SCORE
            # ==================================================

            distance_score = max(
                0,
                min(
                    100,
                    100 - distance * 3
                )
            )


            # ==================================================
            # TIME SCORE
            # ==================================================

            time_score = max(
                0,
                min(
                    100,
                    100 - duration * 2
                )
            )


            # ==================================================
            # FINAL ROUTE SCORE
            # ==================================================

            final_score = (
                safety["safety_score"] * 0.80
                + time_score * 0.10
                + distance_score * 0.10
            )


            # ==================================================
            # STORE RESULTS
            # ==================================================

            results.append(
                {
                    "route_number": index + 1,

                    "route": route,

                    "distance": round(
                        distance,
                        2
                    ),

                    "duration": round(
                        duration,
                        2
                    ),

                    "safety_score": round(
                        safety["safety_score"],
                        2
                    ),

                    "crime_safety_score": round(
                        safety["crime_safety_score"],
                        2
                    ),

                    "police_score": round(
                        safety["police_score"],
                        2
                    ),

                    "hospital_score": round(
                        safety["hospital_score"],
                        2
                    ),

                    "average_police_distance": round(
                        safety["average_police_distance"],
                        3
                    ),

                    "average_hospital_distance": round(
                        safety["average_hospital_distance"],
                        3
                    ),

                    "worst_police_distance": round(
                        safety["worst_police_distance"],
                        3
                    ),

                    "worst_hospital_distance": round(
                        safety["worst_hospital_distance"],
                        3
                    ),

                    "risk": safety["risk"],

                    "crime_risk": safety.get(
                        "crime_risk",
                        None
                    ),

                    "final_score": round(
                        final_score,
                        2
                    ),

                    "points_analyzed": safety.get(
                        "points_analyzed",
                        0
                    )
                }
            )


        # ==================================================
        # RANK ROUTES
        # ==================================================

        results.sort(
            key=lambda x: x["final_score"],
            reverse=True
        )


        # ==================================================
        # SAVE RESULTS
        # ==================================================

        st.session_state.analysis_results = results


        st.success(
            f"✅ {len(results)} route(s) analyzed successfully."
        )


    except Exception as error:

        st.session_state.analysis_results = None

        st.error(
            "❌ Route analysis failed."
        )

        st.code(
            str(error)
        )


# ==================================================
# DISPLAY RESULTS
# ==================================================

if st.session_state.analysis_results:

    results = st.session_state.analysis_results

    recommended = results[0]


    # ==================================================
    # RECOMMENDED ROUTE
    # ==================================================

    st.subheader(
        "⭐ Safest Recommended Route"
    )


    st.success(
        f"Route {recommended['route_number']} "
        f"has the best overall safety score among "
        f"the available routes."
    )


    # ==================================================
    # PRIMARY METRICS
    # ==================================================

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


    # ==================================================
    # SAFETY ANALYSIS
    # ==================================================

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


    # ==================================================
    # INTERACTIVE MAP
    # ==================================================

    st.subheader(
        "🗺️ Interactive Route Map"
    )


    first_route = results[0]["route"]


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


    # ==================================================
    # DRAW ROUTES
    # ==================================================

    for index, item in enumerate(results):

        coordinates = (
            item["route"]
            ["geometry"]
            ["coordinates"]
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


        # ----------------------------------------------
        # RECOMMENDED ROUTE
        # ----------------------------------------------

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


        # ----------------------------------------------
        # POPUP
        # ----------------------------------------------

        popup = (
            f"<b>Route {item['route_number']}</b><br>"
            f"Safety Score: "
            f"{item['safety_score']}/100<br>"
            f"Crime Safety: "
            f"{item['crime_safety_score']}/100<br>"
            f"Risk: "
            f"{item['risk']}<br>"
            f"Average Police Distance: "
            f"{item['average_police_distance']} km<br>"
            f"Average Hospital Distance: "
            f"{item['average_hospital_distance']} km<br>"
            f"Distance: "
            f"{item['distance']} km<br>"
            f"Travel Time: "
            f"{item['duration']} min<br>"
            f"Final Score: "
            f"{item['final_score']}/100"
        )


        # ----------------------------------------------
        # DRAW ROUTE
        # ----------------------------------------------

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


    # ==================================================
    # START MARKER
    # ==================================================

    folium.Marker(
        [
            start_lat,
            start_lon
        ],
        tooltip="START",
        popup="Starting Point",
        icon=folium.Icon(
            color="green"
        )
    ).add_to(m)


    # ==================================================
    # DESTINATION MARKER
    # ==================================================

    folium.Marker(
        [
            end_lat,
            end_lon
        ],
        tooltip="DESTINATION",
        popup="Destination",
        icon=folium.Icon(
            color="red"
        )
    ).add_to(m)


    # ==================================================
    # MAP BOUNDS
    # ==================================================

    if all_points:

        m.fit_bounds(
            all_points
        )


    # ==================================================
    # DISPLAY MAP
    # ==================================================

    st_folium(
        m,
        width=1200,
        height=600,
        returned_objects=[]
    )


    # ==================================================
    # ROUTE COMPARISON
    # ==================================================

    st.subheader(
        "📊 Route Comparison"
    )


    for index, item in enumerate(results):

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
            f"Final Score: "
            f"{item['final_score']}/100 | "
            f"Police Score: "
            f"{item['police_score']}/100 | "
            f"Hospital Score: "
            f"{item['hospital_score']}/100 | "
            f"{item['points_analyzed']} route points analyzed"
        )


        st.divider()


# ==================================================
# DISCLAIMER
# ==================================================

st.caption(
    "Safety scores are comparative estimates and do not "
    "guarantee personal safety. The current system uses "
    "aggregate crime information together with geographic "
    "police and hospital proximity."
)