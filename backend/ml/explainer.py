# ml/explainer.py - SHAP-based Explainable AI for dropout predictions
# Computes SHAP values and translates them into human-readable explanations

import shap
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging

from ml.features import FEATURE_COLUMNS, features_to_dataframe

logger = logging.getLogger(__name__)

# Human-readable labels for each feature
FEATURE_LABELS = {
    "avg_attendance_pct": "Average Attendance Rate",
    "min_attendance_pct": "Lowest Monthly Attendance",
    "attendance_trend": "Attendance Trend Over Time",
    "max_consecutive_absences": "Longest Absence Streak",
    "late_days_total": "Total Late Arrivals",
    "avg_score": "Average Academic Score",
    "score_trend": "Grade Trend Over Time",
    "failed_subjects_total": "Number of Failed Subjects",
    "gpa": "Current GPA",
    "homework_completion_pct": "Homework Completion Rate",
    "class_participation_score": "Class Participation",
    "family_income_encoded": "Family Income Level",
    "parents_education_encoded": "Parents' Education Level",
    "is_single_parent": "Single Parent Household",
    "has_disability": "Learning Disability",
    "distance_from_school_km": "Distance from School",
    "avg_sentiment_score": "Emotional Well-being (Sentiment)",
    "negative_feedback_count": "Negative Feedback Instances",
    "attendance_academic_correlation": "Combined Attendance-Academic Risk",
    "age": "Student Age",
    "grade": "Current Grade Level",
}

# Action templates for each feature's intervention
FACTOR_RECOMMENDATIONS = {
    "avg_attendance_pct": {
        "increasing": "🟢 Attendance is improving. Maintain current engagement.",
        "decreasing": "🔴 Attendance is critically low. Initiate parent-teacher meeting immediately and explore transportation/health barriers.",
    },
    "min_attendance_pct": "📋 Investigate worst attendance month—identify if external event triggered absence pattern.",
    "attendance_trend": {
        "positive": "📈 Attendance trending upward.",
        "negative": "📉 Attendance declining trend. Schedule monthly check-ins with student."
    },
    "max_consecutive_absences": "⚠️ Long absence streak detected. Consider home visit or counselor intervention.",
    "late_days_total": "⏰ Frequent tardiness. Discuss scheduling and transportation challenges with family.",
    "avg_score": "📚 Below-average academic performance. Assign peer tutor and provide extra support resources.",
    "score_trend": {
        "positive": "📈 Grades are improving. Recognize and encourage student.",
        "negative": "📉 Academic performance declining. Review subject difficulty and consider remedial classes."
    },
    "failed_subjects_total": "❗ Multiple subject failures. Create individual academic improvement plan (AIP).",
    "gpa": "📖 Low GPA indicates systemic academic struggles. Consider learning assessment.",
    "homework_completion_pct": "📝 Low homework completion. Identify if student has home study environment or time constraints.",
    "class_participation_score": "🙋 Low classroom engagement. Consider mental health check-in.",
    "family_income_encoded": "💰 Financial challenges may be a barrier. Connect family with school financial assistance programs.",
    "parents_education_encoded": "👪 Limited parental academic support. Provide additional school-based resources and parent guidance.",
    "is_single_parent": "🏠 Single-parent household. Be sensitive to home responsibilities and consider flexible schedule options.",
    "has_disability": "♿ Learning disability noted. Ensure appropriate accommodations and IEP review.",
    "distance_from_school_km": "🚌 Long commute may cause fatigue. Explore bus routes or after-school programs.",
    "avg_sentiment_score": "💬 Negative emotional state detected. Immediate counselor session recommended.",
    "negative_feedback_count": "⚠️ Multiple negative feedback entries. Explore sources of frustration or anxiety.",
    "attendance_academic_correlation": "⚡ Combined attendance and academic decline is a strong dropout indicator. Urgent intervention required.",
    "age": "👤 Age-related factors considered.",
    "grade": "🎓 Grade transition pressure noted. Provide transition support.",
}


