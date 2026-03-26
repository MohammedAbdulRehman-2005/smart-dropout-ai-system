# main.py - FastAPI Application Entry Point
# Assembles all routes, middleware, and startup logic

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import os

from config import settings
from db.database import get_db, create_tables
from db import crud
from api.auth import router as auth_router, get_current_user, require_any_role, require_admin
from ml.pipeline import get_pipeline
from ml.model import get_risk_level, get_risk_color
from utils.data_processor import DataProcessor
from agents.study_plan_agent import (
    get_study_plan_agent, get_notification_agent, get_chatbot
)

# ─────────────────────────────────────────────────────────
# APP CONFIGURATION
# ─────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered platform to predict and prevent student dropouts",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS - Allow frontend on localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router
app.include_router(auth_router)

# Initialize data processor
data_processor = DataProcessor()


# ─────────────────────────────────────────────────────────
# STARTUP: Create tables and seed default users
# ─────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    """Initialize database and create default users on first run."""
    create_tables()
    
    # Create default users if they don't exist
    from db.database import SessionLocal
    from api.auth import get_password_hash
    
    db = SessionLocal()
    try:
        default_users = [
            {"email": "admin@school.edu", "password": "admin123",
             "full_name": "System Administrator", "role": "admin"},
            {"email": "teacher@school.edu", "password": "teacher123",
             "full_name": "Mrs. Priya Sharma", "role": "teacher"},
            {"email": "counselor@school.edu", "password": "counsel123",
             "full_name": "Mr. Rahul Mehta", "role": "counselor"},
        ]
        
        for user_data in default_users:
            if not crud.get_user_by_email(db, user_data["email"]):
                crud.create_user(
                    db,
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    full_name=user_data["full_name"],
                    role=user_data["role"]
                )
                logger.info(f"✅ Created default user: {user_data['email']}")
    finally:
        db.close()
    
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started!")


# ─────────────────────────────────────────────────────────
# PYDANTIC SCHEMAS FOR REQUESTS/RESPONSES
# ─────────────────────────────────────────────────────────
class PredictRequest(BaseModel):
    student_id: int

class FeedbackRequest(BaseModel):
    student_id: int
    feedback_text: str
    source: str = "survey"

class InterventionStatusUpdate(BaseModel):
    status: str

class ChatRequest(BaseModel):
    message: str

class BulkPredictRequest(BaseModel):
    run_all: bool = True


