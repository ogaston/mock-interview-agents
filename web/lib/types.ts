// TypeScript interfaces matching backend Pydantic models

export type Seniority = "junior" | "mid" | "senior" | "lead"
export type InterviewStatus = "in_progress" | "evaluated" | "completed"

// Request Models
export interface StartInterviewRequest {
  role: string
  seniority: Seniority
  focus_areas?: string[]
}

export interface SubmitAnswerRequest {
  answer: string  // min 10 chars
}

// Response Models
export interface Question {
  question_id: number
  question_text: string
  category: string | null
  timestamp: string
}

export interface EvaluationScore {
  clarity: number       // 0-10
  confidence: number    // 0-10
  relevance: number     // 0-10
  overall_score: number // 0-10
}

export interface NLPFeatures {
  word_count?: number
  sentence_count?: number
  avg_sentence_length?: number
  sentiment_score?: number
  confidence_indicators?: number
  filler_words_count?: number
  technical_terms_count?: number
  coherence_score?: number
  complexity_score?: number
}

export interface AnswerEvaluation {
  question_id: number
  answer_text: string
  scores: EvaluationScore
  nlp_features: NLPFeatures
  timestamp: string
}

export interface FeedbackItem {
  category: string
  strength: string | null
  weakness: string | null
  suggestions: string[]
}

export interface InterviewFeedback {
  overall_score: number
  overall_summary: string
  feedback_items: FeedbackItem[]
  recommended_resources: string[]
  strengths: string[]
  areas_for_improvement: string[]
}

export interface InterviewSessionResponse {
  session_id: string
  role: string
  seniority: string
  current_question: Question
  total_questions: number
  status: InterviewStatus
  created_at: string
}

export interface AnswerResponse {
  session_id: string
  question_answered: number
  evaluation: EvaluationScore | null
  next_question: Question | null
  status: InterviewStatus
  total_questions: number
  questions_remaining: number
}

export interface FeedbackResponse {
  session_id: string
  feedback: InterviewFeedback
  all_evaluations: AnswerEvaluation[]
  interview_duration_minutes: number | null
}

export interface SessionHistoryItem {
  session_id: string
  role: string
  seniority: string
  status: string
  questions_answered: number
  total_questions: number
  overall_score: number | null
  created_at: string
}

export interface HealthCheckResponse {
  status: string
  environment: string
  llm_provider: string
}

// Error Response
export interface APIError {
  detail: string
}
