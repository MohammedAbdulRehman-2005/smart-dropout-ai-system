# ml/sentiment.py - NLP Sentiment Analysis for student feedback
# Uses a lightweight rule-based approach (fast) with optional HuggingFace upgrade
# Falls back gracefully if transformers not available

import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# LEXICON-BASED APPROACH (fast, no dependencies)
# Production systems should upgrade to HuggingFace
# ─────────────────────────────────────────────────────────

POSITIVE_WORDS = {
    "happy", "enjoy", "love", "great", "good", "excellent", "wonderful",
    "motivated", "excited", "confident", "proud", "successful", "better",
    "improving", "helpful", "supportive", "fun", "interesting", "amazing",
    "fantastic", "brilliant", "awesome", "like", "understand", "progress"
}

NEGATIVE_WORDS = {
    "sad", "hate", "boring", "difficult", "hard", "confused", "stressed",
    "anxious", "worried", "tired", "frustrated", "angry", "upset", "fail",
    "failing", "lost", "behind", "struggling", "overwhelmed", "hopeless",
    "give up", "dropout", "quit", "leave", "can't", "unable", "never",
    "useless", "stupid", "bad", "terrible", "worse", "worst", "bored"
}

INTENSIFIERS = {"very", "extremely", "really", "so", "too", "quite", "absolutely"}

NEGATORS = {"not", "no", "never", "don't", "doesn't", "didn't", "won't", "isn't", "aren't"}

EMOTION_KEYWORDS = {
    "frustrated": ["frustrated", "annoyed", "irritated", "aggravated"],
    "anxious": ["anxious", "worried", "nervous", "scared", "afraid", "fear"],
    "hopeless": ["hopeless", "give up", "quit", "dropout", "useless", "pointless"],
    "bored": ["bored", "boring", "monotonous", "dull", "uninteresting"],
    "confused": ["confused", "lost", "don't understand", "unclear", "confusing"],
    "motivated": ["motivated", "excited", "eager", "inspired", "enthusiastic"],
    "happy": ["happy", "joyful", "pleased", "content", "satisfied", "cheerful"],
    "tired": ["tired", "exhausted", "sleepy", "fatigue", "burnout"],
}


