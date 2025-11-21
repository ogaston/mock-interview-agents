"""
FastAPI routes for interview operations.
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from datetime import datetime
from app.models.schemas import (
    StartInterviewRequest,
    SubmitAnswerRequest,
    InterviewSessionResponse,
    AnswerResponse,
    FeedbackResponse,
    InterviewState,
    Question
)
from app.graph.workflow import interview_workflow
from app.agents.interviewer import interviewer_agent
from app.config import settings
import json

router = APIRouter(prefix="/api/interviews", tags=["interviews"])

# In-memory storage for interview sessions (no database needed)
interview_sessions: dict[str, InterviewState] = {}


@router.post("/start", response_model=InterviewSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_interview(request: StartInterviewRequest):
    """
    Start a new interview session.

    Creates a new interview, generates the first question (non-streaming), and returns session details.
    For streaming version, use /start-stream endpoint.
    """
    try:
        # Start the interview workflow (without generating all questions upfront)
        state = interview_workflow.start_interview_incremental(
            role=request.role,
            seniority=request.seniority,
            focus_areas=request.focus_areas,
            total_questions=settings.max_questions_per_interview
        )

        # Generate first question
        first_question = interviewer_agent.generate_first_question(state)
        state.questions.append(first_question)
        state.current_question_id = first_question.question_id

        # Store session
        interview_sessions[state.session_id] = state

        return InterviewSessionResponse(
            session_id=state.session_id,
            role=state.role,
            seniority=state.seniority,
            current_question=first_question,
            total_questions=state.total_questions,
            status=state.status,
            created_at=state.created_at
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start interview: {str(e)}"
        )


@router.post("/start-stream")
async def start_interview_stream(request: StartInterviewRequest):
    """
    Start a new interview session with streaming question generation.

    Returns session metadata followed by streamed question text.
    """
    try:
        # Start the interview workflow (without generating questions)
        state = interview_workflow.start_interview_incremental(
            role=request.role,
            seniority=request.seniority,
            focus_areas=request.focus_areas,
            total_questions=settings.max_questions_per_interview
        )

        # Store session
        interview_sessions[state.session_id] = state

        async def generate():
            # First, send session metadata
            metadata = {
                "type": "metadata",
                "session_id": state.session_id,
                "role": state.role,
                "seniority": state.seniority,
                "total_questions": state.total_questions,
                "status": state.status,
                "created_at": state.created_at.isoformat(),
                "question_id": 1,
                "category": "opening"
            }
            yield f"data: {json.dumps(metadata)}\n\n"

            # Stream the first question
            full_text = ""
            async for chunk in interviewer_agent.stream_first_question(state):
                full_text += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

            # Send completion event with full question
            first_question = Question(
                question_id=1,
                question_text=full_text.strip(),
                category="opening",
                timestamp=datetime.utcnow()
            )
            state.questions.append(first_question)
            state.current_question_id = first_question.question_id
            
            # Update stored session
            interview_sessions[state.session_id] = state

            yield f"data: {json.dumps({'type': 'done', 'question_text': full_text.strip()})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start interview: {str(e)}"
        )


@router.post("/{session_id}/answer", response_model=AnswerResponse)
async def submit_answer(session_id: str, request: SubmitAnswerRequest):
    """
    Submit an answer to the current question (non-streaming).

    Stores the answer and returns the next question. When all answers are submitted,
    automatically triggers bulk evaluation. For streaming version, use /answer-stream.
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
        # Submit answer
        state.answers.append(request.answer)

        # Check if all answers have been submitted
        all_answers_submitted = len(state.answers) >= state.total_questions
        
        # Determine response status
        response_status = "in_progress"
        next_question = None
        
        if all_answers_submitted:
            # If all answers submitted, trigger bulk evaluation
            if len(state.evaluations) < len(state.answers):
                state = interview_workflow.evaluate_all_answers(state)
                interview_sessions[session_id] = state
            
            # Check if evaluations are complete
            if len(state.evaluations) == len(state.answers):
                response_status = "evaluated"
        else:
            # Generate next question
            next_question = interviewer_agent.generate_next_question(state)
            state.questions.append(next_question)
            state.current_question_id = next_question.question_id
            response_status = "in_progress"

        # Update stored session
        interview_sessions[session_id] = state

        questions_remaining = max(0, state.total_questions - len(state.answers))

        # Get evaluation if available (only after bulk evaluation)
        evaluation = None
        if state.evaluations and len(state.evaluations) == len(state.answers):
            # All evaluations complete, get the last one for display
            latest_evaluation = state.evaluations[-1]
            evaluation = latest_evaluation.scores

        return AnswerResponse(
            session_id=session_id,
            question_answered=len(state.answers),
            evaluation=evaluation,
            next_question=next_question,
            status=response_status,
            total_questions=state.total_questions,
            questions_remaining=questions_remaining
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process answer: {str(e)}"
        )


@router.post("/{session_id}/answer-stream")
async def submit_answer_stream(session_id: str, request: SubmitAnswerRequest):
    """
    Submit an answer and stream the next question.

    Stores the answer and streams the next question. When all answers are submitted,
    triggers bulk evaluation and returns completion status.
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
        # Submit answer
        state.answers.append(request.answer)

        # Check if all answers have been submitted
        all_answers_submitted = len(state.answers) >= state.total_questions

        async def generate():
            if all_answers_submitted:
                # Send metadata indicating completion
                metadata = {
                    "type": "metadata",
                    "session_id": session_id,
                    "question_answered": len(state.answers),
                    "status": "evaluating",
                    "total_questions": state.total_questions,
                    "questions_remaining": 0,
                    "all_completed": True
                }
                yield f"data: {json.dumps(metadata)}\n\n"

                # Trigger bulk evaluation
                if len(state.evaluations) < len(state.answers):
                    evaluated_state = interview_workflow.evaluate_all_answers(state)
                    interview_sessions[session_id] = evaluated_state
                    
                    # Send evaluation complete
                    eval_data = {
                        "type": "evaluation_complete",
                        "status": "evaluated"
                    }
                    yield f"data: {json.dumps(eval_data)}\n\n"
                
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
            else:
                # Generate next question
                question_id = len(state.questions) + 1
                category = interviewer_agent._determine_category(question_id, state.total_questions)
                
                # Send metadata
                metadata = {
                    "type": "metadata",
                    "session_id": session_id,
                    "question_answered": len(state.answers),
                    "status": "in_progress",
                    "total_questions": state.total_questions,
                    "questions_remaining": state.total_questions - len(state.answers),
                    "question_id": question_id,
                    "category": category
                }
                yield f"data: {json.dumps(metadata)}\n\n"

                # Stream the next question
                full_text = ""
                async for chunk in interviewer_agent.stream_next_question(state):
                    full_text += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

                # Save the complete question
                next_question = Question(
                    question_id=question_id,
                    question_text=full_text.strip(),
                    category=category,
                    timestamp=datetime.utcnow()
                )
                state.questions.append(next_question)
                state.current_question_id = next_question.question_id
                
                # Update stored session
                interview_sessions[session_id] = state

                yield f"data: {json.dumps({'type': 'done', 'question_text': full_text.strip()})}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
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
