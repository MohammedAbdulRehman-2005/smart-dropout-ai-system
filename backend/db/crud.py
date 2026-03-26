# db/crud.py - Database CRUD operations for all entities
# Provides clean data access layer between API routes and ORM models

from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional, List
import datetime

from db.models import (
    Student, Attendance, Academic, Prediction,
    Intervention, StudentFeedback, Alert, User, RiskLevel
)


# ════════════════════════════════════════════════════════
# USER CRUD
# ════════════════════════════════════════════════════════

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, email: str, hashed_password: str,
                full_name: str, role: str) -> User:
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ════════════════════════════════════════════════════════
# STUDENT CRUD
# ════════════════════════════════════════════════════════

def get_students(db: Session, skip: int = 0, limit: int = 100,
                 grade: Optional[int] = None,
                 risk_level: Optional[str] = None) -> List[Student]:
    """Fetch students with optional grade and risk level filters."""
    query = db.query(Student).filter(Student.is_active == True)
    if grade:
        query = query.filter(Student.grade == grade)
    return query.offset(skip).limit(limit).all()


def get_student_by_id(db: Session, student_id: int) -> Optional[Student]:
    return db.query(Student).filter(Student.id == student_id).first()


def get_student_by_student_id(db: Session, student_id: str) -> Optional[Student]:
    return db.query(Student).filter(Student.student_id == student_id).first()


def create_student(db: Session, student_data: dict) -> Student:
    student = Student(**student_data)
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def update_student(db: Session, student_id: int, updates: dict) -> Optional[Student]:
    student = get_student_by_id(db, student_id)
    if student:
        for key, value in updates.items():
            setattr(student, key, value)
        db.commit()
        db.refresh(student)
    return student


def get_total_student_count(db: Session) -> int:
    return db.query(Student).filter(Student.is_active == True).count()


# ════════════════════════════════════════════════════════
# ATTENDANCE CRUD
# ════════════════════════════════════════════════════════