class SentimentAnalyzer:
    """
    Lightweight sentiment analyzer for student feedback text.
    
    Provides:
    - Sentiment score (-1 negative to +1 positive)
    - Sentiment label (positive/neutral/negative)
    - Emotion tags
    
    Note: For production, replace with:
    from transformers import pipeline
    self.pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    """

    def __init__(self):
        self._hf_pipeline = None
        self._try_load_hf()

    def _try_load_hf(self):
        """Attempt to load HuggingFace pipeline (optional, enhances accuracy)."""
        try:
            from transformers import pipeline as hf_pipeline
            self._hf_pipeline = hf_pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                truncation=True,
                max_length=512
            )
            logger.info("✅ HuggingFace sentiment pipeline loaded")
        except Exception as e:
            logger.info(f"HuggingFace not available, using lexicon-based approach: {e}")

    def analyze(self, text: str) -> Dict:
        """
        Analyze sentiment of feedback text.
        
        Returns:
        {
            "sentiment_score": -0.45,       # -1 to +1
            "sentiment_label": "negative",   # positive/neutral/negative
            "emotion_tags": ["frustrated", "anxious"],
            "confidence": 0.82
        }
        """
        if not text or not text.strip():
            return {
                "sentiment_score": 0.0,
                "sentiment_label": "neutral",
                "emotion_tags": [],
                "confidence": 1.0
            }

        text_lower = text.lower().strip()

        # Try HuggingFace first
        if self._hf_pipeline:
            return self._analyze_hf(text_lower)
        else:
            return self._analyze_lexicon(text_lower)

    def _analyze_hf(self, text: str) -> Dict:
        """Sentiment analysis using HuggingFace DistilBERT."""
        try:
            result = self._hf_pipeline(text[:512])[0]
            label = result["label"].lower()  # POSITIVE or NEGATIVE
            confidence = float(result["score"])

            if label == "positive":
                score = confidence * 1.0
                sentiment_label = "positive" if confidence > 0.6 else "neutral"
            else:
                score = -confidence
                sentiment_label = "negative" if confidence > 0.6 else "neutral"

            emotion_tags = self._detect_emotions(text)

            return {
                "sentiment_score": round(score, 3),
                "sentiment_label": sentiment_label,
                "emotion_tags": emotion_tags,
                "confidence": round(confidence, 3)
            }
        except Exception as e:
            logger.warning(f"HuggingFace analysis failed, falling back: {e}")
            return self._analyze_lexicon(text)

    def _analyze_lexicon(self, text: str) -> Dict:
        """Rule-based lexicon approach for sentiment analysis."""
        words = re.findall(r'\b\w+\b', text.lower())

        pos_score = 0
        neg_score = 0
        word_count = max(len(words), 1)

        for i, word in enumerate(words):
            # Check for negation in previous 3 words
            prev_words = words[max(0, i-3):i]
            is_negated = any(neg in prev_words for neg in NEGATORS)

            # Check for intensifier
            has_intensifier = any(inten in prev_words for inten in INTENSIFIERS)
            multiplier = 1.5 if has_intensifier else 1.0

            if word in POSITIVE_WORDS:
                if is_negated:
                    neg_score += 0.5 * multiplier  # Negated positive = mild negative
                else:
                    pos_score += 1.0 * multiplier
            elif word in NEGATIVE_WORDS:
                if is_negated:
                    pos_score += 0.3 * multiplier  # Negated negative = slight positive
                else:
                    neg_score += 1.0 * multiplier

        # Check for multi-word phrases
        for neg_phrase in ["give up", "can't do", "don't care", "don't want", "drop out"]:
            if neg_phrase in text:
                neg_score += 2.0

        # Normalize scores
        total = pos_score + neg_score
        if total == 0:
            normalized_score = 0.0
            confidence = 0.5
        else:
            normalized_score = (pos_score - neg_score) / total
            confidence = min(total / (word_count * 0.3), 1.0)

        # Assign label
        if normalized_score > 0.2:
            label = "positive"
        elif normalized_score < -0.2:
            label = "negative"
        else:
            label = "neutral"

        emotion_tags = self._detect_emotions(text)

        return {
            "sentiment_score": round(float(normalized_score), 3),
            "sentiment_label": label,
            "emotion_tags": emotion_tags,
            "confidence": round(float(confidence), 3)
        }

    def _detect_emotions(self, text: str) -> List[str]:
        """Detect specific emotions from text using keyword matching."""
        detected = []
        for emotion, keywords in EMOTION_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                detected.append(emotion)
        return detected[:4]  # Max 4 emotion tags

    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """Analyze a batch of feedback texts."""
        return [self.analyze(text) for text in texts]

    def aggregate_sentiment(self, analyses: List[Dict]) -> Dict:
        """
        Aggregate multiple sentiment analyses for a student's history.
        
        Returns summary statistics.
        """
        if not analyses:
            return {
                "avg_sentiment": 0.0,
                "label": "neutral",
                "negative_count": 0,
                "positive_count": 0,
                "all_emotions": []
            }

        scores = [a["sentiment_score"] for a in analyses]
        avg_score = sum(scores) / len(scores)

        negative_count = sum(1 for a in analyses if a["sentiment_label"] == "negative")
        positive_count = sum(1 for a in analyses if a["sentiment_label"] == "positive")

        # Collect all unique emotions
        all_emotions = list(set(
            emotion
            for a in analyses
            for emotion in a.get("emotion_tags", [])
        ))

        return {
            "avg_sentiment": round(avg_score, 3),
            "label": "negative" if avg_score < -0.2 else "positive" if avg_score > 0.2 else "neutral",
            "negative_count": negative_count,
            "positive_count": positive_count,
            "all_emotions": all_emotions
        }


# Global singleton
_sentiment_instance = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    global _sentiment_instance
    if _sentiment_instance is None:
        _sentiment_instance = SentimentAnalyzer()
    return _sentiment_instance
