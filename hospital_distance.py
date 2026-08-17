import math
import pandas as pd


HOSPITAL_FILE = "hospital_locations.csv"


def haversine(
    lat1,
    lon1,
    lat2,
    lon2
):
    earth_radius = 6371.0

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    dlat = math.radians(
        lat2 - lat1
    )

    dlon = math.radians(
        lon2 - lon1
    )

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return (
        2
        * earth_radius
        * math.asin(
            math.sqrt(a)
        )
    )


def load_hospitals():

    df = pd.read_csv(
        HOSPITAL_FILE
    )

    required = [
        "latitude",
        "longitude"
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing hospital columns: {missing}"
        )

    df = df.dropna(
        subset=required
    )

    return df


def nearest_hospital(
    latitude,
    longitude
):

    df = load_hospitals()

    best_distance = float("inf")
    best_row = None

    for _, row in df.iterrows():

        distance = haversine(
            latitude,
            longitude,
            row["latitude"],
            row["longitude"]
        )

        if distance < best_distance:

            best_distance = distance
            best_row = row

    if best_row is None:

        raise RuntimeError(
            "No valid hospital locations found."
        )

    return {
        "hospital_name": best_row.get(
            "hospital_name",
            "Unknown Hospital"
        ),
        "distance_km": round(
            best_distance,
            3
        ),
        "latitude": float(
            best_row["latitude"]
        ),
        "longitude": float(
            best_row["longitude"]
        )
    }