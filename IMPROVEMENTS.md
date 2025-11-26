# Improvements & Future Enhancements

This document tracks potential improvements and enhancements for the Mock Interview Agents project.

## Evaluation Improvements

### Async Background Evaluation
**Status:** Not Implemented  
**Priority:** Medium  
**Description:**  
Implement asynchronous evaluation of answers in the background while showing the next question to the user. This would provide the best of both worlds:
- Users don't wait for evaluation before seeing the next question (better UX)
- Evaluations can still be used to adapt subsequent questions (adaptive interviews)
- Real-time feedback can be shown as evaluations complete

**Implementation Approach:**
- Use background tasks (e.g., FastAPI BackgroundTasks or Celery) to evaluate answers asynchronously
- Store evaluation results in the state as they complete
- Update the frontend to display evaluation scores when available (via polling or WebSocket)
- Modify question generation to use available evaluations for adaptive difficulty

**Benefits:**
- Improved user experience (no blocking waits)
- Enables adaptive question generation based on performance
- Real-time feedback without interrupting the interview flow

**Considerations:**
- Need to handle race conditions if user submits answers faster than evaluations complete
- May need to queue evaluations if system is under heavy load
- Frontend needs to handle partial evaluation states gracefully

