"""
Evaluator Agent - Evaluates answers using NLP features and fuzzy logic.
"""
from datetime import datetime
from app.models.schemas import AnswerEvaluation, Question
from app.services.nlp_service import nlp_service
from app.services.fuzzy_service import fuzzy_service


class EvaluatorAgent:
    """Agent responsible for evaluating interview answers."""

    def __init__(self):
        """Initialize the evaluator agent."""
        self.nlp_service = nlp_service
        self.fuzzy_service = fuzzy_service

    def evaluate_answer(
        self,
        question: Question,
        answer: str
    ) -> AnswerEvaluation:
        """
        Evaluate an interview answer using NLP and fuzzy logic.

        Args:
            question: The question that was asked
            answer: The candidate's answer

        Returns:
            AnswerEvaluation with scores and extracted features
        """
        # Step 1: Extract NLP features from the answer
        features = self.nlp_service.extract_features(answer)

        # Step 2: Apply fuzzy logic to calculate scores
        scores = self.fuzzy_service.evaluate(features, answer)

        # Step 3: Get feature summary for interpretability
        feature_summary = self.nlp_service.get_feature_summary(features)

        # Convert NLP features to dict for storage
        nlp_features_dict = {
            "word_count": features.word_count,
            "sentence_count": features.sentence_count,
            "avg_sentence_length": features.avg_sentence_length,
            "sentiment_score": features.sentiment_score,
            "confidence_indicators": features.confidence_indicators,
            "filler_words_count": features.filler_words_count,
            "technical_terms_count": features.technical_terms_count,
            "coherence_score": features.coherence_score,
            "complexity_score": features.complexity_score,
            "summary": feature_summary
        }

        return AnswerEvaluation(
            question_id=question.question_id,
            answer_text=answer,
            scores=scores,
            nlp_features=nlp_features_dict,
            timestamp=datetime.utcnow()
        )

    def get_evaluation_insights(self, evaluation: AnswerEvaluation) -> dict:
        """
        Generate insights from an evaluation.

        Args:
            evaluation: The answer evaluation

        Returns:
            Dictionary with interpretation of scores and suggestions
        """
        insights = {
            "overall_performance": self._interpret_score(evaluation.scores.overall_score),
            "strengths": [],
            "weaknesses": [],
            "quick_tips": []
        }

        # Analyze clarity
        if evaluation.scores.clarity >= 7:
            insights["strengths"].append("Clear and well-structured response")
        elif evaluation.scores.clarity <= 4:
            insights["weaknesses"].append("Response lacks clarity and structure")
            insights["quick_tips"].append("Organize your thoughts before answering")

        # Analyze confidence
        if evaluation.scores.confidence >= 7:
            insights["strengths"].append("Confident delivery")
        elif evaluation.scores.confidence <= 4:
            insights["weaknesses"].append("Response lacks confidence indicators")
            insights["quick_tips"].append("Use more assertive language and provide concrete examples")

        # Analyze relevance
        if evaluation.scores.relevance >= 7:
            insights["strengths"].append("Highly relevant and technical response")
        elif evaluation.scores.relevance <= 4:
            insights["weaknesses"].append("Response could be more technical and relevant")
            insights["quick_tips"].append("Include more technical details and domain-specific terminology")

        # Check for filler words
        filler_count = evaluation.nlp_features.get("filler_words_count", 0)
        if filler_count > 5:
            insights["weaknesses"].append("Excessive use of filler words")
            insights["quick_tips"].append("Practice reducing filler words (um, uh, like)")

        return insights

    def _interpret_score(self, score: float) -> str:
        """Interpret a numeric score into a performance level."""
        if score >= 8:
            return "Excellent"
        elif score >= 6:
            return "Good"
        elif score >= 4:
            return "Fair"
        else:
            return "Needs Improvement"


# Singleton instance
evaluator_agent = EvaluatorAgent()
