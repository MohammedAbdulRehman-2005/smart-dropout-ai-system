# agents/study_plan_agent.py - AI-powered intervention and study plan generator
# Generates personalized study plans, intervention strategies, and emotional support

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# STUDY PLAN AGENT
# Generates personalized academic improvement plans
# ═══════════════════════════════════════════════════════════

class StudyPlanAgent:
    """
    Generates AI-powered personalized study plans and interventions
    based on student risk factors and performance data.
    """

    def generate_intervention_plan(
        self,
        student: Dict,
        risk_score: float,
        top_factors: List[Dict],
        current_features: Dict
    ) -> Dict:
        """
        Generate a comprehensive intervention plan.
        
        Returns structured plan with:
        - Immediate actions (this week)
        - Short-term goals (1 month)
        - Long-term goals (1 semester)
        - Resource recommendations
        """
        plan = {
            "generated_at": datetime.utcnow().isoformat(),
            "student_name": student.get("full_name", "Student"),
            "risk_score": risk_score,
            "urgency": self._get_urgency(risk_score),
            "intervention_type": self._determine_intervention_type(top_factors),
            "immediate_actions": [],
            "short_term_goals": [],
            "long_term_goals": [],
            "resources": [],
            "weekly_schedule": {},
            "simulated_impact": {}
        }

        # Generate actions based on top risk factors
        for factor in top_factors[:3]:
            feature = factor.get("feature", "")
            actions = self._get_actions_for_factor(feature, current_features)
            plan["immediate_actions"].extend(actions.get("immediate", []))
            plan["short_term_goals"].extend(actions.get("short_term", []))
            plan["resources"].extend(actions.get("resources", []))

        # Remove duplicates
        plan["immediate_actions"] = list(dict.fromkeys(plan["immediate_actions"]))[:5]
        plan["short_term_goals"] = list(dict.fromkeys(plan["short_term_goals"]))[:4]
        plan["resources"] = list(dict.fromkeys(plan["resources"]))[:6]

        # Long-term goals based on risk level
        plan["long_term_goals"] = self._get_long_term_goals(risk_score)

        # Generate weekly schedule
        plan["weekly_schedule"] = self._generate_weekly_schedule(top_factors, current_features)

        # Simulate impact of intervention
        plan["simulated_impact"] = self._simulate_risk_reduction(risk_score, top_factors)

        return plan

    def _get_urgency(self, risk_score: float) -> str:
        if risk_score > 85:
            return "critical"
        elif risk_score > 70:
            return "high"
        elif risk_score > 50:
            return "medium"
        else:
            return "low"

    def _determine_intervention_type(self, top_factors: List[Dict]) -> str:
        """Determine the primary intervention category."""
        factor_features = [f.get("feature", "") for f in top_factors]

        if "avg_attendance_pct" in factor_features or "max_consecutive_absences" in factor_features:
            return "attendance_focused"
        elif "avg_score" in factor_features or "failed_subjects_total" in factor_features:
            return "academic_focused"
        elif "avg_sentiment_score" in factor_features or "negative_feedback_count" in factor_features:
            return "emotional_support"
        elif "family_income_encoded" in factor_features or "is_single_parent" in factor_features:
            return "family_support"
        else:
            return "comprehensive"

    def _get_actions_for_factor(self, feature: str, features: Dict) -> Dict:
        """Get specific actions for a given risk factor."""
        action_map = {
            "avg_attendance_pct": {
                "immediate": [
                    "📞 Call parents/guardian today to discuss attendance",
                    "🏥 Schedule health check-up if illness is suspected",
                    "🚌 Explore transportation solutions",
                ],
                "short_term": [
                    "Set up weekly attendance monitoring check-ins",
                    "Create attendance improvement contract signed by student & parent",
                    "Assign attendance buddy/mentor",
                ],
                "resources": [
                    "School counselor appointment",
                    "Transportation assistance program",
                    "After-school support program"
                ]
            },
            "avg_score": {
                "immediate": [
                    "📚 Assign peer tutor for weakest subject immediately",
                    "🎯 Identify specific knowledge gaps through diagnostic test",
                    "👩‍🏫 Schedule teacher one-on-one sessions",
                ],
                "short_term": [
                    "Develop weekly study schedule with teacher",
                    "Enroll in remedial/support classes for failing subjects",
                    "Weekly progress tests to track improvement",
                ],
                "resources": [
                    "Free online resources: Khan Academy",
                    "School library study materials",
                    "Peer tutoring program"
                ]
            },
            "avg_sentiment_score": {
                "immediate": [
                    "💬 Schedule counselor session within 48 hours",
                    "🤝 Connect with school social worker",
                    "🧘 Introduce stress management techniques",
                ],
                "short_term": [
                    "Weekly check-in with school counselor",
                    "Join student support group",
                    "Mindfulness and wellbeing activities",
                ],
                "resources": [
                    "School counseling services",
                    "Student wellness program",
                    "Mental health helpline information"
                ]
            },
            "family_income_encoded": {
                "immediate": [
                    "💰 Apply for school financial assistance program",
                    "📋 Connect with school social worker for support programs",
                ],
                "short_term": [
                    "Explore scholarship opportunities",
                    "Connect with community support programs",
                    "Reduce financial barriers (books, materials)",
                ],
                "resources": [
                    "School financial aid office",
                    "Government student support schemes",
                    "NGO partnerships for student support"
                ]
            },
            "homework_completion_pct": {
                "immediate": [
                    "📖 Assess if student has quiet study space at home",
                    "⏰ Create structured homework schedule",
                ],
                "short_term": [
                    "After-school homework club enrollment",
                    "Weekly homework completion tracking",
                ],
                "resources": [
                    "After-school homework support program",
                    "Library study hours"
                ]
            },
        }

        return action_map.get(feature, {
            "immediate": [f"Address {feature.replace('_', ' ')} with targeted support"],
            "short_term": ["Monitor and follow up monthly"],
            "resources": ["General student support services"]
        })

    def _get_long_term_goals(self, risk_score: float) -> List[str]:
        """Generate semester-long improvement goals."""
        if risk_score > 70:
            return [
                "🎯 Achieve 85% attendance rate by end of semester",
                "📈 Improve average score by 15+ points",
                "😊 Report positive sentiment in monthly feedback",
                "🏆 Complete all subjects without failure",
                "👥 Establish positive peer relationships"
            ]
        elif risk_score > 40:
            return [
                "🎯 Maintain 90%+ attendance consistently",
                "📈 Improve GPA by 0.5 points",
                "📚 Complete 95%+ homework assignments",
                "👥 Increase classroom participation"
            ]
        else:
            return [
                "🎯 Continue excellent attendance (95%+)",
                "🏆 Explore advanced coursework opportunities",
                "👥 Mentor other students"
            ]

    def _generate_weekly_schedule(
        self, top_factors: List[Dict], features: Dict
    ) -> Dict:
        """Generate a sample weekly study/support schedule."""
        schedule = {}
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

        # Base schedule
        base_activities = [
            "Self-study: 1 hour (focus on weakest subject)",
            "Peer tutoring session: 45 mins",
            "Counselor check-in: 20 mins",
            "Extra practice problems: 30 mins",
            "Weekly progress review with teacher: 30 mins"
        ]

        for i, day in enumerate(days):
            activities = [base_activities[i]]
            # Add attendance check for attendance-risk students
            if features.get("avg_attendance_pct", 100) < 75:
                activities.append("Morning check-in with homeroom teacher")
            schedule[day] = activities

        # Weekend
        schedule["Saturday"] = ["Weekend revision: 1.5 hours", "Rest and recreation"]
        schedule["Sunday"] = ["Weekly reflection + goal setting for next week"]

        return schedule

    def _simulate_risk_reduction(
        self, current_risk: float, top_factors: List[Dict]
    ) -> Dict:
        """
        Simulate the expected risk reduction after implementing the plan.
        Returns before/after comparison.
        """
        # Estimate reduction per intervention
        estimated_reduction = 0.0

        for factor in top_factors:
            impact = factor.get("shap_value", 0)
            if factor.get("direction") == "increasing_risk":
                # Full intervention addresses ~70% of each factor's impact
                estimated_reduction += abs(impact) * 70 * 0.7

        # Apply diminishing returns for very high reductions
        estimated_reduction = min(estimated_reduction, 35.0)

        projected_risk = max(current_risk - estimated_reduction, 5.0)

        return {
            "current_risk": round(current_risk, 1),
            "projected_risk_after_intervention": round(projected_risk, 1),
            "estimated_reduction": round(estimated_reduction, 1),
            "confidence": "moderate",
            "timeframe": "4-6 weeks with consistent intervention",
            "success_indicators": [
                "Attendance improves by 10%+",
                "No failed subjects next assessment",
                "Positive sentiment in next feedback survey",
                "Student reports feeling supported"
            ]
        }