# ═══════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════
@app.get("/", tags=["Health"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    pipeline = get_pipeline()
    return {
        "status": "healthy",
        "database": "connected",
        "model_trained": pipeline.model.is_trained,
        "model_version": pipeline.model.model_version,
    }


# ═══════════════════════════════════════════════════════════
# DATA UPLOAD ENDPOINTS
# ═══════════════════════════════════════════════════════════
@app.post("/upload-data", tags=["Data"])
async def upload_data(
    file: UploadFile = File(...),
    data_type: str = "auto",    # students / attendance / academics / feedback / auto
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role)
):
    """
    Upload CSV or Excel files to populate the database.
    
    data_type options:
    - students: Student demographic data
    - attendance: Monthly attendance records  
    - academics: Semester academic records
    - feedback: Student feedback text
    - auto: Auto-detect from column names
    """
    if not file.filename.endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(400, "Only CSV and Excel files are supported")

    content = await file.read()
    
    try:
        df = data_processor.process_file(content, file.filename)
        
        # Auto-detect if needed
        if data_type == "auto":
            data_type = data_processor.detect_combined_format(df)
        
        # Route to appropriate ingestion function
        if data_type == "students":
            result = data_processor.ingest_students(df, db)
        elif data_type == "attendance":
            result = data_processor.ingest_attendance(df, db)
        elif data_type == "academics":
            result = data_processor.ingest_academics(df, db)
        elif data_type == "feedback":
            result = data_processor.ingest_feedback(df, db)
        else:
            raise HTTPException(400, f"Unknown data type: {data_type}")
        
        return {
            "status": "success",
            "filename": file.filename,
            "data_type": data_type,
            "rows_processed": len(df),
            "result": result
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(500, f"Processing failed: {str(e)}")


# ═══════════════════════════════════════════════════════════
# ML TRAINING ENDPOINT
# ═══════════════════════════════════════════════════════════
@app.post("/train-model", tags=["ML"])
async def train_model(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    """
    Train the XGBoost dropout prediction model on current database data.
    
    Requires admin role. Training takes 10-60 seconds depending on data size.
    """
    pipeline = get_pipeline()
    
    student_count = crud.get_total_student_count(db)
    if student_count < 10:
        raise HTTPException(
            400,
            f"Need at least 10 students to train. Currently have {student_count}. "
            "Upload student data first or run the seed script."
        )
    
    try:
        metrics = pipeline.train_from_db(db)
        return {
            "status": "success",
            "message": "Model trained successfully",
            "metrics": metrics,
            "training_samples": student_count
        }
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise HTTPException(500, f"Training failed: {str(e)}")


# ═══════════════════════════════════════════════════════════
# PREDICTION ENDPOINTS
# ═══════════════════════════════════════════════════════════
@app.post("/predict-risk", tags=["Predictions"])
async def predict_risk(
    request: PredictRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role)
):
    """
    Predict dropout risk for a single student.
    
    Returns risk score (0-100), SHAP explanation, trajectory forecast,
    behavioral drift detection, and similar student matches.
    """
    pipeline = get_pipeline()
    
    if not pipeline.model.is_trained:
        raise HTTPException(
            400,
            "Model not trained yet. Call POST /train-model first (admin required)."
        )
    
    student = crud.get_student_by_id(db, request.student_id)
    if not student:
        raise HTTPException(404, f"Student {request.student_id} not found")
    
    try:
        result = pipeline.predict_for_student(db, request.student_id)
        
        agent = get_study_plan_agent()
        top_factors = result["explanation"].get("top_factors", [])
        
        plan = agent.generate_intervention_plan(
            student={"full_name": result["student_name"], "id": result["student_id"]},
            risk_score=result["risk_score"],
            top_factors=top_factors,
            current_features=result["features_used"]
        )
        
        r_score = int(result["risk_score"])
        if r_score <= 40:
            risk_level = "LOW"
        elif r_score <= 70:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
            
        return {
            "risk_score": r_score,
            "risk_level": risk_level,
            "top_factors": top_factors,
            "recommendations": {
                "immediate": plan.get("immediate_actions", []),
                "short_term": plan.get("short_term_goals", [])
            },
            "simulated_impact": plan.get("simulated_impact", {})
        }
    except Exception as e:
        logger.error(f"Prediction error for student {request.student_id}: {e}")
        raise HTTPException(500, f"Prediction failed: {str(e)}")


@app.post("/predict-all", tags=["Predictions"])
async def predict_all_students(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    """Run risk predictions for all active students (batch operation)."""
    pipeline = get_pipeline()
    
    if not pipeline.model.is_trained:
        raise HTTPException(400, "Model not trained yet.")
    
    results = pipeline.predict_all_students(db)
    return {
        "status": "complete",
        "total_predicted": len(results),
        "results": results
    }


# ═══════════════════════════════════════════════════════════
# EXPLANATION ENDPOINT
# ═══════════════════════════════════════════════════════════
@app.get("/get-explanation/{student_id}", tags=["Explainability"])
async def get_explanation(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role)
):
    """
    Get the latest SHAP explanation for a student's risk score.
    Returns top 3 risk factors with recommendations.
    """
    prediction = crud.get_latest_prediction(db, student_id)
    if not prediction:
        raise HTTPException(404, "No prediction found for this student. Run /predict-risk first.")
    
    student = crud.get_student_by_id(db, student_id)
    
    return {
        "student_id": student_id,
        "student_name": student.full_name if student else "Unknown",
        "risk_score": prediction.risk_score,
        "risk_level": prediction.risk_level,
        "risk_color": get_risk_color(prediction.risk_score),
        "top_factors": prediction.top_risk_factors or [],
        "shap_values": prediction.shap_values or {},
        "drift_detected": prediction.behavioral_drift_detected,
        "drift_description": prediction.drift_description,
        "trajectory": {
            "risk_30d": prediction.predicted_risk_30d,
            "risk_60d": prediction.predicted_risk_60d,
            "risk_90d": prediction.predicted_risk_90d,
        },
        "predicted_at": prediction.created_at.isoformat() if prediction.created_at else None
    }


# ═══════════════════════════════════════════════════════════
# RECOMMENDATIONS ENDPOINT
# ═══════════════════════════════════════════════════════════
@app.get("/get-recommendations/{student_id}", tags=["Interventions"])
async def get_recommendations(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role)
):
    """
    Generate AI-powered intervention plan and study recommendations.
    """
    student = crud.get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(404, "Student not found")
    
    prediction = crud.get_latest_prediction(db, student_id)
    if not prediction:
        raise HTTPException(
            400, "No prediction available. Run /predict-risk first."
        )
    
    agent = get_study_plan_agent()
    
    student_dict = {
        "id": student.id,
        "full_name": student.full_name,
        "grade": student.grade,
        "age": student.age,
    }
    
    plan = agent.generate_intervention_plan(
        student=student_dict,
        risk_score=prediction.risk_score,
        top_factors=prediction.top_risk_factors or [],
        current_features={}
    )
    
    # Store intervention in DB
    crud.create_intervention(db, student_id, {
        "intervention_type": plan["intervention_type"],
        "title": f"AI Intervention Plan - {student.full_name}",
        "description": f"Auto-generated plan based on risk score {prediction.risk_score}/100",
        "study_plan": plan,
        "status": "pending",
        "simulated_risk_before": plan["simulated_impact"]["current_risk"],
        "simulated_risk_after": plan["simulated_impact"]["projected_risk_after_intervention"],
    })
    
    return plan


# ═══════════════════════════════════════════════════════════
# STUDENT ENDPOINTS
# ═══════════════════════════════════════════════════════════
@app.get("/student/{student_id}", tags=["Students"])
async def get_student_profile(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role)
):
    """Get complete student profile with latest risk data."""
    student = crud.get_student_by_id(db, student_id)
    if not student:
        raise HTTPException(404, f"Student {student_id} not found")
    
    # Fetch all related data
    attendance = crud.get_student_attendance(db, student_id)
    academics = crud.get_student_academics(db, student_id)
    predictions = crud.get_student_prediction_history(db, student_id, limit=10)
    interventions = crud.get_student_interventions(db, student_id)
    feedback = crud.get_student_feedback(db, student_id)
    alerts = crud.get_student_alerts(db, student_id)
    
    latest_prediction = predictions[0] if predictions else None
    
    return {
        "student": {
            "id": student.id,
            "student_id": student.student_id,
            "full_name": student.full_name,
            "grade": student.grade,
            "age": student.age,
            "gender": student.gender,
            "section": student.section,
            "family_income_level": student.family_income_level,
            "parents_education": student.parents_education,
            "single_parent": student.single_parent,
            "has_disability": student.has_disability,
            "distance_from_school_km": student.distance_from_school_km,
            "guardian_name": student.guardian_name,
            "guardian_phone": student.guardian_phone,
        },
        "current_risk": {
            "score": latest_prediction.risk_score if latest_prediction else None,
            "level": latest_prediction.risk_level if latest_prediction else None,
            "color": get_risk_color(latest_prediction.risk_score) if latest_prediction else "#gray",
            "top_factors": latest_prediction.top_risk_factors if latest_prediction else [],
            "drift_detected": latest_prediction.behavioral_drift_detected if latest_prediction else False,
        },
        "attendance": [
            {
                "month": a.month,
                "year": a.year,
                "attendance_pct": a.attendance_pct,
                "present_days": a.present_days,
                "total_days": a.total_days,
                "consecutive_absences": a.consecutive_absences,
            }
            for a in attendance
        ],
        "academics": [
            {
                "semester": ac.semester,
                "year": ac.year,
                "average_score": ac.average_score,
                "gpa": ac.gpa,
                "failed_subjects": ac.failed_subjects,
                "math_score": ac.math_score,
                "science_score": ac.science_score,
                "english_score": ac.english_score,
            }
            for ac in academics
        ],
        "risk_history": [
            {
                "risk_score": p.risk_score,
                "risk_level": p.risk_level,
                "predicted_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in predictions
        ],
        "trajectory": {
            "risk_30d": latest_prediction.predicted_risk_30d if latest_prediction else None,
            "risk_60d": latest_prediction.predicted_risk_60d if latest_prediction else None,
            "risk_90d": latest_prediction.predicted_risk_90d if latest_prediction else None,
        },
        "interventions": [
            {
                "id": i.id,
                "type": i.intervention_type,
                "title": i.title,
                "status": i.status,
                "created_at": i.created_at.isoformat() if i.created_at else None,
                "simulated_risk_before": i.simulated_risk_before,
                "simulated_risk_after": i.simulated_risk_after,
            }
            for i in interventions
        ],
        "feedback": [
            {
                "text": f.feedback_text[:200],  # Truncate for privacy
                "sentiment_label": f.sentiment_label,
                "sentiment_score": f.sentiment_score,
                "emotion_tags": f.emotion_tags,
                "created_at": f.created_at.isoformat() if f.created_at else None,
            }
            for f in feedback
        ],
        "alerts": [
            {
                "id": a.id,
                "type": a.alert_type,
                "severity": a.severity,
                "title": a.title,
                "message": a.message,
                "is_resolved": a.is_resolved,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alerts
        ]
    }


@app.get("/students", tags=["Students"])
async def list_students(
    skip: int = 0,
    limit: int = 50,
    grade: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role)
):
    """List students with optional grade filter."""
    students = crud.get_students(db, skip=skip, limit=limit, grade=grade)
    
    result = []
    for student in students:
        prediction = crud.get_latest_prediction(db, student.id)
        result.append({
            "id": student.id,
            "student_id": student.student_id,
            "full_name": student.full_name,
            "grade": student.grade,
            "section": student.section,
            "age": student.age,
            "risk_score": prediction.risk_score if prediction else None,
            "risk_level": prediction.risk_level if prediction else "no_data",
            "risk_color": get_risk_color(prediction.risk_score) if prediction else "#9ca3af",
        })
    
    return {"students": result, "total": len(result), "skip": skip, "limit": limit}


@app.post("/students/{student_id}/feedback", tags=["Students"])
async def add_feedback(
    student_id: int,
    request: FeedbackRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role)
):
    """Add student feedback with automatic NLP sentiment analysis."""
    from ml.sentiment import get_sentiment_analyzer
    analyzer = get_sentiment_analyzer()
    analysis = analyzer.analyze(request.feedback_text)
    
    feedback = crud.create_feedback(db, student_id, {
        "feedback_text": request.feedback_text,
        "source": request.source,
        "sentiment_score": analysis["sentiment_score"],
        "sentiment_label": analysis["sentiment_label"],
        "emotion_tags": analysis["emotion_tags"],
    })
    
    return {
        "id": feedback.id,
        "sentiment": analysis,
        "message": "Feedback recorded and analyzed"
    }


