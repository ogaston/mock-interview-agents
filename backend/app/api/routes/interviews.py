"""
FastAPI routes for interview operations.
"""
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import (
    StartInterviewRequest,
    SubmitAnswerRequest,
    InterviewSessionResponse,
    AnswerResponse,
    FeedbackResponse,
    InterviewState
)
from app.graph.workflow import interview_workflow
from app.config import settings

router = APIRouter(prefix="/api/interviews", tags=["interviews"])

# In-memory storage for interview sessions (no database needed)
interview_sessions: dict[str, InterviewState] = {}


@router.post("/start", response_model=InterviewSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_interview(request: StartInterviewRequest):
    """
    Start a new interview session.

    Creates a new interview, generates the first question, and returns session details.
    """
    try:
        # Start the interview workflow
        state = interview_workflow.start_interview(
            role=request.role,
            seniority=request.seniority,
            focus_areas=request.focus_areas,
            total_questions=settings.max_questions_per_interview
        )

        # Store session
        interview_sessions[state.session_id] = state

        # Get the first question
        current_question = state.questions[0] if state.questions else None

        if not current_question:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate initial question"
            )

        return InterviewSessionResponse(
            session_id=state.session_id,
            role=state.role,
            seniority=state.seniority,
            current_question=current_question,
            total_questions=state.total_questions,
            status=state.status,
            created_at=state.created_at
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start interview: {str(e)}"
        )


@router.post("/{session_id}/answer", response_model=AnswerResponse)
async def submit_answer(session_id: str, request: SubmitAnswerRequest):
    """
    Submit an answer to the current question.

    Evaluates the answer and returns the next question or completes the interview.
    """
    # Get session
    state = interview_sessions.get(session_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview session {session_id} not found"
        )

    if state.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview is already completed"
        )

    try:
        # Submit answer and get updated state
        updated_state = interview_workflow.submit_answer(state, request.answer)

        # Update stored session
        interview_sessions[session_id] = updated_state

        # Get the most recent evaluation
        latest_evaluation = updated_state.evaluations[-1] if updated_state.evaluations else None

        if not latest_evaluation:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to evaluate answer"
            )

        # Get next question (if interview continues)
        next_question = None
        if updated_state.status == "in_progress" and len(updated_state.questions) > len(updated_state.answers):
            next_question = updated_state.questions[-1]

        questions_remaining = max(0, updated_state.total_questions - len(updated_state.answers))

        return AnswerResponse(
            session_id=session_id,
            question_answered=latest_evaluation.question_id,
            evaluation=latest_evaluation.scores,
            next_question=next_question,
            status=updated_state.status,
            total_questions=updated_state.total_questions,
            questions_remaining=questions_remaining
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process answer: {str(e)}"
        )


@router.get("/{session_id}/feedback", response_model=FeedbackResponse)
async def get_feedback(session_id: str):
    """
    Get comprehensive feedback for a completed interview.

    Returns detailed analysis, scores, and improvement recommendations.
    """
    # Get session
    state = interview_sessions.get(session_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview session {session_id} not found"
        )

    try:
        # Generate feedback if not already done
        if not state.final_feedback:
            state = interview_workflow.get_feedback(state)
            interview_sessions[session_id] = state

        if not state.final_feedback:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate feedback"
            )

        # Calculate interview duration
        if state.evaluations:
            first_timestamp = state.questions[0].timestamp
            last_timestamp = state.evaluations[-1].timestamp
            duration = (last_timestamp - first_timestamp).total_seconds() / 60
        else:
            duration = None

        return FeedbackResponse(
            session_id=session_id,
            feedback=state.final_feedback,
            all_evaluations=state.evaluations,
            interview_duration_minutes=round(duration, 2) if duration else None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback: {str(e)}"
        )


@router.get("/history", response_model=list[dict])
async def get_interview_history():
    """
    Get list of all interview sessions.

    Returns basic information about all stored interview sessions.
    """
    history = []

    for session_id, state in interview_sessions.items():
        history.append({
            "session_id": session_id,
            "role": state.role,
            "seniority": state.seniority,
            "status": state.status,
            "questions_answered": len(state.answers),
            "total_questions": state.total_questions,
            "overall_score": state.final_feedback.overall_score if state.final_feedback else None,
            "created_at": state.created_at.isoformat()
        })

    # Sort by created_at descending
    history.sort(key=lambda x: x["created_at"], reverse=True)

    return history


@router.post("/{session_id}/complete", status_code=status.HTTP_200_OK)
async def complete_interview(session_id: str):
    """
    Manually complete an interview session early.

    Generates feedback based on questions answered so far.
    """
    # Get session
    state = interview_sessions.get(session_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview session {session_id} not found"
        )

    if state.status == "completed":
        return {"message": "Interview already completed", "session_id": session_id}

    if not state.answers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot complete interview with no answers"
        )

    try:
        # Generate feedback
        state = interview_workflow.get_feedback(state)
        interview_sessions[session_id] = state

        return {
            "message": "Interview completed successfully",
            "session_id": session_id,
            "questions_answered": len(state.answers)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete interview: {str(e)}"
        )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interview(session_id: str):
    """
    Delete an interview session.

    Removes the session from memory.
    """
    if session_id not in interview_sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview session {session_id} not found"
        )

    del interview_sessions[session_id]
    return None
