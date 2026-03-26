# db/models.py - SQLAlchemy ORM models for all database tables
# Defines schema for students, attendance, academics, predictions, interventions

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, JSON, Enum
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    COUNSELOR = "counselor"


class RiskLevel(str, enum.Enum):
    LOW = "low"        # 0-40
    MEDIUM = "medium"  # 41-70
    HIGH = "high"      # 71-100


# ─────────────────────────────────────────────────────────
# USER TABLE - For authentication (teachers, admins, counselors)
# ─────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.TEACHER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ─────────────────────────────────────────────────────────
# STUDENT TABLE - Core student demographics
# ─────────────────────────────────────────────────────────
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String(50), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    grade = Column(Integer)                    # Grade/class (1-12)
    age = Column(Integer)
    gender = Column(String(20))
    section = Column(String(10))
    school_id = Column(String(50))
    
    # Socio-economic indicators
    family_income_level = Column(String(20))   # low / medium / high
    parents_education = Column(String(50))     # none / primary / secondary / graduate
    single_parent = Column(Boolean, default=False)
    has_disability = Column(Boolean, default=False)
    distance_from_school_km = Column(Float, default=0.0)
    
    # Contact info
    guardian_name = Column(String(255))
    guardian_phone = Column(String(20))
    guardian_email = Column(String(255))
    
    is_active = Column(Boolean, default=True)
    enrolled_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    attendance_records = relationship("Attendance", back_populates="student")
    academic_records = relationship("Academic", back_populates="student")
    predictions = relationship("Prediction", back_populates="student")
    interventions = relationship("Intervention", back_populates="student")
    feedback_records = relationship("StudentFeedback", back_populates="student")


# ─────────────────────────────────────────────────────────
# ATTENDANCE TABLE - Daily/weekly attendance data
# ─────────────────────────────────────────────────────────
class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    
    month = Column(String(20))                 # e.g. "2024-01"
    year = Column(Integer)
    
    total_days = Column(Integer, default=0)    # Total school days in period
    present_days = Column(Integer, default=0)  # Days student was present
    absent_days = Column(Integer, default=0)
    late_days = Column(Integer, default=0)
    
    attendance_pct = Column(Float, default=0.0)  # Computed: present/total * 100
    consecutive_absences = Column(Integer, default=0)  # Max streak of absences
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("Student", back_populates="attendance_records")


# ─────────────────────────────────────────────────────────
# ACADEMIC TABLE - Marks, grades, performance
# ─────────────────────────────────────────────────────────
class Academic(Base):
    __tablename__ = "academics"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    
    semester = Column(String(20))              # e.g. "2024-S1"
    year = Column(Integer)
    
    # Core subjects (0-100 marks)
    math_score = Column(Float, default=0.0)
    science_score = Column(Float, default=0.0)
    english_score = Column(Float, default=0.0)
    social_score = Column(Float, default=0.0)
    language_score = Column(Float, default=0.0)
    
    # Computed
    average_score = Column(Float, default=0.0)
    gpa = Column(Float, default=0.0)           # 0.0 - 4.0
    failed_subjects = Column(Integer, default=0)
    
    # Behavioral in academic context
    homework_completion_pct = Column(Float, default=0.0)
    class_participation_score = Column(Float, default=0.0)  # Teacher-rated 1-5
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("Student", back_populates="academic_records")


# ─────────────────────────────────────────────────────────
# PREDICTION TABLE - ML risk scores over time
# ─────────────────────────────────────────────────────────
class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    
    risk_score = Column(Float, nullable=False)       # 0-100
    risk_level = Column(Enum(RiskLevel))             # low/medium/high
    
    # SHAP explanation - stored as JSON
    shap_values = Column(JSON)                       # {"feature": shap_value, ...}
    top_risk_factors = Column(JSON)                  # [{"factor": "...", "impact": 0.3}, ...]
    
    # Trajectory forecast
    predicted_risk_30d = Column(Float)               # Forecasted risk in 30 days
    predicted_risk_60d = Column(Float)
    predicted_risk_90d = Column(Float)
    
    # Behavioral drift flag
    behavioral_drift_detected = Column(Boolean, default=False)
    drift_description = Column(Text)
    
    # Similar students (KNN)
    similar_student_ids = Column(JSON)               # [id1, id2, id3]
    
    model_version = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("Student", back_populates="predictions")


# ─────────────────────────────────────────────────────────
# INTERVENTION TABLE - Recommended & applied interventions
# ─────────────────────────────────────────────────────────
class Intervention(Base):
    __tablename__ = "interventions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    
    intervention_type = Column(String(100))          # academic / attendance / counseling / family
    title = Column(String(255))
    description = Column(Text)
    
    # AI-generated plan
    study_plan = Column(JSON)                        # Structured plan with tasks
    
    # Status tracking
    status = Column(String(50), default="pending")   # pending / active / completed
    assigned_to = Column(String(255))                # Teacher or counselor name
    
    # Impact simulation
    simulated_risk_before = Column(Float)
    simulated_risk_after = Column(Float)
    
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    student = relationship("Student", back_populates="interventions")


# ─────────────────────────────────────────────────────────
# STUDENT FEEDBACK TABLE - Free-text for NLP
# ─────────────────────────────────────────────────────────
class StudentFeedback(Base):
    __tablename__ = "student_feedback"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    
    feedback_text = Column(Text, nullable=False)
    source = Column(String(50))                      # survey / teacher_note / self_report
    
    # NLP Analysis results
    sentiment_score = Column(Float)                  # -1 (negative) to 1 (positive)
    sentiment_label = Column(String(20))             # positive / neutral / negative
    emotion_tags = Column(JSON)                      # ["frustrated", "anxious", ...]
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("Student", back_populates="feedback_records")


# ─────────────────────────────────────────────────────────
# ALERT TABLE - Automated notifications
# ─────────────────────────────────────────────────────────
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    
    alert_type = Column(String(50))                  # risk_increase / high_absence / low_grade
    severity = Column(String(20))                    # low / medium / high / critical
    title = Column(String(255))
    message = Column(Text)
    
    # Delivery tracking
    sent_to_teacher = Column(Boolean, default=False)
    sent_to_parent = Column(Boolean, default=False)
    sent_to_counselor = Column(Boolean, default=False)
    
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
