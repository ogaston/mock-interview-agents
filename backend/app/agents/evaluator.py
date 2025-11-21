"""
Evaluator Agent - Evaluates answers using NLP features and fuzzy logic.
"""
from datetime import datetime
from app.models.schemas import AnswerEvaluation, Question, InterviewState
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
            insights["strengths"].append("Respuesta clara y bien estructurada")
        elif evaluation.scores.clarity <= 4:
            insights["weaknesses"].append("La respuesta carece de claridad y estructura")
            insights["quick_tips"].append("Organiza tus pensamientos antes de responder")

        # Analyze confidence
        if evaluation.scores.confidence >= 7:
            insights["strengths"].append("Comunicación confiada")
        elif evaluation.scores.confidence <= 4:
            insights["weaknesses"].append("La respuesta carece de indicadores de confianza")
            insights["quick_tips"].append("Usa lenguaje más asertivo y proporciona ejemplos concretos")

        # Analyze relevance
        if evaluation.scores.relevance >= 7:
            insights["strengths"].append("Respuesta altamente relevante y técnica")
        elif evaluation.scores.relevance <= 4:
            insights["weaknesses"].append("La respuesta podría ser más técnica y relevante")
            insights["quick_tips"].append("Incluye más detalles técnicos y terminología específica del dominio")

        # Check for filler words
        filler_count = evaluation.nlp_features.get("filler_words_count", 0)
        if filler_count > 5:
            insights["weaknesses"].append("Uso excesivo de muletillas")
            insights["quick_tips"].append("Practica reducir muletillas (eh, um, pues)")

        return insights

    def evaluate_all_answers(self, state: InterviewState) -> list[AnswerEvaluation]:
        """
        Evaluate all unanswered questions in bulk.

        Args:
            state: Interview state with questions and answers

        Returns:
            List of evaluations for all question-answer pairs
        """
        evaluations = []
        
        # Evaluate all question-answer pairs
        for i, (question, answer) in enumerate(zip(state.questions, state.answers)):
            # Skip if already evaluated
            if i < len(state.evaluations):
                continue
            
            # Evaluate this answer
            evaluation = self.evaluate_answer(question, answer)
            evaluations.append(evaluation)
        
        return evaluations

    def _interpret_score(self, score: float) -> str:
        """Interpret a numeric score into a performance level."""
        if score >= 8:
            return "Excelente"
        elif score >= 6:
            return "Bueno"
        elif score >= 4:
            return "Regular"
        else:
            return "Necesita Mejorar"


# Singleton instance
evaluator_agent = EvaluatorAgent()
