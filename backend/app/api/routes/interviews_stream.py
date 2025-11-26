"""
FastAPI routes for streaming interview operations.
"""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from app.models.schemas import (
    StartInterviewRequest,
    SubmitAnswerRequest
)
from app.graph.workflow import interview_workflow
from app.agents.interviewer import interviewer_agent
from app.config import settings
from app.store import interview_sessions
import json

router = APIRouter(prefix="/api/interviews/stream", tags=["interviews-stream"])


@router.post("/start")
async def start_interview_stream(request: StartInterviewRequest):
    """
    Start a new interview session with streaming question generation.

    Returns session metadata followed by streamed question text.
    """
    try:
        # Start the interview workflow 
        state = interview_workflow.start_interview_incremental(
            role=request.role,
            seniority=request.seniority,
            focus_areas=request.focus_areas,
            total_questions=settings.max_questions_per_interview,
            generate_first_question=False
        )

        # Store session
        interview_sessions[state.session_id] = state

        async def generate():
            nonlocal state
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

            # Add the streamed question to state using workflow helper
            state = interview_workflow.add_streamed_question(
                state=state,
                question_text=full_text,
                question_id=1,
                category="opening"
            )
            
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


@router.post("/{session_id}/answer")
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
            nonlocal state
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

                # Add the streamed question to state using workflow helper
                state = interview_workflow.add_streamed_question(
                    state=state,
                    question_text=full_text,
                    question_id=question_id,
                    category=category
                )
                
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

