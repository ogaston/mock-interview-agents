"""
Fuzzy Logic Service for evaluating interview answers.
Uses scikit-fuzzy to implement fuzzy inference system for scoring clarity, confidence, and relevance.
"""
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from app.models.schemas import NLPFeatures, EvaluationScore


class FuzzyEvaluationService:
    """Service for evaluating answers using fuzzy logic."""

    def __init__(self):
        """Initialize fuzzy inference system."""
        self._setup_fuzzy_system()

    def _setup_fuzzy_system(self):
        """Set up the fuzzy inference system with rules."""

        # Define fuzzy variables for inputs (0-10 scale after normalization)
        self.word_count = ctrl.Antecedent(np.arange(0, 11, 1), 'word_count')
        self.coherence = ctrl.Antecedent(np.arange(0, 11, 1), 'coherence')
        self.confidence_level = ctrl.Antecedent(np.arange(0, 11, 1), 'confidence_level')
        self.technical_depth = ctrl.Antecedent(np.arange(0, 11, 1), 'technical_depth')
        self.filler_ratio = ctrl.Antecedent(np.arange(0, 11, 1), 'filler_ratio')  # Inverse: lower is better
        self.complexity = ctrl.Antecedent(np.arange(0, 11, 1), 'complexity')

        # Define fuzzy variables for outputs (0-10 scale)
        self.clarity_score = ctrl.Consequent(np.arange(0, 11, 1), 'clarity_score')
        self.confidence_score = ctrl.Consequent(np.arange(0, 11, 1), 'confidence_score')
        self.relevance_score = ctrl.Consequent(np.arange(0, 11, 1), 'relevance_score')

        # Define membership functions for inputs
        # Word count: low, medium, high
        self.word_count['low'] = fuzz.trimf(self.word_count.universe, [0, 0, 4])
        self.word_count['medium'] = fuzz.trimf(self.word_count.universe, [3, 5, 7])
        self.word_count['high'] = fuzz.trimf(self.word_count.universe, [6, 10, 10])

        # Coherence: low, medium, high
        self.coherence['low'] = fuzz.trimf(self.coherence.universe, [0, 0, 4])
        self.coherence['medium'] = fuzz.trimf(self.coherence.universe, [3, 5, 7])
        self.coherence['high'] = fuzz.trimf(self.coherence.universe, [6, 10, 10])

        # Confidence level: low, medium, high
        self.confidence_level['low'] = fuzz.trimf(self.confidence_level.universe, [0, 0, 4])
        self.confidence_level['medium'] = fuzz.trimf(self.confidence_level.universe, [3, 5, 7])
        self.confidence_level['high'] = fuzz.trimf(self.confidence_level.universe, [6, 10, 10])

        # Technical depth: low, medium, high
        self.technical_depth['low'] = fuzz.trimf(self.technical_depth.universe, [0, 0, 4])
        self.technical_depth['medium'] = fuzz.trimf(self.technical_depth.universe, [3, 5, 7])
        self.technical_depth['high'] = fuzz.trimf(self.technical_depth.universe, [6, 10, 10])

        # Filler ratio: low (good), medium, high (bad)
        self.filler_ratio['low'] = fuzz.trimf(self.filler_ratio.universe, [0, 0, 3])
        self.filler_ratio['medium'] = fuzz.trimf(self.filler_ratio.universe, [2, 5, 8])
        self.filler_ratio['high'] = fuzz.trimf(self.filler_ratio.universe, [7, 10, 10])

        # Complexity: low, medium, high
        self.complexity['low'] = fuzz.trimf(self.complexity.universe, [0, 0, 4])
        self.complexity['medium'] = fuzz.trimf(self.complexity.universe, [3, 5, 7])
        self.complexity['high'] = fuzz.trimf(self.complexity.universe, [6, 10, 10])

        # Define membership functions for outputs
        for output in [self.clarity_score, self.confidence_score, self.relevance_score]:
            output['poor'] = fuzz.trimf(output.universe, [0, 0, 3])
            output['fair'] = fuzz.trimf(output.universe, [2, 4, 6])
            output['good'] = fuzz.trimf(output.universe, [5, 7, 9])
            output['excellent'] = fuzz.trimf(output.universe, [8, 10, 10])

        # Define fuzzy rules
        self._define_rules()

    def _define_rules(self):
        """Define fuzzy inference rules."""

        # Clarity rules (based on coherence, filler words, and structure)
        clarity_rules = [
            ctrl.Rule(self.coherence['high'] & self.filler_ratio['low'], self.clarity_score['excellent']),
            ctrl.Rule(self.coherence['high'] & self.filler_ratio['medium'], self.clarity_score['good']),
            ctrl.Rule(self.coherence['medium'] & self.filler_ratio['low'], self.clarity_score['good']),
            ctrl.Rule(self.coherence['medium'] & self.filler_ratio['medium'], self.clarity_score['fair']),
            ctrl.Rule(self.coherence['low'] | self.filler_ratio['high'], self.clarity_score['poor']),
        ]

        # Confidence rules (based on confidence indicators and word count)
        confidence_rules = [
            ctrl.Rule(self.confidence_level['high'] & self.word_count['high'], self.confidence_score['excellent']),
            ctrl.Rule(self.confidence_level['high'] & self.word_count['medium'], self.confidence_score['good']),
            ctrl.Rule(self.confidence_level['medium'] & self.word_count['medium'], self.confidence_score['good']),
            ctrl.Rule(self.confidence_level['medium'] & self.word_count['low'], self.confidence_score['fair']),
            ctrl.Rule(self.confidence_level['low'], self.confidence_score['poor']),
        ]

        # Relevance rules (based on technical depth and complexity)
        relevance_rules = [
            ctrl.Rule(self.technical_depth['high'] & self.complexity['high'], self.relevance_score['excellent']),
            ctrl.Rule(self.technical_depth['high'] & self.complexity['medium'], self.relevance_score['good']),
            ctrl.Rule(self.technical_depth['medium'] & self.complexity['medium'], self.relevance_score['good']),
            ctrl.Rule(self.technical_depth['medium'] & self.complexity['low'], self.relevance_score['fair']),
            ctrl.Rule(self.technical_depth['low'], self.relevance_score['poor']),
        ]

        # Create control systems
        self.clarity_system = ctrl.ControlSystem(clarity_rules)
        self.confidence_system = ctrl.ControlSystem(confidence_rules)
        self.relevance_system = ctrl.ControlSystem(relevance_rules)

    def evaluate(self, features: NLPFeatures, answer_text: str) -> EvaluationScore:
        """
        Evaluate an answer using fuzzy logic.

        Args:
            features: Extracted NLP features
            answer_text: The original answer text

        Returns:
            EvaluationScore with all score components
        """
        # Normalize features to 0-10 scale
        normalized = self._normalize_features(features)

        # Calculate clarity score
        clarity_sim = ctrl.ControlSystemSimulation(self.clarity_system)
        clarity_sim.input['coherence'] = normalized['coherence']
        clarity_sim.input['filler_ratio'] = normalized['filler_ratio']
        try:
            clarity_sim.compute()
            clarity = float(clarity_sim.output['clarity_score'])
        except (KeyError, AssertionError):
            # Fallback if fuzzy inference fails (edge case inputs)
            clarity = 5.0  # Default to middle score

        # Calculate confidence score
        confidence_sim = ctrl.ControlSystemSimulation(self.confidence_system)
        confidence_sim.input['confidence_level'] = normalized['confidence_level']
        confidence_sim.input['word_count'] = normalized['word_count']
        try:
            confidence_sim.compute()
            confidence = float(confidence_sim.output['confidence_score'])
        except (KeyError, AssertionError):
            # Fallback if fuzzy inference fails (edge case inputs)
            confidence = 5.0  # Default to middle score

        # Calculate relevance score
        relevance_sim = ctrl.ControlSystemSimulation(self.relevance_system)
        relevance_sim.input['technical_depth'] = normalized['technical_depth']
        relevance_sim.input['complexity'] = normalized['complexity']
        try:
            relevance_sim.compute()
            relevance = float(relevance_sim.output['relevance_score'])
        except (KeyError, AssertionError):
            # Fallback if fuzzy inference fails (edge case inputs)
            relevance = 5.0  # Default to middle score

        # Calculate overall score (weighted average)
        overall = (clarity * 0.3) + (confidence * 0.3) + (relevance * 0.4)

        return EvaluationScore(
            clarity=round(clarity, 2),
            confidence=round(confidence, 2),
            relevance=round(relevance, 2),
            overall_score=round(overall, 2)
        )

    def _normalize_features(self, features: NLPFeatures) -> dict:
        """
        Normalize NLP features to 0-10 scale for fuzzy input.

        Args:
            features: NLPFeatures object

        Returns:
            Dictionary of normalized values
        """
        # Word count: normalize based on expected ranges (50-200 words)
        word_count_norm = min((features.word_count / 150) * 10, 10)

        # Coherence: already 0-1, scale to 0-10
        coherence_norm = features.coherence_score * 10

        # Confidence level: based on confidence indicators per 100 words
        confidence_ratio = (features.confidence_indicators / max(features.word_count / 100, 1))
        confidence_norm = min(confidence_ratio * 5, 10)  # Scale appropriately

        # Technical depth: based on technical terms per 100 words
        technical_ratio = (features.technical_terms_count / max(features.word_count / 100, 1))
        technical_norm = min(technical_ratio * 3, 10)  # Scale appropriately

        # Filler ratio: inverse - more fillers = worse score
        filler_ratio = (features.filler_words_count / max(features.word_count / 100, 1))
        filler_norm = max(10 - (filler_ratio * 5), 0)  # Inverse scale

        # Complexity: already 0-1, scale to 0-10
        complexity_norm = features.complexity_score * 10

        return {
            'word_count': max(0, min(word_count_norm, 10)),
            'coherence': max(0, min(coherence_norm, 10)),
            'confidence_level': max(0, min(confidence_norm, 10)),
            'technical_depth': max(0, min(technical_norm, 10)),
            'filler_ratio': max(0, min(filler_norm, 10)),
            'complexity': max(0, min(complexity_norm, 10)),
        }


# Singleton instance
fuzzy_service = FuzzyEvaluationService()