# ═══════════════════════════════════════════════════════════
# NOTIFICATION AGENT
# Manages automated alerts to teachers, parents, counselors
# ═══════════════════════════════════════════════════════════

class NotificationAgent:
    """
    Manages and dispatches automated alerts for at-risk students.
    
    In production: integrate with email (SMTP), SMS (Twilio), 
    or push notification services.
    """

    def __init__(self):
        self.notification_log = []  # In-memory log (replace with DB in production)

    def send_high_risk_alert(
        self,
        student: Dict,
        risk_score: float,
        top_factors: List[Dict],
        recipients: List[str]
    ) -> Dict:
        """Send alert for high-risk student detection."""
        factor_text = "\n".join([
            f"  • {f['label']}: {f['direction'].replace('_', ' ')}"
            for f in top_factors[:3]
        ])

        message = {
            "type": "high_risk_alert",
            "severity": "critical" if risk_score > 85 else "high",
            "subject": f"⚠️ Urgent: {student['full_name']} needs immediate attention",
            "body": (
                f"Dear Educator,\n\n"
                f"Student {student['full_name']} (Grade {student.get('grade', 'N/A')}) "
                f"has been flagged with a HIGH dropout risk score of {risk_score}/100.\n\n"
                f"Key Risk Factors:\n{factor_text}\n\n"
                f"Please take immediate action and log your intervention in the system.\n\n"
                f"View full profile: [Dashboard Link]\n\n"
                f"- Smart EWS Automated Alert System"
            ),
            "recipients": recipients,
            "student_id": student.get("id"),
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Log notification (in production: send via SMTP/API)
        self.notification_log.append(message)
        logger.info(f"📧 Alert sent for {student['full_name']} (risk: {risk_score}) to {recipients}")

        return {"status": "sent", "message": message}

    def send_attendance_alert(
        self, student: Dict, consecutive_absences: int
    ) -> Dict:
        """Alert when student misses too many consecutive days."""
        message = {
            "type": "attendance_alert",
            "severity": "high" if consecutive_absences >= 5 else "medium",
            "subject": f"📅 Attendance Alert: {student['full_name']} absent {consecutive_absences} days",
            "body": (
                f"Student {student['full_name']} has been absent for "
                f"{consecutive_absences} consecutive school days. "
                f"Please contact the family."
            ),
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.notification_log.append(message)
        return {"status": "sent", "message": message}

    def get_pending_notifications(self) -> List[Dict]:
        """Return all pending/unread notifications."""
        return self.notification_log[-20:]  # Last 20

    def generate_mock_alerts(self, high_risk_students: List[Dict]) -> List[Dict]:
        """Generate mock real-time alerts for demo purposes."""
        alerts = []
        for student in high_risk_students[:5]:
            risk = student.get("risk_score", 75)
            alerts.append({
                "id": student.get("student_id", "STU001"),
                "type": "high_risk",
                "student_name": student.get("full_name", "Unknown"),
                "message": f"Risk score: {risk}/100 - Intervention needed",
                "severity": "critical" if risk > 85 else "high",
                "timestamp": datetime.utcnow().isoformat(),
                "resolved": False
            })
        return alerts


# ═══════════════════════════════════════════════════════════
# CHATBOT AGENT
# Basic emotional support chatbot for students
# ═══════════════════════════════════════════════════════════

class SupportChatbot:
    """
    Rule-based emotional support chatbot for students.
    In production: replace with LLM API call (Claude/GPT-4).
    """

    RESPONSES = {
        "struggling": [
            "I hear you — it's really tough sometimes. You're not alone in feeling this way. 💙",
            "Struggling academically doesn't mean you're failing as a person. Let's figure this out together.",
            "Many students feel exactly the same. Have you spoken to your counselor yet? They're here to help."
        ],
        "absent": [
            "Sometimes it's hard to come to school. What's been making it difficult for you?",
            "I noticed you've missed some days. Is everything okay at home?",
            "Remember, each day you come back is a fresh start."
        ],
        "failing": [
            "Failing a subject feels awful, but it's not the end. Let's make a plan.",
            "Everyone fails sometimes — even the best students. What subject is hardest for you?",
            "Have you talked to your teacher about extra help? Most teachers want to see you succeed."
        ],
        "anxious": [
            "Feeling anxious about school is very common. Deep breaths — you've got this. 🌟",
            "Anxiety can make everything feel bigger than it is. Would you like to try a quick breathing exercise?",
            "Your counselor has techniques that can really help with school anxiety."
        ],
        "motivation": [
            "Losing motivation happens to everyone. What did you enjoy about school before?",
            "Sometimes small goals make a big difference. What's one tiny thing you can achieve today?",
            "I believe in you. You've made it this far — that matters."
        ],
        "default": [
            "I'm here to listen. Tell me more about what you're going through.",
            "Thank you for sharing. How are you feeling right now?",
            "You reached out — that takes courage. How can I help today?",
            "I'm a support bot, but your school counselor can give you even better personal support!"
        ]
    }

    def get_response(self, user_message: str) -> str:
        """Generate contextual response based on keywords in message."""
        message_lower = user_message.lower()

        if any(w in message_lower for w in ["struggling", "hard", "difficult", "can't do"]):
            category = "struggling"
        elif any(w in message_lower for w in ["absent", "skip", "don't want to go", "missing"]):
            category = "absent"
        elif any(w in message_lower for w in ["fail", "failing", "bad grade", "low marks"]):
            category = "failing"
        elif any(w in message_lower for w in ["anxious", "worried", "scared", "nervous", "stress"]):
            category = "anxious"
        elif any(w in message_lower for w in ["motivation", "bored", "give up", "pointless"]):
            category = "motivation"
        else:
            category = "default"

        import random
        responses = self.RESPONSES[category]
        return random.choice(responses)

    def get_initial_message(self) -> str:
        return (
            "Hi there! 👋 I'm your school support assistant. "
            "I'm here to listen and help. How are you feeling today? "
            "Remember, you can also talk to your school counselor anytime."
        )


# ─────────────────────────────────────────────────────────
# Global instances
# ─────────────────────────────────────────────────────────
_study_plan_agent = None
_notification_agent = None
_chatbot = None


def get_study_plan_agent() -> StudyPlanAgent:
    global _study_plan_agent
    if _study_plan_agent is None:
        _study_plan_agent = StudyPlanAgent()
    return _study_plan_agent


def get_notification_agent() -> NotificationAgent:
    global _notification_agent
    if _notification_agent is None:
        _notification_agent = NotificationAgent()
    return _notification_agent


def get_chatbot() -> SupportChatbot:
    global _chatbot
    if _chatbot is None:
        _chatbot = SupportChatbot()
    return _chatbot
