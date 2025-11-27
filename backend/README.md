# Backend - Mock Interview Agent

AI-powered interview training agent built with **LangGraph**, **FastAPI**, **NLP**, and **Fuzzy Logic**.

## Overview

This backend provides a comprehensive mock interview platform that uses multi-agent architecture to simulate realistic interview experiences. The system generates contextual questions, evaluates responses using fuzzy logic, and provides personalized feedback.

### Key Features

- **Intelligent Question Generation**: LLM-powered contextual questions based on role and seniority
- **Multi-Agent Architecture**: Deliberative workflow using LangGraph
- **Fuzzy Logic Evaluation**: Sophisticated scoring for clarity, confidence, and relevance
- **NLP Analysis**: Deep linguistic feature extraction using spaCy
- **Personalized Feedback**: AI-generated improvement recommendations

## Architecture

### Agent System

1. **InterviewerAgent** (LLM): Generates contextual interview questions and adapts difficulty.
2. **EvaluatorAgent** (Fuzzy Logic + NLP): Extracts linguistic features and applies fuzzy logic rules for scoring.
3. **FeedbackAgent** (LLM): Generates comprehensive performance analysis and improvement recommendations.

### Tech Stack

- **Framework**: FastAPI 0.115+
- **Orchestration**: LangGraph 0.2+
- **LLM Integration**: LangChain (OpenAI or Anthropic)
- **NLP**: spaCy 3.8+
- **Fuzzy Logic**: scikit-fuzzy 0.5+

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
   python -m spacy download es_core_news_sm
   ```

3. **Configure environment**:
   Copy a `.env` file from `.env.example`
   ```sh
   cp .env.example .env
   ```

### Running

```bash
# Development mode (with auto-reload)
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000.

## Evaluation Metric

- **Clarity** (0-10): Based on coherence and filler word usage
- **Confidence** (0-10): Based on confidence indicators and response length
- **Relevance** (0-10): Based on technical depth and vocabulary complexity
- **Overall Score** (0-10): Weighted average (30% clarity + 30% confidence + 40% relevance)

### Fuzzy Logic Rules

The evaluation system uses fuzzy inference with three rule sets. All inputs are normalized to a 0-10 scale.

#### Input Variables

| Variable | Low | Medium | High |
|----------|-----|--------|------|
| **Word Count** | 0-4 | 3-7 | 6-10 |
| **Coherence** | 0-4 | 3-7 | 6-10 |
| **Confidence Level** | 0-4 | 3-7 | 6-10 |
| **Technical Depth** | 0-4 | 3-7 | 6-10 |
| **Filler Ratio** | 0-3 (good) | 2-8 | 7-10 (bad) |
| **Complexity** | 0-4 | 3-7 | 6-10 |

#### Clarity Rules

| Coherence | Filler Ratio | Output Score |
|-----------|--------------|--------------|
| High | Low | Excellent |
| High | Medium | Good |
| Medium | Low | Good |
| Medium | Medium | Fair |
| Low | *any* | Poor |
| *any* | High | Poor |

#### Confidence Rules

| Confidence Level | Word Count | Output Score |
|------------------|------------|--------------|
| High | High | Excellent |
| High | Medium | Good |
| Medium | Medium | Good |
| Medium | Low | Fair |
| Low | *any* | Poor |

#### Relevance Rules

| Technical Depth | Complexity | Output Score |
|-----------------|------------|--------------|
| High | High | Excellent |
| High | Medium | Good |
| Medium | Medium | Good |
| Medium | Low | Fair |
| Low | *any* | Poor |

#### Output Score Levels

| Level | Score Range |
|-------|-------------|
| Poor | 0-3 |
| Fair | 2-6 |
| Good | 5-9 |
| Excellent | 8-10 |

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