class DropoutExplainer:
    """
    Generates SHAP-based explanations for individual dropout risk predictions.
    """

    def __init__(self, model, scaler):
        self.model = model
        self.scaler = scaler
        self._explainer: Optional[shap.TreeExplainer] = None

    def _get_explainer(self) -> shap.TreeExplainer:
        """Lazy initialization of SHAP TreeExplainer."""
        if self._explainer is None:
            self._explainer = shap.TreeExplainer(self.model)
        return self._explainer

    def compute_shap_values(self, feature_vector: Dict) -> Dict[str, float]:
        """
        Compute SHAP values for a single student's feature vector.
        
        Returns a dict mapping feature_name -> shap_value
        Positive SHAP = increases risk, Negative = decreases risk
        """
        df = features_to_dataframe(feature_vector)
        X_scaled = self.scaler.transform(df)

        explainer = self._get_explainer()
        shap_values = explainer.shap_values(X_scaled)

        # For binary classification, shap_values has shape (2, n_features)
        # Index 1 = dropout class
        if isinstance(shap_values, list):
            vals = shap_values[1][0]
        else:
            vals = shap_values[0]

        return dict(zip(FEATURE_COLUMNS, vals.tolist()))

    def get_top_risk_factors(
        self, shap_values: Dict[str, float], n: int = 3
    ) -> List[Dict]:
        """
        Extract top N risk-increasing factors from SHAP values.
        
        Returns list of:
        {
            "feature": "avg_attendance_pct",
            "label": "Average Attendance Rate",
            "shap_value": 0.23,
            "impact": "high",
            "direction": "increasing_risk",
            "recommendation": "..."
        }
        """
        # Sort by absolute SHAP value, descending
        sorted_factors = sorted(
            shap_values.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )

        top_factors = []
        for feature, shap_val in sorted_factors[:n]:
            impact_magnitude = abs(shap_val)

            # Classify impact level
            if impact_magnitude > 0.3:
                impact = "critical"
            elif impact_magnitude > 0.15:
                impact = "high"
            elif impact_magnitude > 0.05:
                impact = "medium"
            else:
                impact = "low"

            direction = "increasing_risk" if shap_val > 0 else "decreasing_risk"

            # Get recommendation
            rec_entry = FACTOR_RECOMMENDATIONS.get(feature, "Review this factor with the student.")
            if isinstance(rec_entry, dict):
                rec = rec_entry.get("negative" if shap_val > 0 else "positive", "Monitor this factor.")
            else:
                rec = rec_entry

            top_factors.append({
                "feature": feature,
                "label": FEATURE_LABELS.get(feature, feature.replace("_", " ").title()),
                "shap_value": round(float(shap_val), 4),
                "impact": impact,
                "direction": direction,
                "recommendation": rec,
                "rank": len(top_factors) + 1
            })

        return top_factors

    def generate_explanation_summary(
        self, risk_score: float, top_factors: List[Dict]
    ) -> str:
        """
        Generate a human-readable explanation paragraph for counselors/teachers.
        """
        risk_label = "HIGH" if risk_score > 70 else "MEDIUM" if risk_score > 40 else "LOW"

        if not top_factors:
            return f"Risk score: {risk_score}/100 ({risk_label}). No significant risk factors identified."

        factor_summaries = []
        for f in top_factors[:3]:
            label = f["label"]
            direction = "increasing" if f["direction"] == "increasing_risk" else "decreasing"
            factor_summaries.append(f"{label} ({direction} risk)")

        factors_str = ", ".join(factor_summaries)
        summary = (
            f"This student has a {risk_label} dropout risk score of {risk_score}/100. "
            f"The primary contributing factors are: {factors_str}. "
        )

        if risk_score > 70:
            summary += "Immediate intervention is strongly recommended."
        elif risk_score > 40:
            summary += "Proactive monitoring and targeted support are advised."
        else:
            summary += "Continue routine support and monitoring."

        return summary

    def explain_prediction(
        self, feature_vector: Dict, risk_score: float
    ) -> Dict:
        """
        Full explanation pipeline: SHAP → top factors → summary.
        Returns a complete explanation object.
        """
        try:
            shap_values = self.compute_shap_values(feature_vector)
            top_factors = self.get_top_risk_factors(shap_values, n=5)
            summary = self.generate_explanation_summary(risk_score, top_factors)

            return {
                "risk_score": risk_score,
                "shap_values": shap_values,
                "top_factors": top_factors[:3],  # Top 3 for display
                "all_factors": top_factors,
                "summary": summary,
            }
        except Exception as e:
            logger.error(f"SHAP explanation failed: {e}")
            # Fallback: use model feature importance
            return {
                "risk_score": risk_score,
                "shap_values": {},
                "top_factors": _get_fallback_factors(feature_vector, risk_score),
                "all_factors": [],
                "summary": f"Risk score: {risk_score}/100. Explanation temporarily unavailable.",
            }


def _get_fallback_factors(feature_vector: Dict, risk_score: float) -> List[Dict]:
    """Fallback explanation using rule-based logic when SHAP fails."""
    factors = []

    # Rule-based checks
    if feature_vector.get("avg_attendance_pct", 100) < 75:
        factors.append({
            "feature": "avg_attendance_pct",
            "label": "Average Attendance Rate",
            "shap_value": 0.3,
            "impact": "high",
            "direction": "increasing_risk",
            "recommendation": FACTOR_RECOMMENDATIONS["avg_attendance_pct"]["decreasing"],
            "rank": len(factors) + 1
        })

    if feature_vector.get("avg_score", 100) < 50:
        factors.append({
            "feature": "avg_score",
            "label": "Average Academic Score",
            "shap_value": 0.25,
            "impact": "high",
            "direction": "increasing_risk",
            "recommendation": FACTOR_RECOMMENDATIONS["avg_score"],
            "rank": len(factors) + 1
        })

    if feature_vector.get("avg_sentiment_score", 0) < -0.3:
        factors.append({
            "feature": "avg_sentiment_score",
            "label": "Emotional Well-being",
            "shap_value": 0.2,
            "impact": "medium",
            "direction": "increasing_risk",
            "recommendation": FACTOR_RECOMMENDATIONS["avg_sentiment_score"],
            "rank": len(factors) + 1
        })

    return factors[:3]
