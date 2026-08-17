import os

import requests
import streamlit as st
from dotenv import load_dotenv


# ==================================================
# LOAD LOCAL .ENV
# ==================================================

load_dotenv()


# ==================================================
# API KEY
# ==================================================
# Streamlit Cloud:
#     st.secrets["ORS_API_KEY"]
#
# Local VS Code:
#     .env -> ORS_API_KEY
#
# Streamlit Secrets takes priority.
# ==================================================

API_KEY = st.secrets.get(
    "ORS_API_KEY",
    os.getenv("ORS_API_KEY")
)


# ==================================================
# OPENROUTESERVICE URL
# ==================================================

URL = (
    "https://api.heigit.org/"
    "openrouteservice/v2/directions/"
    "driving-car/geojson"
)


# ==================================================
# GET ROUTES
# ==================================================

def get_routes(
    start_lon,
    start_lat,
    end_lon,
    end_lat
):

    if not API_KEY:

        raise Exception(
            "ORS_API_KEY was not found. "
            "Please add ORS_API_KEY to Streamlit Secrets "
            "or your local .env file."
        )


    coordinates = [
        [
            start_lon,
            start_lat
        ],
        [
            end_lon,
            end_lat
        ]
    ]


    body = {
        "coordinates": coordinates,

        "alternative_routes": {
            "target_count": 3,
            "share_factor": 0.6,
            "weight_factor": 1.4
        }
    }


    response = requests.post(
        URL,
        json=body,
        headers={
            "Authorization": API_KEY,
            "Content-Type": "application/json"
        },
        timeout=30
    )


    response.raise_for_status()


    return response.json()
