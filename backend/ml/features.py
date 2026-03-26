# ml/features.py - Feature engineering for dropout prediction
# Transforms raw student data into model-ready features including
# temporal patterns, rolling averages, and composite risk indicators

import pandas as pd
import numpy as np
from typing import Dict, List, Any


# ─────────────────────────────────────────────────────────
# FEATURE DEFINITIONS
# These are the exact features the model trains and predicts on
# ─────────────────────────────────────────────────────────
FEATURE_COLUMNS = [
    # Attendance features
    "avg_attendance_pct",           # Average attendance % across months
    "min_attendance_pct",           # Worst attendance month
    "attendance_trend",             # Slope of attendance over time (negative = declining)
    "max_consecutive_absences",     # Longest absence streak
    "late_days_total",              # Total late arrivals

    # Academic features
    "avg_score",                    # Mean score across subjects
    "score_trend",                  # Slope of scores over time
    "failed_subjects_total",        # Total subjects failed
    "gpa",                         # Current GPA
    "homework_completion_pct",      # Homework submission rate
    "class_participation_score",    # Teacher-rated engagement (1-5)

    # Socio-economic features
    "family_income_encoded",        # low=0, medium=1, high=2
    "parents_education_encoded",    # none=0, primary=1, secondary=2, graduate=3
    "is_single_parent",            # 0 or 1
    "has_disability",              # 0 or 1
    "distance_from_school_km",      # Physical distance

    # Behavioral / sentiment
    "avg_sentiment_score",         # NLP sentiment mean (-1 to 1)
    "negative_feedback_count",      # Count of negative sentiment entries

    # Derived risk indicators
    "attendance_academic_correlation",  # Low attendance + low grades = high risk
    "age",
    "grade",
]


def encode_categorical_features(df: pd.DataFrame) -> pd.DataFrame:
    """Encode categorical/string columns to numeric."""
    df = df.copy()

    # Family income level
    income_map = {"low": 0, "medium": 1, "high": 2}
    if "family_income_level" in df.columns:
        df["family_income_encoded"] = (
            df["family_income_level"].str.lower()
            .map(income_map).fillna(1)
        )

    # Parents education
    edu_map = {"none": 0, "primary": 1, "secondary": 2, "graduate": 3}
    if "parents_education" in df.columns:
        df["parents_education_encoded"] = (
            df["parents_education"].str.lower()
            .map(edu_map).fillna(1)
        )

    # Boolean flags
    for col in ["single_parent", "has_disability"]:
        if col in df.columns:
            df[f"is_{col}"] = df[col].astype(int)

    return df


def compute_attendance_features(attendance_records: List[Dict]) -> Dict:
    """
    Compute attendance features from a list of monthly records.
    
    attendance_records: [
        {"month": "2024-01", "attendance_pct": 85.0, "consecutive_absences": 2, "late_days": 1},
        ...
    ]
    """
    if not attendance_records:
        return {
            "avg_attendance_pct": 75.0,  # Assume average if no data
            "min_attendance_pct": 75.0,
            "attendance_trend": 0.0,
            "max_consecutive_absences": 0,
            "late_days_total": 0,
        }

    pcts = [r.get("attendance_pct", 75.0) for r in attendance_records]
    consecutive = [r.get("consecutive_absences", 0) for r in attendance_records]
    late = [r.get("late_days", 0) for r in attendance_records]

    # Compute linear trend (negative = declining)
    if len(pcts) >= 2:
        x = np.arange(len(pcts))
        trend = float(np.polyfit(x, pcts, 1)[0])  # Slope
    else:
        trend = 0.0

    return {
        "avg_attendance_pct": float(np.mean(pcts)),
        "min_attendance_pct": float(np.min(pcts)),
        "attendance_trend": trend,
        "max_consecutive_absences": int(max(consecutive)),
        "late_days_total": int(sum(late)),
    }


