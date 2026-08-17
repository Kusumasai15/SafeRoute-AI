import pandas as pd
import math


POLICE_FILE = "police_locations.csv"


def haversine(
    lat1,
    lon1,
    lat2,
    lon2
):
    """
    Return distance between two points in kilometres.
    """

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


def load_police_locations():

    df = pd.read_csv(
        POLICE_FILE
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
            f"Missing columns: {missing}"
        )

    df = df.dropna(
        subset=required
    )

    return df


def nearest_police_station(
    latitude,
    longitude
):

    df = load_police_locations()

    distances = []

    for _, row in df.iterrows():

        distance = haversine(
            latitude,
            longitude,
            row["latitude"],
            row["longitude"]
        )

        distances.append(distance)


    nearest_index = min(
        range(len(distances)),
        key=distances.__getitem__
    )


    nearest_row = df.iloc[
        nearest_index
    ]


    return {
        "police_station": nearest_row.get(
            "police_station",
            "Unknown"
        ),
        "distance_km": round(
            distances[nearest_index],
            3
        ),
        "latitude": nearest_row[
            "latitude"
        ],
        "longitude": nearest_row[
            "longitude"
        ]
    }