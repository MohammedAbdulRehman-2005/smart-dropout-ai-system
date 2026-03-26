# 🎓 Smart School Dropout Early Warning System

A production-ready, AI-powered platform to predict, explain, and prevent student dropouts using machine learning, explainable AI, and intelligent intervention planning.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                          │
│  Admin Dashboard │ Student Profile │ Counselor Panel │ Auth     │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/REST (JWT Auth)
┌───────────────────────────▼─────────────────────────────────────┐
│                    BACKEND (FastAPI)                              │
│  /upload-data  /train-model  /predict-risk  /get-explanation     │
│  /get-recommendations  /student/{id}  /alerts  /interventions    │
└──────────┬────────────────┬────────────────────┬────────────────┘
           │                │                    │
┌──────────▼──────┐ ┌───────▼──────┐ ┌──────────▼──────────────┐
│   ML Pipeline   │ │   Database   │ │     AI Agent System      │
│  XGBoost Model  │ │   SQLite/PG  │ │  Notification Agent      │
│  SHAP Explain.  │ │  students    │ │  Study Plan Generator    │
│  KNN Matching   │ │  attendance  │ │  Emotional Support Bot   │
│  NLP Sentiment  │ │  academics   │ │  Alert Dispatcher        │
└─────────────────┘ │  predictions │ └──────────────────────────┘
                    │  interventions│
                    └───────────────┘
```

## 📁 Folder Structure

```
smart-dropout-system/
├── backend/
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # Configuration & env vars
│   ├── requirements.txt
│   ├── api/
│   │   ├── auth.py                # JWT authentication
│   │   ├── students.py            # Student CRUD endpoints
│   │   ├── predictions.py         # Risk prediction endpoints
│   │   ├── interventions.py       # Intervention endpoints
│   │   └── admin.py               # Admin endpoints
│   ├── ml/
│   │   ├── pipeline.py            # Full ML pipeline
│   │   ├── model.py               # XGBoost model
│   │   ├── explainer.py           # SHAP explainability
│   │   ├── knn_matcher.py         # KNN similar students
│   │   ├── sentiment.py           # NLP sentiment analysis
│   │   └── features.py            # Feature engineering
│   ├── db/
│   │   ├── database.py            # DB connection & session
│   │   ├── models.py              # SQLAlchemy ORM models
│   │   └── crud.py                # DB CRUD operations
│   ├── agents/
│   │   ├── notification_agent.py  # Alert system
│   │   ├── study_plan_agent.py    # AI study plan generator
│   │   └── chatbot_agent.py       # Emotional support chatbot
│   └── utils/
│       ├── data_processor.py      # CSV/Excel ingestion
│       └── validators.py          # Input validation
│
├── frontend/
│   ├── package.json
│   ├── tailwind.config.js
│   └── src/
│       ├── App.jsx
│       ├── index.jsx
│       ├── api/
│       │   └── client.js          # Axios API client
│       ├── hooks/
│       │   ├── useAuth.js
│       │   └── useStudents.js
│       ├── pages/
│       │   ├── Login.jsx
│       │   ├── AdminDashboard.jsx
│       │   ├── StudentProfile.jsx
│       │   └── CounselorPanel.jsx
│       ├── components/
│       │   ├── shared/            # Shared UI components
│       │   ├── admin/             # Admin-specific components
│       │   ├── student/           # Student profile components
│       │   └── counselor/         # Counselor panel components
│       └── utils/
│           └── riskHelpers.js     # Risk color coding utils
│
├── data/
│   ├── sample_students.csv        # Sample dataset
│   └── sample_attendance.csv
│
├── scripts/
│   ├── seed_db.py                 # Database seeder
│   └── generate_sample_data.py   # Sample data generator
│
└── docker-compose.yml
```

## 🚀 Quick Start

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

### 2. Database + Sample Data
```bash
cd scripts
python generate_sample_data.py  # Creates data/sample_students.csv
python seed_db.py                # Seeds SQLite database
```

### 3. Train the Model
```bash
curl -X POST http://localhost:8000/train-model
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm start  # Runs on http://localhost:3000
```

### Default Login Credentials
| Role      | Email                    | Password  |
|-----------|--------------------------|-----------|
| Admin     | admin@school.edu         | admin123  |
| Teacher   | teacher@school.edu       | teacher123|
| Counselor | counselor@school.edu     | counsel123|

## 🎯 Risk Color Coding
- 🟢 **Green (0–40)**: Low risk
- 🟡 **Yellow (41–70)**: Medium risk  
- 🔴 **Red (71–100)**: High risk — immediate intervention needed

## 📊 Sample Dataset Format
See `data/sample_students.csv` for expected column format.
