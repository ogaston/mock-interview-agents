"""
NLP Service for extracting linguistic features from interview answers.
Uses spaCy for text analysis and basic sentiment/complexity metrics.
"""
import re
from typing import Dict
from app.models.schemas import NLPFeatures


class NLPService:
    """Service for analyzing text and extracting linguistic features."""

    def __init__(self):
        """Initialize the NLP service. Lazy-loads spaCy model when needed."""
        self._nlp = None
        self.filler_words = {
            "eh", "este", "o sea", "digamos", "bueno", "tipo", "sabes",
            "entonces", "mhm", "pues", "básicamente", "literalmente", "así que", "umm", "uh"
        }
        self.confidence_indicators = {
            "definitivamente", "ciertamente", "claramente", "obviamente",
            "precisamente", "exactamente", "absolutamente", "seguro",
            "indudablemente", "sin duda", "creo", "pienso", "sé", "confío", "experiencia"
        }
        # Common technical terms (English terms are common in tech, added Spanish variations)
        self.technical_terms = {
            "algorithm", "complexity", "database", "api", "framework",
            "architecture", "scalability", "optimization", "implementation",
            "design pattern", "microservice", "cache", "queue", "stack",
            "performance", "latency", "throughput", "distributed", "concurrent",
            "algoritmo", "complejidad", "base de datos", "arquitectura",
            "escalabilidad", "optimización", "implementación", "patrón de diseño",
            "microservicio", "cola", "pila", "rendimiento", "latencia",
            "concurrente", "distribuido"
        }

    @property
    def nlp(self):
        """Lazy-load spaCy model."""
        if self._nlp is None:
            try:
                import spacy
                # Try to load Spanish model, fallback to blank if not available
                try:
                    self._nlp = spacy.load("es_core_news_sm")
                except OSError:
                    print("Warning: spaCy model 'es_core_news_sm' not found. Using blank model.")
                    print("Install with: python -m spacy download es_core_news_sm")
                    self._nlp = spacy.blank("es")
            except ImportError:
                raise ImportError("spaCy is not installed. Install with: pip install spacy")
        return self._nlp

    def extract_features(self, text: str) -> NLPFeatures:
        """
        Extract comprehensive NLP features from text.

        Args:
            text: The answer text to analyze

        Returns:
            NLPFeatures object containing all extracted features
        """
        if not text or not text.strip():
            return NLPFeatures()

        text_lower = text.lower()
        doc = self.nlp(text)

        # Basic text statistics
        words = [token for token in doc if not token.is_punct and not token.is_space]
        word_count = len(words)
        sentences = list(doc.sents)
        sentence_count = len(sentences)
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0

        # Count filler words
        filler_count = sum(1 for word in self.filler_words if word in text_lower)

        # Count confidence indicators
        confidence_count = sum(1 for word in self.confidence_indicators if word in text_lower)

        # Count technical terms
        technical_count = sum(1 for term in self.technical_terms if term in text_lower)

        # Sentiment analysis (simple approach using positive/negative word lists)
        sentiment = self._calculate_sentiment(text_lower)

        # Coherence score (based on sentence connectivity)
        coherence = self._calculate_coherence(doc, sentences)

        # Complexity score (based on vocabulary diversity and word length)
        complexity = self._calculate_complexity(words)

        return NLPFeatures(
            word_count=word_count,
            sentence_count=sentence_count,
            avg_sentence_length=round(avg_sentence_length, 2),
            sentiment_score=round(sentiment, 3),
            confidence_indicators=confidence_count,
            filler_words_count=filler_count,
            technical_terms_count=technical_count,
            coherence_score=round(coherence, 3),
            complexity_score=round(complexity, 3)
        )

    def _calculate_sentiment(self, text: str) -> float:
        """
        Calculate basic sentiment score from -1 (negative) to 1 (positive).
        This is a simple implementation; for production, consider using transformers.
        """
        positive_words = {
            "bien", "excelente", "gran", "positivo", "éxito", "lograr",
            "mejorar", "efectivo", "eficiente", "fuerte", "confiado", "capaz",
            "bueno", "genial", "increíble", "solución", "resolver"
        }
        negative_words = {
            "mal", "pobre", "fallar", "difícil", "problema", "asunto", "lucha",
            "débil", "incapaz", "no puedo", "nunca", "imposible", "confundido",
            "error", "malo", "complicado"
        }

        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)

        total = pos_count + neg_count
        if total == 0:
            return 0.0

        return (pos_count - neg_count) / total

    def _calculate_coherence(self, doc, sentences: list) -> float:
        """
        Calculate coherence based on sentence connectivity.
        Uses overlap of entities and key terms between sentences.
        """
        if len(sentences) <= 1:
            return 1.0

        # Extract key nouns and entities from each sentence
        sentence_keywords = []
        for sent in sentences:
            keywords = {token.lemma_.lower() for token in sent if token.pos_ in ["NOUN", "PROPN", "VERB"]}
            sentence_keywords.append(keywords)

        # Calculate overlap between consecutive sentences
        overlaps = []
        for i in range(len(sentence_keywords) - 1):
            current = sentence_keywords[i]
            next_sent = sentence_keywords[i + 1]
            if len(current) > 0 and len(next_sent) > 0:
                overlap = len(current & next_sent) / len(current | next_sent)
                overlaps.append(overlap)

        return sum(overlaps) / len(overlaps) if overlaps else 0.5

    def _calculate_complexity(self, words: list) -> float:
        """
        Calculate vocabulary complexity based on diversity and word length.
        Returns a score from 0 to 1.
        """
        if len(words) == 0:
            return 0.0

        # Vocabulary diversity (unique words / total words)
        unique_words = set(token.lemma_.lower() for token in words)
        diversity = len(unique_words) / len(words)

        # Average word length
        avg_word_length = sum(len(token.text) for token in words) / len(words)
        # Normalize to 0-1 (assuming avg word length of 5 is medium, 10 is complex)
        length_score = min(avg_word_length / 10, 1.0)

        # Combine metrics
        complexity = (diversity * 0.6) + (length_score * 0.4)

        return complexity

    def get_feature_summary(self, features: NLPFeatures) -> Dict[str, str]:
        """
        Get a human-readable summary of the features.

        Args:
            features: NLPFeatures object

        Returns:
            Dictionary with feature interpretations
        """
        summary = {}

        # Word count interpretation
        if features.word_count < 50:
            summary["length"] = "muy breve"
        elif features.word_count < 100:
            summary["length"] = "breve"
        elif features.word_count < 200:
            summary["length"] = "moderada"
        else:
            summary["length"] = "detallada"

        # Sentiment interpretation
        if features.sentiment_score > 0.3:
            summary["tone"] = "positivo"
        elif features.sentiment_score < -0.3:
            summary["tone"] = "negativo"
        else:
            summary["tone"] = "neutral"

        # Coherence interpretation
        if features.coherence_score > 0.7:
            summary["coherence"] = "muy coherente"
        elif features.coherence_score > 0.4:
            summary["coherence"] = "moderadamente coherente"
        else:
            summary["coherence"] = "necesita mejor estructura"

        # Complexity interpretation
        if features.complexity_score > 0.7:
            summary["complexity"] = "vocabulario sofisticado"
        elif features.complexity_score > 0.4:
            summary["complexity"] = "complejidad moderada"
        else:
            summary["complexity"] = "lenguaje simple"

        return summary


# Singleton instance
nlp_service = NLPService()