def compute_academic_features(academic_records: List[Dict]) -> Dict:
    """
    Compute academic features from a list of semester records.
    
    academic_records: [
        {"average_score": 65.0, "gpa": 2.5, "failed_subjects": 1, ...},
        ...
    ]
    """
    if not academic_records:
        return {
            "avg_score": 60.0,
            "score_trend": 0.0,
            "failed_subjects_total": 0,
            "gpa": 2.5,
            "homework_completion_pct": 70.0,
            "class_participation_score": 3.0,
        }

    scores = [r.get("average_score", 60.0) for r in academic_records]
    failed = [r.get("failed_subjects", 0) for r in academic_records]
    hw = [r.get("homework_completion_pct", 70.0) for r in academic_records]
    participation = [r.get("class_participation_score", 3.0) for r in academic_records]
    latest_gpa = academic_records[0].get("gpa", 2.5)  # Most recent

    # Score trend
    if len(scores) >= 2:
        x = np.arange(len(scores))
        trend = float(np.polyfit(x, scores, 1)[0])
    else:
        trend = 0.0

    return {
        "avg_score": float(np.mean(scores)),
        "score_trend": trend,
        "failed_subjects_total": int(sum(failed)),
        "gpa": float(latest_gpa),
        "homework_completion_pct": float(np.mean(hw)),
        "class_participation_score": float(np.mean(participation)),
    }


def compute_sentiment_features(feedback_records: List[Dict]) -> Dict:
    """Aggregate NLP sentiment scores from feedback records."""
    if not feedback_records:
        return {
            "avg_sentiment_score": 0.0,
            "negative_feedback_count": 0,
        }

    sentiments = [r.get("sentiment_score", 0.0) for r in feedback_records]
    negative_count = sum(1 for s in sentiments if s < -0.2)

    return {
        "avg_sentiment_score": float(np.mean(sentiments)),
        "negative_feedback_count": negative_count,
    }


def build_feature_vector(
    student: Dict,
    attendance_records: List[Dict],
    academic_records: List[Dict],
    feedback_records: List[Dict]
) -> Dict[str, float]:
    """
    Build the complete feature vector for a single student.
    This is the main function called during prediction.
    
    Returns a dict mapping feature_name -> float_value
    """
    features = {}

    # Attendance features
    att_features = compute_attendance_features(attendance_records)
    features.update(att_features)

    # Academic features
    acad_features = compute_academic_features(academic_records)
    features.update(acad_features)

    # Sentiment features
    sent_features = compute_sentiment_features(feedback_records)
    features.update(sent_features)

    # Student demographics
    features["age"] = float(student.get("age", 15))
    features["grade"] = float(student.get("grade", 9))
    features["distance_from_school_km"] = float(student.get("distance_from_school_km", 2.0))
    features["is_single_parent"] = int(bool(student.get("single_parent", False)))
    features["has_disability"] = int(bool(student.get("has_disability", False)))

    # Encode income
    income_map = {"low": 0, "medium": 1, "high": 2}
    features["family_income_encoded"] = income_map.get(
        str(student.get("family_income_level", "medium")).lower(), 1
    )

    # Encode education
    edu_map = {"none": 0, "primary": 1, "secondary": 2, "graduate": 3}
    features["parents_education_encoded"] = edu_map.get(
        str(student.get("parents_education", "secondary")).lower(), 2
    )

    # Derived composite indicator
    # Low attendance AND low grades = compounding risk
    att_norm = (100 - features["avg_attendance_pct"]) / 100
    score_norm = (100 - features["avg_score"]) / 100
    features["attendance_academic_correlation"] = float(att_norm * score_norm)

    # Ensure all feature columns exist, fill missing with 0
    for col in FEATURE_COLUMNS:
        if col not in features:
            features[col] = 0.0

    return {col: features[col] for col in FEATURE_COLUMNS}


def features_to_dataframe(feature_vector: Dict[str, float]) -> pd.DataFrame:
    """Convert a feature vector dict to a single-row DataFrame for model input."""
    return pd.DataFrame([feature_vector])[FEATURE_COLUMNS]


def dataframe_to_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process a raw uploaded DataFrame (from CSV/Excel) into model-ready features.
    Expects aggregated columns per student.
    """
    df = df.copy()
    df = encode_categorical_features(df)

    # Compute composite feature
    att_norm = (100 - df.get("avg_attendance_pct", 75)) / 100
    score_norm = (100 - df.get("avg_score", 60)) / 100
    df["attendance_academic_correlation"] = att_norm * score_norm

    # Fill NaN with column medians
    for col in FEATURE_COLUMNS:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())
        else:
            df[col] = 0.0

    return df[FEATURE_COLUMNS]
