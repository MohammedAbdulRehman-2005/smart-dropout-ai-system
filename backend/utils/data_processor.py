# utils/data_processor.py - CSV/Excel data ingestion and preprocessing
# Handles file upload, validation, cleaning, and database seeding

import pandas as pd
import numpy as np
import io
import logging
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session

from db import crud
from ml.sentiment import get_sentiment_analyzer

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Handles CSV/Excel ingestion, cleaning, and database population.
    
    Supported formats:
    - students.csv: Student demographics
    - attendance.csv: Monthly attendance records
    - academics.csv: Semester academic records
    - feedback.csv: Student feedback text
    - combined.csv: All-in-one format
    """

    REQUIRED_STUDENT_COLUMNS = [
        "student_id", "full_name", "grade", "age"
    ]

    OPTIONAL_STUDENT_COLUMNS = [
        "gender", "section", "family_income_level", "parents_education",
        "single_parent", "has_disability", "distance_from_school_km",
        "guardian_name", "guardian_phone", "guardian_email"
    ]

    def process_file(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Load and do basic cleaning of uploaded file."""
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_content))
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            raise ValueError(f"Unsupported file format: {filename}. Use CSV or Excel.")

        # Basic cleaning
        df.columns = [col.lower().strip().replace(" ", "_") for col in df.columns]
        df = df.dropna(how="all")  # Drop completely empty rows

        logger.info(f"Loaded {len(df)} rows from {filename}")
        return df

    def validate_student_data(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate student DataFrame for required columns."""
        errors = []
        for col in self.REQUIRED_STUDENT_COLUMNS:
            if col not in df.columns:
                errors.append(f"Missing required column: '{col}'")

        if "student_id" in df.columns and df["student_id"].duplicated().any():
            n_dupes = df["student_id"].duplicated().sum()
            errors.append(f"{n_dupes} duplicate student_id values found")

        return len(errors) == 0, errors

    def ingest_students(self, df: pd.DataFrame, db: Session) -> Dict:
        """Import student records from DataFrame into database."""
        valid, errors = self.validate_student_data(df)
        if not valid:
            raise ValueError(f"Validation failed: {'; '.join(errors)}")

        created = 0
        updated = 0
        skipped = 0

        for _, row in df.iterrows():
            try:
                student_data = {
                    "student_id": str(row["student_id"]),
                    "full_name": str(row["full_name"]),
                    "grade": int(row.get("grade", 9)),
                    "age": int(row.get("age", 15)),
                    "gender": str(row.get("gender", "unknown")),
                    "section": str(row.get("section", "A")),
                    "family_income_level": str(row.get("family_income_level", "medium")).lower(),
                    "parents_education": str(row.get("parents_education", "secondary")).lower(),
                    "single_parent": bool(row.get("single_parent", False)),
                    "has_disability": bool(row.get("has_disability", False)),
                    "distance_from_school_km": float(row.get("distance_from_school_km", 2.0)),
                    "guardian_name": str(row.get("guardian_name", "")),
                    "guardian_phone": str(row.get("guardian_phone", "")),
                    "guardian_email": str(row.get("guardian_email", "")),
                }

                existing = crud.get_student_by_student_id(db, student_data["student_id"])
                if existing:
                    crud.update_student(db, existing.id, student_data)
                    updated += 1
                else:
                    crud.create_student(db, student_data)
                    created += 1

            except Exception as e:
                logger.warning(f"Skipping row {row.get('student_id', '?')}: {e}")
                skipped += 1

        return {"created": created, "updated": updated, "skipped": skipped}

    def ingest_attendance(self, df: pd.DataFrame, db: Session) -> Dict:
        """Import attendance records from DataFrame."""
        created = 0
        errors = 0

        for _, row in df.iterrows():
            try:
                student = crud.get_student_by_student_id(db, str(row["student_id"]))
                if not student:
                    errors += 1
                    continue

                total = int(row.get("total_days", 22))
                present = int(row.get("present_days", 18))
                absent = total - present
                att_pct = round((present / max(total, 1)) * 100, 1)

                att_data = {
                    "total_days": total,
                    "present_days": present,
                    "absent_days": absent,
                    "late_days": int(row.get("late_days", 0)),
                    "attendance_pct": att_pct,
                    "consecutive_absences": int(row.get("consecutive_absences", 0)),
                }

                crud.create_or_update_attendance(
                    db,
                    student.id,
                    str(row.get("month", "2024-01")),
                    int(row.get("year", 2024)),
                    att_data
                )
                created += 1

            except Exception as e:
                logger.warning(f"Attendance row error: {e}")
                errors += 1

        return {"created": created, "errors": errors}

    def ingest_academics(self, df: pd.DataFrame, db: Session) -> Dict:
        """Import academic records from DataFrame."""
        created = 0
        errors = 0

        for _, row in df.iterrows():
            try:
                student = crud.get_student_by_student_id(db, str(row["student_id"]))
                if not student:
                    errors += 1
                    continue

                scores = []
                subject_cols = ["math_score", "science_score", "english_score",
                                "social_score", "language_score"]
                for col in subject_cols:
                    if col in row and pd.notna(row[col]):
                        scores.append(float(row[col]))

                avg_score = np.mean(scores) if scores else 60.0
                gpa = round((avg_score / 100) * 4.0, 2)
                failed = sum(1 for s in scores if s < 35)

                acad_data = {
                    "math_score": float(row.get("math_score", 60)),
                    "science_score": float(row.get("science_score", 60)),
                    "english_score": float(row.get("english_score", 60)),
                    "social_score": float(row.get("social_score", 60)),
                    "language_score": float(row.get("language_score", 60)),
                    "average_score": round(avg_score, 1),
                    "gpa": gpa,
                    "failed_subjects": failed,
                    "homework_completion_pct": float(row.get("homework_completion_pct", 80)),
                    "class_participation_score": float(row.get("class_participation_score", 3.0)),
                }

                crud.create_or_update_academic(
                    db,
                    student.id,
                    str(row.get("semester", "2024-S1")),
                    int(row.get("year", 2024)),
                    acad_data
                )
                created += 1

            except Exception as e:
                logger.warning(f"Academic row error: {e}")
                errors += 1

        return {"created": created, "errors": errors}

    def ingest_feedback(self, df: pd.DataFrame, db: Session) -> Dict:
        """Import and analyze student feedback from DataFrame."""
        created = 0
        errors = 0
        analyzer = get_sentiment_analyzer()

        for _, row in df.iterrows():
            try:
                student = crud.get_student_by_student_id(db, str(row["student_id"]))
                if not student:
                    errors += 1
                    continue

                text = str(row.get("feedback_text", ""))
                if not text.strip():
                    continue

                analysis = analyzer.analyze(text)

                feedback_data = {
                    "feedback_text": text,
                    "source": str(row.get("source", "survey")),
                    "sentiment_score": analysis["sentiment_score"],
                    "sentiment_label": analysis["sentiment_label"],
                    "emotion_tags": analysis["emotion_tags"],
                }

                crud.create_feedback(db, student.id, feedback_data)
                created += 1

            except Exception as e:
                logger.warning(f"Feedback row error: {e}")
                errors += 1

        return {"created": created, "errors": errors}

    def detect_combined_format(self, df: pd.DataFrame) -> str:
        """Detect what type of data is in the uploaded file."""
        cols = set(df.columns)

        if "feedback_text" in cols:
            return "feedback"
        elif "attendance_pct" in cols or "present_days" in cols:
            return "attendance"
        elif "math_score" in cols or "average_score" in cols:
            return "academics"
        elif "student_id" in cols and "full_name" in cols:
            return "students"
        else:
            return "unknown"