def create_or_update_attendance(db: Session, student_db_id: int,
                                 month: str, year: int,
                                 attendance_data: dict) -> Attendance:
    """Create or update attendance record for a student/month."""
    existing = db.query(Attendance).filter(
        Attendance.student_id == student_db_id,
        Attendance.month == month,
        Attendance.year == year
    ).first()

    if existing:
        for key, value in attendance_data.items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        record = Attendance(
            student_id=student_db_id,
            month=month,
            year=year,
            **attendance_data
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record


def get_student_attendance(db: Session, student_id: int,
                            limit: int = 12) -> List[Attendance]:
    """Get recent attendance records ordered by most recent."""
    return (
        db.query(Attendance)
        .filter(Attendance.student_id == student_id)
        .order_by(desc(Attendance.year), desc(Attendance.month))
        .limit(limit)
        .all()
    )


# ════════════════════════════════════════════════════════
# ACADEMIC CRUD
# ════════════════════════════════════════════════════════

def create_or_update_academic(db: Session, student_db_id: int,
                               semester: str, year: int,
                               academic_data: dict) -> Academic:
    existing = db.query(Academic).filter(
        Academic.student_id == student_db_id,
        Academic.semester == semester,
        Academic.year == year
    ).first()

    if existing:
        for key, value in academic_data.items():
            setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    else:
        record = Academic(
            student_id=student_db_id,
            semester=semester,
            year=year,
            **academic_data
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record


def get_student_academics(db: Session, student_id: int,
                           limit: int = 6) -> List[Academic]:
    return (
        db.query(Academic)
        .filter(Academic.student_id == student_id)
        .order_by(desc(Academic.year), desc(Academic.semester))
        .limit(limit)
        .all()
    )


# ════════════════════════════════════════════════════════
# PREDICTION CRUD
# ════════════════════════════════════════════════════════

def create_prediction(db: Session, student_db_id: int,
                       prediction_data: dict) -> Prediction:
    prediction = Prediction(
        student_id=student_db_id,
        **prediction_data
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def get_latest_prediction(db: Session, student_id: int) -> Optional[Prediction]:
    return (
        db.query(Prediction)
        .filter(Prediction.student_id == student_id)
        .order_by(desc(Prediction.created_at))
        .first()
    )


def get_student_prediction_history(db: Session, student_id: int,
                                    limit: int = 10) -> List[Prediction]:
    return (
        db.query(Prediction)
        .filter(Prediction.student_id == student_id)
        .order_by(desc(Prediction.created_at))
        .limit(limit)
        .all()
    )


def get_high_risk_students(db: Session, threshold: float = 70.0) -> List:
    """Get students with latest prediction above threshold."""
    # Subquery: get latest prediction per student
    subq = (
        db.query(
            Prediction.student_id,
            func.max(Prediction.created_at).label("max_date")
        )
        .group_by(Prediction.student_id)
        .subquery()
    )

    results = (
        db.query(Student, Prediction)
        .join(Prediction, Student.id == Prediction.student_id)
        .join(subq, (Prediction.student_id == subq.c.student_id) &
                    (Prediction.created_at == subq.c.max_date))
        .filter(Prediction.risk_score >= threshold)
        .filter(Student.is_active == True)
        .order_by(desc(Prediction.risk_score))
        .all()
    )
    return results


def get_risk_distribution(db: Session) -> dict:
    """Get count of students in each risk category."""
    # Get latest prediction per student
    subq = (
        db.query(
            Prediction.student_id,
            func.max(Prediction.created_at).label("max_date")
        )
        .group_by(Prediction.student_id)
        .subquery()
    )

    predictions = (
        db.query(Prediction)
        .join(subq, (Prediction.student_id == subq.c.student_id) &
                    (Prediction.created_at == subq.c.max_date))
        .all()
    )

    distribution = {"low": 0, "medium": 0, "high": 0, "no_data": 0}
    for pred in predictions:
        if pred.risk_score <= 40:
            distribution["low"] += 1
        elif pred.risk_score <= 70:
            distribution["medium"] += 1
        else:
            distribution["high"] += 1

    # Count students without predictions
    students_with_predictions = set(p.student_id for p in predictions)
    all_student_ids = set(
        s.id for s in db.query(Student).filter(Student.is_active == True).all()
    )
    distribution["no_data"] = len(all_student_ids - students_with_predictions)

    return distribution


# ════════════════════════════════════════════════════════
# INTERVENTION CRUD
# ════════════════════════════════════════════════════════

def create_intervention(db: Session, student_db_id: int,
                         intervention_data: dict) -> Intervention:
    intervention = Intervention(
        student_id=student_db_id,
        **intervention_data
    )
    db.add(intervention)
    db.commit()
    db.refresh(intervention)
    return intervention


def get_student_interventions(db: Session, student_id: int) -> List[Intervention]:
    return (
        db.query(Intervention)
        .filter(Intervention.student_id == student_id)
        .order_by(desc(Intervention.created_at))
        .all()
    )


def update_intervention_status(db: Session, intervention_id: int,
                                status: str) -> Optional[Intervention]:
    intervention = db.query(Intervention).filter(
        Intervention.id == intervention_id
    ).first()
    if intervention:
        intervention.status = status
        db.commit()
        db.refresh(intervention)
    return intervention


# ════════════════════════════════════════════════════════
# FEEDBACK CRUD
# ════════════════════════════════════════════════════════

def create_feedback(db: Session, student_db_id: int,
                     feedback_data: dict) -> StudentFeedback:
    feedback = StudentFeedback(
        student_id=student_db_id,
        **feedback_data
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def get_student_feedback(db: Session, student_id: int,
                          limit: int = 10) -> List[StudentFeedback]:
    return (
        db.query(StudentFeedback)
        .filter(StudentFeedback.student_id == student_id)
        .order_by(desc(StudentFeedback.created_at))
        .limit(limit)
        .all()
    )


# ════════════════════════════════════════════════════════
# ALERT CRUD
# ════════════════════════════════════════════════════════

def create_alert(db: Session, student_db_id: int,
                  alert_data: dict) -> Alert:
    alert = Alert(
        student_id=student_db_id,
        **alert_data
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def get_recent_alerts(db: Session, limit: int = 50,
                       unresolved_only: bool = True) -> List[Alert]:
    query = db.query(Alert)
    if unresolved_only:
        query = query.filter(Alert.is_resolved == False)
    return query.order_by(desc(Alert.created_at)).limit(limit).all()


def get_student_alerts(db: Session, student_id: int) -> List[Alert]:
    return (
        db.query(Alert)
        .filter(Alert.student_id == student_id)
        .order_by(desc(Alert.created_at))
        .all()
    )


def resolve_alert(db: Session, alert_id: int) -> Optional[Alert]:
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        alert.is_resolved = True
        alert.resolved_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(alert)
    return alert
