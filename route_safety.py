import joblib
import pandas as pd


# ==========================================
# LOAD REAL CRIME MODEL
# ==========================================

model_data = joblib.load(
    "real_crime_model.pkl"
)

model = model_data["model"]
features = model_data["features"]


# ==========================================
# PREDICT CRIME RISK
# ==========================================

def predict_route_safety(
    current_month,
    year_to_date,
    crime_activity
):

    data = pd.DataFrame([
        {
            "During the current month": current_month,
            "During the current year upto the end of month under review": year_to_date,
            "crime_activity": crime_activity
        }
    ])

    prediction = model.predict(
        data[features]
    )[0]

    prediction = float(prediction)


    # ======================================
    # TEMPORARY COMPARATIVE SCORE
    # ======================================

    safety_score = 100 - (
        prediction * 100
    )

    safety_score = max(
        0,
        min(
            100,
            safety_score
        )
    )


    if safety_score >= 70:

        risk = "Low"

    elif safety_score >= 40:

        risk = "Medium"

    else:

        risk = "High"


    return {
        "risk": risk,
        "safety_score": round(
            safety_score,
            2
        ),
        "crime_risk": round(
            prediction,
            4
        ),
        "points_analyzed": 1
    }