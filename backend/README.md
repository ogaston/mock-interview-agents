# Backend - Mock Interview Agent

AI-powered interview training agent built with **LangGraph**, **FastAPI**, **NLP**, and **Fuzzy Logic**.

## Overview

This backend provides a comprehensive mock interview platform that uses multi-agent architecture to simulate realistic interview experiences. The system generates contextual questions, evaluates responses using fuzzy logic, and provides personalized feedback.

### Key Features

- **Intelligent Question Generation**: LLM-powered contextual questions based on role and seniority
- **Multi-Agent Architecture**: Deliberative workflow using LangGraph
- **Fuzzy Logic Evaluation**: Sophisticated scoring for clarity, confidence, and relevance
- **NLP Analysis**: Deep linguistic feature extraction using spaCy
- **Personalized Feedback**: AI-generated improvement recommendations and resources
- **No Database Required**: In-memory session storage for simplicity

## Architecture

### Three-Agent System

1. **InterviewerAgent** (LLM-based)
   - Generates contextual interview questions
   - Adapts difficulty based on candidate performance
   - Covers opening, foundational, intermediate, advanced, and closing questions

2. **EvaluatorAgent** (Fuzzy Logic + NLP)
   - Extracts linguistic features (coherence, sentiment, complexity, etc.)
   - Applies fuzzy logic rules for scoring
   - Evaluates clarity, confidence, and relevance

3. **FeedbackAgent** (LLM-based)
   - Generates comprehensive performance analysis
   - Provides specific strengths and improvement areas
   - Recommends learning resources and practice materials

### LangGraph Workflow

```
Start Interview → Generate Question → [User Answers] → Evaluate Answer →
  ↓                                                           ↓
  └─────────────────← Generate Next Question ←───────────────┘
                            ↓ (if complete)
                      Generate Feedback → End
```

## Technology Stack

- **Framework**: FastAPI 0.115+
- **Orchestration**: LangGraph 0.2+
- **LLM Integration**: LangChain (OpenAI or Anthropic)
- **NLP**: spaCy 3.8+
- **Fuzzy Logic**: scikit-fuzzy 0.5+
- **ML**: Transformers, PyTorch (optional for advanced NLP)

## Getting Started

### Prerequisites

- Python 3.10 or higher
- OpenAI API key OR Anthropic API key

### Installation

1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Download spaCy language model**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and add your API key:
   ```env
   # For OpenAI
   OPENAI_API_KEY=sk-your-key-here
   LLM_PROVIDER=openai

   # OR for Anthropic
   # ANTHROPIC_API_KEY=your-key-here
   # LLM_PROVIDER=anthropic
   ```

### Running the Server

```bash
# Development mode (with auto-reload)
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### 1. Start Interview
```http
POST /api/interviews/start
Content-Type: application/json

{
  "role": "Software Engineer",
  "seniority": "mid",
  "focus_areas": ["algorithms", "system design"]  // optional
}
```

**Response**:
```json
{
  "session_id": "uuid-here",
  "role": "Software Engineer",
  "seniority": "mid",
  "current_question": {
    "question_id": 1,
    "question_text": "Can you explain the difference between...",
    "category": "opening"
  },
  "total_questions": 10,
  "status": "in_progress"
}
```

### 2. Submit Answer
```http
POST /api/interviews/{session_id}/answer
Content-Type: application/json

{
  "answer": "Your detailed answer here..."
}
```

**Response**:
```json
{
  "session_id": "uuid-here",
  "question_answered": 1,
  "evaluation": {
    "clarity": 7.5,
    "confidence": 8.2,
    "relevance": 6.8,
    "overall_score": 7.5
  },
  "next_question": {
    "question_id": 2,
    "question_text": "Next question...",
    "category": "foundational"
  },
  "status": "in_progress",
  "questions_remaining": 9
}
```

### 3. Get Feedback
```http
GET /api/interviews/{session_id}/feedback
```

**Response**:
```json
{
  "session_id": "uuid-here",
  "feedback": {
    "overall_score": 7.5,
    "overall_summary": "Strong performance with good technical knowledge...",
    "strengths": [
      "Clear communication style",
      "Good grasp of fundamental concepts"
    ],
    "areas_for_improvement": [
      "Could provide more concrete examples",
      "Practice system design patterns"
    ],
    "feedback_items": [
      {
        "category": "Communication Skills",
        "strength": "Well-structured responses",
        "weakness": "Occasional use of filler words",
        "suggestions": [
          "Practice speaking more slowly",
          "Prepare example stories in advance"
        ]
      }
    ],
    "recommended_resources": [
      "Book: Cracking the Coding Interview",
      "Platform: LeetCode for algorithm practice"
    ]
  },
  "all_evaluations": [...],
  "interview_duration_minutes": 15.5
}
```

### 4. Get Interview History
```http
GET /api/interviews/history
```

### 5. Complete Interview Early
```http
POST /api/interviews/{session_id}/complete
```

### 6. Delete Interview
```http
DELETE /api/interviews/{session_id}
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Settings and configuration
│   ├── api/
│   │   └── routes/
│   │       └── interviews.py   # API endpoints
│   ├── agents/
│   │   ├── interviewer.py      # Question generation agent
│   │   ├── evaluator.py        # Answer evaluation agent
│   │   └── feedback.py         # Feedback generation agent
│   ├── graph/
│   │   └── workflow.py         # LangGraph orchestration
│   ├── models/
│   │   └── schemas.py          # Pydantic models
│   └── services/
│       ├── nlp_service.py      # NLP feature extraction
│       └── fuzzy_service.py    # Fuzzy logic evaluation
├── requirements.txt
├── .env.example
└── README.md
```

## Configuration

Environment variables in `.env`:

```env
# LLM Provider (openai or anthropic)
LLM_PROVIDER=openai

