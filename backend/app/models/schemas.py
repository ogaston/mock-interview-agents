"""
Pydantic models for the Mock Interview Agent API.
"""
from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


# ============================================================================
# Request Models
# ============================================================================

class StartInterviewRequest(BaseModel):
    """Request to start a new interview session."""
    role: str = Field(..., description="Job role/position for the interview", examples=["Software Engineer", "Product Manager"])
    seniority: Literal["junior", "mid", "senior", "lead"] = Field(..., description="Seniority level of the position")
    focus_areas: list[str] | None = Field(None, description="Optional specific areas to focus on", examples=[["algorithms", "system design"]])


class SubmitAnswerRequest(BaseModel):
    """Request to submit an answer to a question."""
    answer: str = Field(..., description="User's answer to the current question", min_length=10)


# ============================================================================
# Response Models
# ============================================================================

class Question(BaseModel):
    """A single interview question."""
    question_id: int = Field(..., description="Sequential question number")
    question_text: str = Field(..., description="The interview question")
    category: str | None = Field(None, description="Category of the question (e.g., technical, behavioral)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EvaluationScore(BaseModel):
    """Fuzzy logic evaluation scores for an answer."""
    clarity: float = Field(..., ge=0.0, le=10.0, description="Clarity score (0-10)")
    confidence: float = Field(..., ge=0.0, le=10.0, description="Confidence score (0-10)")
    relevance: float = Field(..., ge=0.0, le=10.0, description="Relevance score (0-10)")
    overall_score: float = Field(..., ge=0.0, le=10.0, description="Overall aggregated score (0-10)")


class AnswerEvaluation(BaseModel):
    """Evaluation of a single answer."""
    question_id: int
    answer_text: str
    scores: EvaluationScore
    nlp_features: dict = Field(default_factory=dict, description="Extracted NLP features")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FeedbackItem(BaseModel):
    """Individual feedback item with suggestions."""
    category: str = Field(..., description="Feedback category (e.g., 'Communication', 'Technical Knowledge')")
    strength: str | None = Field(None, description="What the candidate did well")
    weakness: str | None = Field(None, description="What needs improvement")
    suggestions: list[str] = Field(default_factory=list, description="Specific improvement suggestions")


class InterviewFeedback(BaseModel):
    """Comprehensive feedback for the entire interview."""
    overall_score: float = Field(..., ge=0.0, le=10.0)
    overall_summary: str = Field(..., description="General summary of performance")
    feedback_items: list[FeedbackItem] = Field(default_factory=list)
    recommended_resources: list[str] = Field(default_factory=list, description="Learning resources and practice materials")
    strengths: list[str] = Field(default_factory=list)
    areas_for_improvement: list[str] = Field(default_factory=list)


class InterviewSessionResponse(BaseModel):
    """Response for a new interview session."""
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    role: str
    seniority: str
    current_question: Question
    total_questions: int
    status: Literal["in_progress", "completed"] = "in_progress"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AnswerResponse(BaseModel):
    """Response after submitting an answer."""
    session_id: str
    question_answered: int
    evaluation: EvaluationScore | None = Field(None, description="Evaluation scores (only available after all answers are evaluated)")
    next_question: Question | None = Field(None, description="Next question if interview continues")
    status: Literal["in_progress", "completed", "evaluated"] = Field("in_progress", description="Status: in_progress, evaluated (all answers evaluated), or completed")
    total_questions: int
    questions_remaining: int


class FeedbackResponse(BaseModel):
    """Response containing final interview feedback."""
    session_id: str
    feedback: InterviewFeedback
    all_evaluations: list[AnswerEvaluation]
    interview_duration_minutes: float | None = None


# ============================================================================
# Internal State Models (for LangGraph)
# ============================================================================

class InterviewState(BaseModel):
    """State for the LangGraph interview workflow."""
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    role: str
    seniority: str
    focus_areas: list[str] = Field(default_factory=list)

    # Interview progress
    current_question_id: int = 0
    total_questions: int = 10
    questions: list[Question] = Field(default_factory=list)
    answers: list[str] = Field(default_factory=list)
    evaluations: list[AnswerEvaluation] = Field(default_factory=list)

    # Final feedback (populated at end)
    final_feedback: InterviewFeedback | None = None

    # Status tracking
    status: Literal["in_progress", "completed"] = "in_progress"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"arbitrary_types_allowed": True}


class NLPFeatures(BaseModel):
    """Extracted NLP features from an answer."""
    word_count: int = 0
    sentence_count: int = 0
    avg_sentence_length: float = 0.0
    sentiment_score: float = 0.0  # -1 to 1
    confidence_indicators: int = 0  # Count of confident language
    filler_words_count: int = 0  # "um", "uh", "like", etc.
    technical_terms_count: int = 0
    coherence_score: float = 0.0  # 0 to 1
    complexity_score: float = 0.0  # Based on vocabulary
