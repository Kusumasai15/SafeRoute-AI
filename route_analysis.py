import pandas as pd

from route_safety import predict_route_safety
from police_distance import nearest_police_station
from hospital_distance import nearest_hospital


CRIME_FILE = "crime_features.csv"


def load_crime_baseline():

    df = pd.read_csv(
        CRIME_FILE
    )

    df.columns = (
        df.columns
        .str.strip()
    )

    numeric_columns = [
        "During the current month",
        "During the current year upto the end of month under review",
        "crime_activity"
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    df = df.dropna(
        subset=numeric_columns
    )

    if df.empty:
        raise ValueError(
            "No valid crime records found."
        )

    return {
        "current_month": df[
            "During the current month"
        ].mean(),

        "year_to_date": df[
            "During the current year upto the end of month under review"
        ].mean(),

        "crime_activity": df[
            "crime_activity"
        ].mean()
    }


def proximity_score(
    distance_km
):
    """
    Converts distance into a comparative 0-100 score.
    Closer emergency services = higher score.
    """

    score = (
        100
        / (1 + distance_km)
    )

    return max(
        0,
        min(
            100,
            score
        )
    )


def analyze_route(route):

    coordinates = (
        route["geometry"]["coordinates"]
    )

    max_points = 10

    step = max(
        1,
        len(coordinates) // max_points
    )

    sampled_points = coordinates[
        ::step
    ][:max_points]


    if not sampled_points:
        raise ValueError(
            "Route contains no coordinates."
        )


    crime = load_crime_baseline()


    police_distances = []
    hospital_distances = []

    police_names = []
    hospital_names = []


    for point in sampled_points:

        longitude = point[0]
        latitude = point[1]


        police = nearest_police_station(
            latitude,
            longitude
        )

        hospital = nearest_hospital(
            latitude,
            longitude
        )


        police_distances.append(
            police["distance_km"]
        )

        hospital_distances.append(
            hospital["distance_km"]
        )


        police_names.append(
            police["police_station"]
        )

        hospital_names.append(
            hospital["hospital_name"]
        )


    average_police_distance = (
        sum(police_distances)
        / len(police_distances)
    )

    worst_police_distance = max(
        police_distances
    )


    average_hospital_distance = (
        sum(hospital_distances)
        / len(hospital_distances)
    )

    worst_hospital_distance = max(
        hospital_distances
    )


    crime_result = predict_route_safety(
        crime["current_month"],
        crime["year_to_date"],
        crime["crime_activity"]
    )


    police_score = proximity_score(
        average_police_distance
    )

    hospital_score = proximity_score(
        average_hospital_distance
    )


    final_safety_score = (
        crime_result["safety_score"] * 0.60
        + police_score * 0.25
        + hospital_score * 0.15
    )


    final_safety_score = max(
        0,
        min(
            100,
            final_safety_score
        )
    )


    if final_safety_score >= 70:
        risk = "Low"

    elif final_safety_score >= 40:
        risk = "Medium"

    else:
        risk = "High"


    return {

        "safety_score": round(
            final_safety_score,
            2
        ),

        "crime_safety_score": round(
            crime_result["safety_score"],
            2
        ),

        "police_score": round(
            police_score,
            2
        ),

        "hospital_score": round(
            hospital_score,
            2
        ),

        "average_police_distance": round(
            average_police_distance,
            3
        ),

        "worst_police_distance": round(
            worst_police_distance,
            3
        ),

        "average_hospital_distance": round(
            average_hospital_distance,
            3
        ),

        "worst_hospital_distance": round(
            worst_hospital_distance,
            3
        ),

        "risk": risk,

        "crime_risk": crime_result[
            "crime_risk"
        ],

        "points_analyzed": len(
            sampled_points
        ),

        "police_stations": list(
            dict.fromkeys(
                police_names
            )
        ),

        "hospitals": list(
            dict.fromkeys(
                hospital_names
            )
        )
    }