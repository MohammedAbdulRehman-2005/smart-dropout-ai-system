# ml/model.py - XGBoost Dropout Risk Prediction Model
# Trains, saves, loads, and predicts with the core ML model
# Risk score is output as 0-100 (probability * 100)

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    roc_auc_score, classification_report,
    mean_absolute_error, accuracy_score
)
from sklearn.neighbors import NearestNeighbors
import joblib
import os
import logging
from typing import Tuple, Dict, Optional, List

from ml.features import FEATURE_COLUMNS, features_to_dataframe
from config import settings

logger = logging.getLogger(__name__)


class DropoutRiskModel:
    """
    XGBoost-based dropout risk prediction model.
    
    Outputs a risk score 0-100 where:
    - 0-40:  Low risk (green)
    - 41-70: Medium risk (yellow)  
    - 71-100: High risk (red)
    """

    def __init__(self):
        self.model: Optional[xgb.XGBClassifier] = None
        self.scaler: Optional[StandardScaler] = None
        self.knn: Optional[NearestNeighbors] = None
        self.feature_names: List[str] = FEATURE_COLUMNS
        self.model_version: str = "1.0.0"
        self.is_trained: bool = False
        self._load_if_exists()

    def _load_if_exists(self):
        """Attempt to load pre-trained model from disk on initialization."""
        try:
            if (os.path.exists(settings.MODEL_PATH) and
                    os.path.exists(settings.SCALER_PATH)):
                self.model = joblib.load(settings.MODEL_PATH)
                self.scaler = joblib.load(settings.SCALER_PATH)
                if os.path.exists(settings.KNN_PATH):
                    self.knn = joblib.load(settings.KNN_PATH)
                self.is_trained = True
                logger.info("✅ Pre-trained model loaded from disk")
        except Exception as e:
            logger.warning(f"Could not load saved model: {e}")

    def train(self, df: pd.DataFrame, target_col: str = "dropout") -> Dict:
        """
        Train the XGBoost model on the provided dataset.
        
        df: DataFrame with feature columns + target column
        target_col: Column name for binary dropout label (0=stayed, 1=dropout)
        
        Returns training metrics dict.
        """
        logger.info(f"🚀 Starting model training on {len(df)} samples...")

        # Prepare features
        X = df[FEATURE_COLUMNS].copy()
        y = df[target_col].copy()

        # Validate
        if len(X) < 10:
            raise ValueError("Need at least 10 samples to train")

        # Handle missing values
        X = X.fillna(X.median())

        # Train/test split (stratified to maintain class balance)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Class imbalance handling
        pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)

        # XGBoost model with tuned hyperparameters
        self.model = xgb.XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            gamma=0.1,
            reg_alpha=0.1,
            reg_lambda=1.0,
            scale_pos_weight=pos_weight,
            eval_metric="auc",
            random_state=42,
            n_jobs=-1,
            use_label_encoder=False
        )

        # Train with early stopping on eval set
        self.model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_test_scaled, y_test)],
            verbose=False
        )

        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        y_proba = self.model.predict_proba(X_test_scaled)[:, 1]

        metrics = {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "auc_roc": float(roc_auc_score(y_test, y_proba)),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "dropout_rate": float(y.mean()),
            "feature_count": len(FEATURE_COLUMNS),
        }
        logger.info(f"📊 Training complete: AUC={metrics['auc_roc']:.3f}, "
                    f"Accuracy={metrics['accuracy']:.3f}")

        # Train KNN for similarity matching (on scaled features)
        X_all_scaled = self.scaler.transform(X.fillna(X.median()))
        self.knn = NearestNeighbors(n_neighbors=6, metric="euclidean")
        self.knn.fit(X_all_scaled)

        # Store training indices for KNN lookup
        self._train_indices = df.index.tolist()

        # Save models to disk
        self._save()
        self.is_trained = True

        return metrics

    def predict_risk(self, feature_vector: Dict) -> Tuple[float, float]:
        """
        Predict risk score for a single student.
        
        Returns:
            (risk_score_0_to_100, dropout_probability_0_to_1)
        """
        if not self.is_trained:
            raise RuntimeError("Model not trained yet. Call /train-model first.")

        df = features_to_dataframe(feature_vector)
        X_scaled = self.scaler.transform(df)

        probability = float(self.model.predict_proba(X_scaled)[0, 1])
        risk_score = round(probability * 100, 1)

        return risk_score, probability

    def predict_batch(self, feature_df: pd.DataFrame) -> np.ndarray:
        """Predict risk scores for a batch of students."""
        if not self.is_trained:
            raise RuntimeError("Model not trained yet.")

        X = feature_df[FEATURE_COLUMNS].fillna(0)
        X_scaled = self.scaler.transform(X)
        probabilities = self.model.predict_proba(X_scaled)[:, 1]
        return probabilities * 100  # 0-100 scores

    def find_similar_students(
        self, feature_vector: Dict, student_ids: List[int], k: int = 5
    ) -> List[int]:
        """
        Use KNN to find k most similar students.
        
        feature_vector: Feature dict for the query student
        student_ids: Ordered list of student DB ids (matches training order)
        Returns: List of similar student DB ids
        """
        if not self.knn or not self.is_trained:
            return []

        df = features_to_dataframe(feature_vector)
        X_scaled = self.scaler.transform(df)

        _, indices = self.knn.kneighbors(X_scaled, n_neighbors=min(k + 1, len(student_ids)))
        # Exclude the query student itself (index 0 = itself if included)
        neighbor_indices = indices[0][1:]  # Skip first (self)

        return [
            student_ids[i] for i in neighbor_indices
            if i < len(student_ids)
        ][:k]

    def forecast_risk_trajectory(
        self, current_risk: float,
        attendance_trend: float,
        score_trend: float
    ) -> Dict[str, float]:
        """
        Forecast future risk scores based on current trends.
        Uses simple linear extrapolation with decay factor.
        
        Returns predicted risk at 30, 60, 90 days.
        """
        # Attendance degradation contribution
        # A 1% monthly attendance drop translates to ~0.5 risk increase
        att_monthly_impact = -attendance_trend * 0.5  # negative trend = risk increase

        # Score degradation contribution
        # A 1-point score drop per semester translates to ~0.3 risk increase
        score_monthly_impact = -score_trend * 0.3

        total_monthly_increase = att_monthly_impact + score_monthly_impact

        # Clip to prevent unrealistic projections
        total_monthly_increase = np.clip(total_monthly_increase, -5.0, 8.0)

        def project(days: int) -> float:
            months = days / 30
            projected = current_risk + (total_monthly_increase * months)
            # Apply slight regression toward mean for longer forecasts
            regression = (current_risk - 50) * 0.05 * months
            projected -= regression
            return float(np.clip(projected, 0, 100))

        return {
            "risk_30d": project(30),
            "risk_60d": project(60),
            "risk_90d": project(90),
        }

    def detect_behavioral_drift(
        self, prediction_history: List[Dict]
    ) -> Tuple[bool, str]:
        """
        Detect if a student's risk is drifting significantly.
        
        prediction_history: List of past predictions (most recent first)
        Returns: (drift_detected: bool, description: str)
        """
        if len(prediction_history) < 3:
            return False, "Insufficient history for drift detection"

        recent_scores = [p["risk_score"] for p in prediction_history[:5]]

        # Check for rapid increase (>15 points in last 2 predictions)
        if len(recent_scores) >= 2:
            recent_delta = recent_scores[0] - recent_scores[1]
            if recent_delta > 15:
                return True, f"Risk increased sharply by {recent_delta:.1f} points recently"

        # Check for consistent upward trend
        if len(recent_scores) >= 4:
            x = np.arange(len(recent_scores))
            slope = np.polyfit(x, recent_scores[::-1], 1)[0]  # Reverse to chronological
            if slope > 5.0:  # Increasing >5 pts per period
                return True, f"Consistent upward risk trend detected (slope: {slope:.1f})"

        # Check for volatility (high variance)
        if len(recent_scores) >= 4:
            std_dev = np.std(recent_scores)
            if std_dev > 20:
                return True, f"High risk volatility detected (std: {std_dev:.1f})"

        return False, "No significant behavioral drift detected"

    def _save(self):
        """Save trained model artifacts to disk."""
        os.makedirs(os.path.dirname(settings.MODEL_PATH), exist_ok=True)
        joblib.dump(self.model, settings.MODEL_PATH)
        joblib.dump(self.scaler, settings.SCALER_PATH)
        if self.knn:
            joblib.dump(self.knn, settings.KNN_PATH)
        logger.info(f"💾 Model saved to {settings.MODEL_PATH}")

    def get_feature_importance(self) -> Dict[str, float]:
        """Return feature importance scores from the trained model."""
        if not self.is_trained:
            return {}
        importance = self.model.feature_importances_
        return dict(zip(FEATURE_COLUMNS, importance.tolist()))


def get_risk_level(risk_score: float) -> str:
    """Convert numeric risk score to categorical level."""
    if risk_score <= 40:
        return "low"
    elif risk_score <= 70:
        return "medium"
    else:
        return "high"


def get_risk_color(risk_score: float) -> str:
    """Get hex color for risk score visualization."""
    if risk_score <= 40:
        return "#22c55e"   # Green
    elif risk_score <= 70:
        return "#eab308"   # Yellow
    else:
        return "#ef4444"   # Red


# Global singleton model instance
_model_instance: Optional[DropoutRiskModel] = None


def get_model() -> DropoutRiskModel:
    """Get or create the global model instance."""
    global _model_instance
    if _model_instance is None:
        _model_instance = DropoutRiskModel()
    return _model_instance
