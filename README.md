# Mock Interview with Agents

## Overview

Mock Interview with Agents is an AI-powered platform designed to simulate realistic technical and behavioral interviews. It combines a modern Next.js frontend with a sophisticated Python backend using multi-agent architecture to provide intelligent questioning, real-time evaluation, and personalized feedback.

## Purpose

The goal of this project is to help job seekers and professionals improve their interview skills by providing:
- **Realistic Simulations**: Role-specific questions adapted to experience levels.
- **Objective Evaluation**: Scoring based on clarity, confidence, and relevance using fuzzy logic and NLP.
- **Actionable Feedback**: Detailed insights and recommendations for improvement.

## Architecture

The project is split into two main components:

### Backend (`/backend`)
- **Framework**: FastAPI
- **Agent Orchestration**: LangGraph (Multi-agent workflow)
- **NLP & Logic**: spaCy (Linguistic analysis) & scikit-fuzzy (Fuzzy logic scoring)
- **Agents**:
  - `InterviewerAgent`: Generates contextual questions.
  - `EvaluatorAgent`: Analyzes responses.
  - `FeedbackAgent`: Provides improvement tips.

### Frontend (`/web`)
- **Framework**: Next.js 16 (App Router) & React 19
- **Styling**: Tailwind CSS 4 & shadcn/ui
- **Features**: Interactive interview sessions, real-time progress, and visual feedback dashboards.

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.10+
- OpenAI or Anthropic API Key

## Contribution

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

