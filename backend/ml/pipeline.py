# ml/pipeline.py - ML Pipeline Orchestrator
# Coordinates data ingestion → feature engineering → training → prediction
# This is the main interface for all ML operations

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session

from ml.model import DropoutRiskModel, get_model, get_risk_level
from ml.explainer import DropoutExplainer
from ml.features import (
    FEATURE_COLUMNS, build_feature_vector,
    features_to_dataframe, dataframe_to_features
)
from ml.sentiment import get_sentiment_analyzer
from db import crud
from agents.study_plan_agent import get_notification_agent

logger = logging.getLogger(__name__)


class DropoutPipeline:
    """
    End-to-end ML pipeline for dropout risk prediction.
    
    Usage:
        pipeline = DropoutPipeline()
        result = await pipeline.predict_for_student(db, student_id=42)
    """

    def __init__(self):
        self.model: DropoutRiskModel = get_model()
        self.sentiment_analyzer = get_sentiment_analyzer()
        self._explainer: Optional[DropoutExplainer] = None

    def _get_explainer(self) -> DropoutExplainer:
        """Lazy init SHAP explainer (requires trained model)."""
        if self._explainer is None and self.model.is_trained:
            self._explainer = DropoutExplainer(
                self.model.model,
                self.model.scaler
            )
        return self._explainer

    # ════════════════════════════════════════════════════════
    # TRAINING
    # ════════════════════════════════════════════════════════

    def train_from_dataframe(self, df: pd.DataFrame) -> Dict:
        """
        Train model from a processed DataFrame.
        
        df must contain all FEATURE_COLUMNS + 'dropout' target column.
        """
        if "dropout" not in df.columns:
            # Synthetically generate labels if not present
            # (Use when only feature data is available without historical outcome)
            df = self._generate_synthetic_labels(df)

        feature_df = dataframe_to_features(df)
        feature_df["dropout"] = df["dropout"].values

        metrics = self.model.train(feature_df, target_col="dropout")

        # Reset explainer after retraining
        self._explainer = None

        return metrics

    def train_from_db(self, db: Session) -> Dict:
        """
        Train model using all student data from the database.
        Fetches, processes, and trains in one call.
        """
        logger.info("📥 Loading training data from database...")

        students = crud.get_students(db, limit=10000)
        if len(students) < 10:
            raise ValueError("Need at least 10 students in database to train")

        rows = []
        for student in students:
            att_records = crud.get_student_attendance(db, student.id)
            acad_records = crud.get_student_academics(db, student.id)
            fb_records = crud.get_student_feedback(db, student.id)

            att_dicts = [
                {
                    "attendance_pct": a.attendance_pct,
                    "consecutive_absences": a.consecutive_absences,
                    "late_days": a.late_days
                }
                for a in att_records
            ]
            acad_dicts = [
                {
                    "average_score": a.average_score,
                    "gpa": a.gpa,
                    "failed_subjects": a.failed_subjects,
                    "homework_completion_pct": a.homework_completion_pct,
                    "class_participation_score": a.class_participation_score,
                }
                for a in acad_records
            ]
            fb_dicts = [
                {"sentiment_score": f.sentiment_score or 0.0}
                for f in fb_records
            ]

            student_dict = {
                "age": student.age,
                "grade": student.grade,
                "distance_from_school_km": student.distance_from_school_km,
                "single_parent": student.single_parent,
                "has_disability": student.has_disability,
                "family_income_level": student.family_income_level,
                "parents_education": student.parents_education,
            }

            features = build_feature_vector(student_dict, att_dicts, acad_dicts, fb_dicts)
            features["student_id"] = student.id
            rows.append(features)

        df = pd.DataFrame(rows)
        df = self._generate_synthetic_labels(df)

        metrics = self.model.train(df, target_col="dropout")
        self._explainer = None

        logger.info(f"✅ Model trained on {len(df)} students")
        return metrics

    def _generate_synthetic_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate synthetic dropout labels based on feature thresholds.
        Used when historical dropout data isn't available.
        
        Risk factors that contribute to dropout label:
        - Low attendance (<70%)
        - Low scores (<50)
        - High consecutive absences (>10)
        - Negative sentiment
        - Multiple failed subjects
        """
        df = df.copy()
        score = np.zeros(len(df))

        if "avg_attendance_pct" in df.columns:
            score += (df["avg_attendance_pct"] < 70).astype(float) * 2
            score += (df["avg_attendance_pct"] < 50).astype(float) * 2

        if "avg_score" in df.columns:
            score += (df["avg_score"] < 50).astype(float) * 2
            score += (df["avg_score"] < 35).astype(float) * 2

        if "max_consecutive_absences" in df.columns:
            score += (df["max_consecutive_absences"] > 10).astype(float) * 1.5

        if "failed_subjects_total" in df.columns:
            score += (df["failed_subjects_total"] >= 2).astype(float) * 1.5

        if "avg_sentiment_score" in df.columns:
            score += (df["avg_sentiment_score"] < -0.3).astype(float) * 1.0

        if "family_income_encoded" in df.columns:
            score += (df["family_income_encoded"] == 0).astype(float) * 0.5

        # Add noise to prevent perfect separation
        noise = np.random.normal(0, 0.3, len(df))
        score += noise

        # Threshold for dropout label
        df["dropout"] = (score >= 4.0).astype(int)

        logger.info(f"Generated labels: {df['dropout'].sum()} dropouts / {len(df)} total "
                    f"({df['dropout'].mean():.1%} rate)")
        return df

    # ════════════════════════════════════════════════════════
    # PREDICTION
    # ════════════════════════════════════════════════════════

    def predict_for_student(
        self, db: Session, student_id: int
    ) -> Dict:
        """
        Full prediction pipeline for a single student.
        
        1. Fetch student data from DB
        2. Build feature vector
        3. Run model prediction
        4. Generate SHAP explanation
        5. Forecast risk trajectory
        6. Detect behavioral drift
        7. Find similar students (KNN)
        8. Store prediction in DB
        
        Returns complete prediction result dict.
        """
        student = crud.get_student_by_id(db, student_id)
        if not student:
            raise ValueError(f"Student {student_id} not found")

        if not self.model.is_trained:
            raise RuntimeError("Model not trained. Call /train-model first.")

        # 1. Fetch data
        att_records = crud.get_student_attendance(db, student_id)
        acad_records = crud.get_student_academics(db, student_id)
        fb_records = crud.get_student_feedback(db, student_id)
        prediction_history = crud.get_student_prediction_history(db, student_id)

        # 2. Build feature vector
        att_dicts = [
            {
                "attendance_pct": a.attendance_pct,
                "consecutive_absences": a.consecutive_absences,
                "late_days": a.late_days
            }
            for a in att_records
        ]
        acad_dicts = [
            {
                "average_score": a.average_score,
                "gpa": a.gpa,
                "failed_subjects": a.failed_subjects,
                "homework_completion_pct": a.homework_completion_pct,
                "class_participation_score": a.class_participation_score,
            }
            for a in acad_records
        ]

        # Analyze any unanalyzed feedback
        fb_dicts = []
        for fb in fb_records:
            if fb.sentiment_score is None:
                analysis = self.sentiment_analyzer.analyze(fb.feedback_text)
                fb.sentiment_score = analysis["sentiment_score"]
                try:
                    db.commit()
                except Exception:
                    db.rollback()
            fb_dicts.append({"sentiment_score": fb.sentiment_score or 0.0})

        student_dict = {
            "age": student.age,
            "grade": student.grade,
            "distance_from_school_km": student.distance_from_school_km,
            "single_parent": student.single_parent,
            "has_disability": student.has_disability,
            "family_income_level": student.family_income_level,
            "parents_education": student.parents_education,
        }

        feature_vector = build_feature_vector(student_dict, att_dicts, acad_dicts, fb_dicts)

        # 3. Predict
        risk_score, probability = self.model.predict_risk(feature_vector)
        risk_level = get_risk_level(risk_score)

        # 4. SHAP explanation
        explainer = self._get_explainer()
        if explainer:
            explanation = explainer.explain_prediction(feature_vector, risk_score)
        else:
            explanation = {
                "risk_score": risk_score,
                "shap_values": {},
                "top_factors": [],
                "summary": f"Risk score: {risk_score}/100"
            }

        # 5. Forecast trajectory
        att_trend = feature_vector.get("attendance_trend", 0.0)
        score_trend = feature_vector.get("score_trend", 0.0)
        trajectory = self.model.forecast_risk_trajectory(risk_score, att_trend, score_trend)

        # 6. Behavioral drift detection
        history_dicts = [
            {"risk_score": p.risk_score}
            for p in prediction_history
        ]
        drift_detected, drift_desc = self.model.detect_behavioral_drift(history_dicts)

        # 7. KNN similar students
        all_student_ids = [s.id for s in crud.get_students(db, limit=500)]
        similar_ids = self.model.find_similar_students(feature_vector, all_student_ids, k=5)
        similar_ids = [sid for sid in similar_ids if sid != student_id]

        # 8. Store prediction
        prediction_data = {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "shap_values": explanation.get("shap_values", {}),
            "top_risk_factors": explanation.get("top_factors", []),
            "predicted_risk_30d": trajectory["risk_30d"],
            "predicted_risk_60d": trajectory["risk_60d"],
            "predicted_risk_90d": trajectory["risk_90d"],
            "behavioral_drift_detected": drift_detected,
            "drift_description": drift_desc,
            "similar_student_ids": similar_ids[:5],
            "model_version": self.model.model_version,
        }
        crud.create_prediction(db, student_id, prediction_data)

        # Generate alert if high risk
        if risk_score > 70:
            self._create_risk_alert(db, student, risk_score, explanation)

        return {
            "student_id": student_id,
            "student_name": student.full_name,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "probability": round(probability, 3),
            "explanation": explanation,
            "trajectory": trajectory,
            "drift_detected": drift_detected,
            "drift_description": drift_desc,
            "similar_student_ids": similar_ids[:5],
            "features_used": feature_vector,
        }

    def predict_all_students(self, db: Session) -> List[Dict]:
        """Run predictions for all active students."""
        students = crud.get_students(db, limit=10000)
        results = []
        errors = []

        for student in students:
            try:
                result = self.predict_for_student(db, student.id)
                results.append({
                    "student_id": student.id,
                    "student_name": student.full_name,
                    "risk_score": result["risk_score"],
                    "risk_level": result["risk_level"],
                })
            except Exception as e:
                errors.append({"student_id": student.id, "error": str(e)})

        logger.info(f"Batch prediction: {len(results)} succeeded, {len(errors)} failed")
        return results

    def _create_risk_alert(self, db: Session, student, risk_score: float, explanation: Dict):
        """Create an automated alert for high-risk students."""
        try:
            existing_alerts = crud.get_student_alerts(db, student.id)
            # Don't spam alerts - check if unresolved high-risk alert already exists
            for alert in existing_alerts:
                if not alert.is_resolved and alert.alert_type == "high_risk":
                    return

            top_factors = explanation.get("top_factors", [])
            factor_text = (
                ", ".join([f["label"] for f in top_factors[:2]])
                if top_factors else "multiple risk factors"
            )

            crud.create_alert(db, student.id, {
                "alert_type": "high_risk",
                "severity": "critical" if risk_score > 85 else "high",
                "title": f"🚨 High Dropout Risk: {student.full_name}",
                "message": (
                    f"Student {student.full_name} (Grade {student.grade}) has a "
                    f"risk score of {risk_score}/100. "
                    f"Key factors: {factor_text}. Immediate intervention recommended."
                ),
                "sent_to_teacher": False,
                "sent_to_parent": False,
                "sent_to_counselor": False,
            })
            
            # Also trigger the Notification Agent
            notification_agent = get_notification_agent()
            student_dict = {
                "id": student.id,
                "full_name": student.full_name,
                "grade": student.grade
            }
            notification_agent.send_high_risk_alert(
                student=student_dict,
                risk_score=risk_score,
                top_factors=top_factors,
                recipients=["counselor@school.edu", "teacher@school.edu"]
            )
            
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")


# Global pipeline instance
_pipeline_instance: Optional[DropoutPipeline] = None


def get_pipeline() -> DropoutPipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = DropoutPipeline()
    return _pipeline_instance
