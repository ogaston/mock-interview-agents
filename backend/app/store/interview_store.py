"""
In-memory storage for interview sessions.
"""
from app.models.schemas import InterviewState

# In-memory storage for interview sessions (no database needed)
interview_sessions: dict[str, InterviewState] = {}