# ═══════════════════════════════════════════════════════════
# ADMIN DASHBOARD ENDPOINTS
# ═══════════════════════════════════════════════════════════
@app.get("/admin/dashboard", tags=["Admin"])
async def admin_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role)
):
    """Get summary statistics for admin dashboard."""
    total_students = crud.get_total_student_count(db)
    risk_distribution = crud.get_risk_distribution(db)
    high_risk_list = crud.get_high_risk_students(db, threshold=70.0)
    recent_alerts = crud.get_recent_alerts(db, limit=10)
    
    pipeline = get_pipeline()
    
    return {
        "summary": {
            "total_students": total_students,
            "model_trained": pipeline.model.is_trained,
            "high_risk_count": risk_distribution.get("high", 0),
            "medium_risk_count": risk_distribution.get("medium", 0),
            "low_risk_count": risk_distribution.get("low", 0),
            "no_data_count": risk_distribution.get("no_data", 0),
        },
        "risk_distribution": risk_distribution,
        "high_risk_students": [
            {
                "id": student.id,
                "student_id": student.student_id,
                "full_name": student.full_name,
                "grade": student.grade,
                "risk_score": prediction.risk_score,
                "risk_color": get_risk_color(prediction.risk_score),
            }
            for student, prediction in high_risk_list[:10]
        ],
        "recent_alerts": [
            {
                "id": a.id,
                "student_id": a.student_id,
                "title": a.title,
                "severity": a.severity,
                "is_resolved": a.is_resolved,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in recent_alerts
        ]
    }


# ═══════════════════════════════════════════════════════════
# ALERT ENDPOINTS
# ═══════════════════════════════════════════════════════════
@app.get("/alerts", tags=["Alerts"])
async def get_alerts(
    unresolved_only: bool = True,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role)
):
    """Get recent alerts (optionally filtered to unresolved only)."""
    alerts = crud.get_recent_alerts(db, limit=50, unresolved_only=unresolved_only)
    return {
        "alerts": [
            {
                "id": a.id,
                "student_id": a.student_id,
                "type": a.alert_type,
                "severity": a.severity,
                "title": a.title,
                "message": a.message,
                "is_resolved": a.is_resolved,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in alerts
        ],
        "count": len(alerts)
    }


@app.post("/alerts/{alert_id}/resolve", tags=["Alerts"])
async def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role)
):
    """Mark an alert as resolved."""
    alert = crud.resolve_alert(db, alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found")
    return {"status": "resolved", "alert_id": alert_id}


# ═══════════════════════════════════════════════════════════
# INTERVENTION ENDPOINTS
# ═══════════════════════════════════════════════════════════
@app.patch("/interventions/{intervention_id}", tags=["Interventions"])
async def update_intervention(
    intervention_id: int,
    update: InterventionStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_any_role)
):
    """Update intervention status (pending/active/completed)."""
    valid_statuses = ["pending", "active", "completed"]
    if update.status not in valid_statuses:
        raise HTTPException(400, f"Status must be one of: {valid_statuses}")
    
    intervention = crud.update_intervention_status(db, intervention_id, update.status)
    if not intervention:
        raise HTTPException(404, "Intervention not found")
    return {"status": "updated", "intervention_id": intervention_id, "new_status": update.status}