# OpenAI Configuration
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini

# Anthropic Configuration (alternative)
# ANTHROPIC_API_KEY=your_key_here
# ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Application Settings
ENVIRONMENT=development
LOG_LEVEL=INFO

# Interview Settings
MAX_QUESTIONS_PER_INTERVIEW=10
DEFAULT_INTERVIEW_DURATION_MINUTES=30

# CORS Settings
CORS_ALLOW_ORIGINS=*  # Comma-separated list (e.g., "http://localhost:3000,http://localhost:3001") or "*" for all
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=*  # Comma-separated list (e.g., "GET,POST,PUT,DELETE") or "*" for all
CORS_ALLOW_HEADERS=*  # Comma-separated list (e.g., "Content-Type,Authorization") or "*" for all
```

## Example Usage

### Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Start interview
response = requests.post(f"{BASE_URL}/api/interviews/start", json={
    "role": "Backend Engineer",
    "seniority": "senior",
    "focus_areas": ["distributed systems", "databases"]
})
session = response.json()
session_id = session["session_id"]
print(f"Question 1: {session['current_question']['question_text']}")

# 2. Submit answer
answer_response = requests.post(
    f"{BASE_URL}/api/interviews/{session_id}/answer",
    json={"answer": "My answer is..."}
)
result = answer_response.json()
print(f"Score: {result['evaluation']['overall_score']}/10")
print(f"Next Question: {result['next_question']['question_text']}")

# 3. Get final feedback (after completing all questions)
feedback_response = requests.get(f"{BASE_URL}/api/interviews/{session_id}/feedback")
feedback = feedback_response.json()
print(f"Overall Score: {feedback['feedback']['overall_score']}/10")
print(f"Summary: {feedback['feedback']['overall_summary']}")
```

### cURL Examples

```bash
# Start interview
curl -X POST http://localhost:8000/api/interviews/start \
  -H "Content-Type: application/json" \
  -d '{"role": "Software Engineer", "seniority": "mid"}'

# Submit answer
curl -X POST http://localhost:8000/api/interviews/{session_id}/answer \
  -H "Content-Type: application/json" \
  -d '{"answer": "My detailed answer..."}'

# Get feedback
curl http://localhost:8000/api/interviews/{session_id}/feedback
```

## Evaluation Metrics

### NLP Features Extracted
- Word count and sentence count
- Average sentence length
- Sentiment score (-1 to 1)
- Confidence indicators count
- Filler words count
- Technical terms count
- Coherence score (0 to 1)
- Complexity score (0 to 1)

### Fuzzy Logic Scoring
- **Clarity** (0-10): Based on coherence and filler word usage
- **Confidence** (0-10): Based on confidence indicators and response length
- **Relevance** (0-10): Based on technical depth and vocabulary complexity
- **Overall Score** (0-10): Weighted average (30% clarity + 30% confidence + 40% relevance)

## Development

### Adding New Features

1. **Modify LangGraph workflow**: Edit `app/graph/workflow.py`
2. **Add new agents**: Create in `app/agents/`
3. **Extend NLP analysis**: Update `app/services/nlp_service.py`
4. **Adjust fuzzy rules**: Modify `app/services/fuzzy_service.py`
5. **Add API endpoints**: Extend `app/api/routes/interviews.py`

### Testing

```bash
# Run the server and test with interactive docs
# Navigate to http://localhost:8000/docs
```

## Troubleshooting

### Common Issues

1. **spaCy model not found**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

2. **API key errors**: Ensure `.env` file exists and has valid API key

3. **Import errors**: Make sure you're running from the backend directory

4. **Port already in use**: Change port in `app/main.py` or kill process on port 8000

## Future Enhancements

- [ ] Add database persistence (PostgreSQL/MongoDB)
- [ ] Implement user authentication
- [ ] Add voice-to-text for verbal interview practice
- [ ] Integrate LlamaIndex for role-specific knowledge bases
- [ ] Add WebSocket support for real-time interviews
- [ ] Implement interview session recording/replay
- [ ] Add multi-language support
- [ ] Create admin dashboard for analytics

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
