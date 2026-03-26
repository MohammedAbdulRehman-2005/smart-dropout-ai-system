#!/usr/bin/env python3
# scripts/seed_db.py - Populate database with realistic sample data
# Run: python scripts/seed_db.py

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))

import random
import numpy as np
from datetime import datetime, timedelta

# Change to backend directory for imports
os.chdir(os.path.join(os.path.dirname(__file__), "../backend"))

from db.database import SessionLocal, create_tables
from db import crud
from ml.sentiment import get_sentiment_analyzer


def seed_database(db=None):
    """Seed database with 60 students and supporting data."""
    external_db = db is not None
    if db is None:
        create_tables()
        db = SessionLocal()

    random.seed(42)
    np.random.seed(42)

    analyzer = get_sentiment_analyzer()

    print("🌱 Seeding database with sample data...")

    # ─── Student Profiles ───────────────────────────────────────
    student_names = [
        "Arjun Sharma", "Priya Patel", "Rohit Kumar", "Anita Singh",
        "Mohammed Ali", "Deepika Reddy", "Sanjay Gupta", "Kavitha Nair",
        "Vikas Tiwari", "Sunita Devi", "Rahul Mehta", "Pooja Mishra",
        "Ajay Yadav", "Nisha Verma", "Ravi Shankar", "Meena Kumari",
        "Suresh Babu", "Geeta Rao", "Dinesh Joshi", "Lakshmi Pillai",
        "Amit Chauhan", "Rekha Srivastava", "Vijay Kumar", "Seema Agarwal",
        "Krishnan Menon", "Usha Deshpande", "Arun Nambiar", "Saranya Raja",
        "Balaji Iyer", "Chithra Murugan", "Dev Khanna", "Farzana Sheikh",
        "Gopal Das", "Hamida Begum", "Irfan Malik", "Jyoti Bhatt",
        "Kiran Desai", "Leela Swamy", "Mohan Prasad", "Nalini Bose",
        "Omkar Jain", "Parvati Hegde", "Quadir Hussain", "Radha Thakur",
        "Sunil Patil", "Tanuja Wagh", "Umesh Kulkarni", "Vandana More",
        "Wasim Khan", "Yamuna Pillai", "Zainab Ansari", "Abhishek Roy",
        "Bindiya Sen", "Chetan Pandey", "Divya Ghosh", "Ekta Trivedi",
        "Farhan Siddiqui", "Gita Banerjee", "Harish Nair", "Indira Menon",
    ]

    # Profile templates: (risk_profile, income, education, single_parent, disability)
    risk_profiles = {
        "high_risk": {
            "attendance_range": (45, 72),
            "score_range": (25, 48),
            "income": "low",
            "hw_completion": (30, 60),
            "sentiment_options": [
                "I hate school, it's pointless. I want to give up.",
                "Everything is too hard. I don't understand anything.",
                "I'm so stressed and tired all the time. I can't focus.",
                "Nobody helps me when I struggle. I feel hopeless.",
                "I miss school a lot because I have to work at home.",
            ],
        },
        "medium_risk": {
            "attendance_range": (72, 85),
            "score_range": (45, 65),
            "income": "medium",
            "hw_completion": (60, 80),
            "sentiment_options": [
                "School is okay but some subjects are really difficult.",
                "I'm struggling with math but trying my best.",
                "Sometimes I feel bored in class.",
                "I wish teachers would explain things more slowly.",
                "I am worried about my exams coming up.",
            ],
        },
        "low_risk": {
            "attendance_range": (88, 100),
            "score_range": (65, 95),
            "income": "medium",
            "hw_completion": (85, 100),
            "sentiment_options": [
                "I enjoy learning and school is fun for me!",
                "I love science class, it's my favorite.",
                "My teachers are very helpful and supportive.",
                "I feel confident about my upcoming exams.",
                "School helps me learn new things every day.",
            ],
        },
    }

    income_levels = ["low", "medium", "high"]
    education_levels = ["none", "primary", "secondary", "graduate"]
    genders = ["Male", "Female", "Other"]
    sections = ["A", "B", "C", "D"]

    created_students = []
    students_created = 0

    for i, name in enumerate(student_names):
        # Assign risk profile (30% high, 35% medium, 35% low)
        if i < 18:
            profile_name = "high_risk"
        elif i < 39:
            profile_name = "medium_risk"
        else:
            profile_name = "low_risk"

        profile = risk_profiles[profile_name]

        student_id = f"STU{1000 + i:04d}"
        grade = random.randint(8, 12)
        age = grade + 5 + random.randint(0, 2)

        # Check if exists
        if crud.get_student_by_student_id(db, student_id):
            created_students.append(crud.get_student_by_student_id(db, student_id))
            continue

        student_data = {
            "student_id": student_id,
            "full_name": name,
            "grade": grade,
            "age": age,
            "gender": random.choice(genders),
            "section": random.choice(sections),
            "family_income_level": profile.get("income", random.choice(income_levels)),
            "parents_education": random.choice(education_levels),
            "single_parent": random.random() < (0.4 if profile_name == "high_risk" else 0.15),
            "has_disability": random.random() < (0.2 if profile_name == "high_risk" else 0.05),
            "distance_from_school_km": round(random.uniform(0.5, 15.0), 1),
            "guardian_name": f"Parent of {name.split()[0]}",
            "guardian_phone": f"98{random.randint(10000000, 99999999)}",
            "guardian_email": f"parent_{student_id.lower()}@example.com",
        }

        student = crud.create_student(db, student_data)
        created_students.append(student)
        students_created += 1

        # ─── Attendance Records (12 months) ─────────────────
        att_low, att_high = profile["attendance_range"]
        months = [
            "2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06",
            "2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12"
        ]

        base_attendance = random.uniform(att_low, att_high)
        for month in months:
            # Add trend: high-risk students decline over time
            month_idx = months.index(month)
            if profile_name == "high_risk":
                att_pct = base_attendance - (month_idx * 0.8) + random.uniform(-5, 5)
            else:
                att_pct = base_attendance + random.uniform(-4, 4)
            att_pct = max(20.0, min(100.0, att_pct))

            total_days = 22
            present_days = int(att_pct / 100 * total_days)
            consecutive = max(0, int((1 - att_pct/100) * 10))

            crud.create_or_update_attendance(db, student.id, month, int(month[:4]), {
                "total_days": total_days,
                "present_days": present_days,
                "absent_days": total_days - present_days,
                "late_days": random.randint(0, 3 if profile_name != "low_risk" else 1),
                "attendance_pct": round(att_pct, 1),
                "consecutive_absences": consecutive,
            })

        # ─── Academic Records (4 semesters) ─────────────────
        score_low, score_high = profile["score_range"]
        semesters = [
            ("2023-S1", 2023), ("2023-S2", 2023),
            ("2024-S1", 2024), ("2024-S2", 2024)
        ]

        base_score = random.uniform(score_low, score_high)
        for sem, year in semesters:
            sem_idx = semesters.index((sem, year))
            if profile_name == "high_risk":
                score = base_score - (sem_idx * 2.5) + random.uniform(-8, 8)
            else:
                score = base_score + random.uniform(-8, 8)
            score = max(10.0, min(100.0, score))

            # Individual subject scores with variance
            subjects = {}
            for subj in ["math_score", "science_score", "english_score",
                          "social_score", "language_score"]:
                subjects[subj] = max(0.0, min(100.0, score + random.uniform(-15, 15)))

            avg_score = np.mean(list(subjects.values()))
            failed = sum(1 for s in subjects.values() if s < 35)
            gpa = round((avg_score / 100) * 4.0, 2)
            hw_low, hw_high = profile["hw_completion"]

            crud.create_or_update_academic(db, student.id, sem, year, {
                **subjects,
                "average_score": round(avg_score, 1),
                "gpa": gpa,
                "failed_subjects": failed,
                "homework_completion_pct": round(random.uniform(hw_low, hw_high), 1),
                "class_participation_score": round(
                    random.uniform(1.5, 3.0) if profile_name == "high_risk" else
                    random.uniform(2.5, 4.5), 1
                ),
            })

        # ─── Feedback Records ────────────────────────────────
        sentiments = profile["sentiment_options"]
        for _ in range(random.randint(1, 3)):
            text = random.choice(sentiments)
            analysis = analyzer.analyze(text)
            crud.create_feedback(db, student.id, {
                "feedback_text": text,
                "source": random.choice(["survey", "teacher_note", "self_report"]),
                "sentiment_score": analysis["sentiment_score"],
                "sentiment_label": analysis["sentiment_label"],
                "emotion_tags": analysis["emotion_tags"],
            })

    total_count = crud.get_total_student_count(db)
    print(f"✅ Database seeded: {students_created} new students created ({total_count} total)")

    if not external_db:
        db.close()

    return {
        "students_created": students_created,
        "total_students": total_count
    }


if __name__ == "__main__":
    print("🌱 Starting database seed...")
    result = seed_database()
    print(f"\n🎉 Done! {result}")
    print("\n📝 Next steps:")
    print("  1. Start backend: uvicorn main:app --reload")
    print("  2. Train model: POST http://localhost:8000/train-model")
    print("  3. View docs: http://localhost:8000/docs")