# ═══════════════════════════════════════════════════════════
# CHATBOT ENDPOINT
# ═══════════════════════════════════════════════════════════
@app.post("/chatbot", tags=["AI Agent"])
async def chat(request: ChatRequest):
    """
    Emotional support chatbot for students.
    Rule-based with LLM integration hooks.
    """
    chatbot = get_chatbot()
    response = chatbot.get_response(request.message)
    return {
        "response": response,
        "type": "support"
    }


@app.get("/chatbot/greeting", tags=["AI Agent"])
async def chatbot_greeting():
    """Get the chatbot's initial greeting message."""
    chatbot = get_chatbot()
    return {"message": chatbot.get_initial_message()}


# ═══════════════════════════════════════════════════════════
# SEED ENDPOINT (for quick demo setup)
# ═══════════════════════════════════════════════════════════
@app.post("/seed-demo-data", tags=["Setup"])
async def seed_demo_data(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):
    """
    Seed database with sample data for demonstration.
    Generates 50 students with realistic randomized data.
    """
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../scripts")
    
    try:
        from scripts.seed_db import seed_database
        result = seed_database(db)
        return {"status": "success", "seeded": result}
    except ImportError:
        # Inline basic seeding
        from scripts_inline import quick_seed
        result = quick_seed(db)
        return {"status": "success", "seeded": result}
    except Exception as e:
        raise HTTPException(500, f"Seeding failed: {str(e)}")
