'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { apiClient } from '@/lib/api-client'
import type { InterviewSessionResponse, Question, EvaluationScore } from '@/lib/types'

interface InterviewSessionProps {
  data: InterviewSessionResponse
  onComplete: (sessionId: string) => void
}

export function InterviewSession({ data, onComplete }: InterviewSessionProps) {
  const [currentQuestion, setCurrentQuestion] = useState<Question>(data.current_question)
  const [currentAnswer, setCurrentAnswer] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [questionsAnswered, setQuestionsAnswered] = useState(0)
  const [lastEvaluation, setLastEvaluation] = useState<EvaluationScore | null>(null)
  const [showEvaluation, setShowEvaluation] = useState(false)

  const handleNext = async () => {
    if (!currentAnswer.trim() || currentAnswer.length < 10) {
      setError('Please provide an answer of at least 10 characters.')
      return
    }

    setIsProcessing(true)
    setError(null)
    setShowEvaluation(false)

    try {
      const response = await apiClient.submitAnswer(data.session_id, {
        answer: currentAnswer,
      })

      setLastEvaluation(response.evaluation)
      setShowEvaluation(true)
      setQuestionsAnswered(response.question_answered)

      // Wait a moment to show evaluation before moving to next question or completing
      await new Promise((resolve) => setTimeout(resolve, 1500))

      if (response.status === 'completed' || response.next_question === null) {
        // Interview complete
        onComplete(data.session_id)
      } else {
        // Move to next question
        setCurrentQuestion(response.next_question)
        setCurrentAnswer('')
        setShowEvaluation(false)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to submit answer'
      setError(errorMessage)
      console.error('Error submitting answer:', err)
    } finally {
      setIsProcessing(false)
    }
  }

  const progress = ((questionsAnswered + 1) / data.total_questions) * 100

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 gap-6">
      <div className="w-full max-w-2xl">
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-2xl font-bold">Interview in Progress</h2>
            <span className="text-sm text-muted-foreground">
              Question {questionsAnswered + 1} of {data.total_questions}
            </span>
          </div>
          <div className="w-full bg-secondary rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        <Card>
          <CardContent className="pt-8 space-y-6">
            <div className="space-y-4">
              <div>
                <h3 className="text-xl font-semibold leading-relaxed">
                  {currentQuestion.question_text}
                </h3>
                {currentQuestion.category && (
                  <span className="text-xs text-muted-foreground mt-1 inline-block">
                    Category: {currentQuestion.category}
                  </span>
                )}
              </div>
              <Textarea
                placeholder="Your answer here... (minimum 10 characters)"
                value={currentAnswer}
                onChange={(e) => setCurrentAnswer(e.target.value)}
                className="min-h-32 resize-none"
                disabled={isProcessing}
              />
              {currentAnswer.length > 0 && currentAnswer.length < 10 && (
                <p className="text-xs text-muted-foreground">
                  {10 - currentAnswer.length} more characters needed
                </p>
              )}
            </div>

            {showEvaluation && lastEvaluation && (
              <div className="p-4 rounded-lg bg-primary/5 border border-primary/20 space-y-2">
                <h4 className="font-semibold text-sm">Answer Evaluation:</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>Clarity: <span className="font-semibold">{lastEvaluation.clarity.toFixed(1)}/10</span></div>
                  <div>Confidence: <span className="font-semibold">{lastEvaluation.confidence.toFixed(1)}/10</span></div>
                  <div>Relevance: <span className="font-semibold">{lastEvaluation.relevance.toFixed(1)}/10</span></div>
                  <div>Overall: <span className="font-semibold">{lastEvaluation.overall_score.toFixed(1)}/10</span></div>
                </div>
              </div>
            )}

            {error && (
              <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
                {error}
              </div>
            )}

            <div className="flex gap-3">
              <Button
                onClick={handleNext}
                disabled={!currentAnswer.trim() || currentAnswer.length < 10 || isProcessing}
                className="flex-1"
              >
                {isProcessing
                  ? 'Evaluating...'
                  : questionsAnswered === data.total_questions - 1
                    ? 'Complete Interview'
                    : 'Submit & Continue'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
