'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { apiClient } from '@/lib/api-client'
import type { InterviewSessionResponse, Question, AnswerEvaluation } from '@/lib/types'

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
  const [status, setStatus] = useState<'in_progress' | 'evaluated' | 'completed'>(data.status)
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [evaluations, setEvaluations] = useState<AnswerEvaluation[]>([])

  // Fetch evaluations when status becomes 'evaluated'
  useEffect(() => {
    if (status === 'evaluated' && evaluations.length === 0) {
      fetchEvaluations()
    }
  }, [status])

  const fetchEvaluations = async () => {
    try {
      const feedback = await apiClient.getFeedback(data.session_id)
      setEvaluations(feedback.all_evaluations)
    } catch (err) {
      console.error('Error fetching evaluations:', err)
    }
  }

  const handleNext = async () => {
    if (!currentAnswer.trim() || currentAnswer.length < 10) {
      setError('Por favor proporciona una respuesta de al menos 10 caracteres.')
      return
    }

    setIsProcessing(true)
    setError(null)

    try {
      const response = await apiClient.submitAnswer(data.session_id, {
        answer: currentAnswer,
      })

      setQuestionsAnswered(response.question_answered)
      setStatus(response.status)

      // Check if all answers are submitted
      if (response.questions_remaining === 0) {
        // All answers submitted - evaluation should be complete synchronously
        setIsEvaluating(false)
        // Status should already be 'evaluated' from the API response
      } else if (response.next_question) {
        // Move to next question
        setCurrentQuestion(response.next_question)
        setCurrentAnswer('')
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al enviar la respuesta'
      setError(errorMessage)
      console.error('Error submitting answer:', err)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleGetFeedback = async () => {
    setIsProcessing(true)
    setError(null)

    try {
      const feedback = await apiClient.getFeedback(data.session_id)
      // Call onComplete with session ID to show feedback
      onComplete(data.session_id)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al obtener la retroalimentación'
      setError(errorMessage)
      console.error('Error getting feedback:', err)
    } finally {
      setIsProcessing(false)
    }
  }

  // Calculate progress - use questionsAnswered directly when evaluated, otherwise add 1 for current question
  const currentQuestionNumber = status === 'evaluated' ? questionsAnswered : questionsAnswered + 1
  const progress = (currentQuestionNumber / data.total_questions) * 100

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 gap-6">
      <div className="w-full max-w-2xl">
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-2xl font-bold">
              {status === 'evaluated' ? 'Entrevista Completa' : 'Entrevista en Progreso'}
            </h2>
            <span className="text-sm text-muted-foreground">
              {status === 'evaluated' 
                ? `${questionsAnswered} preguntas respondidas`
                : `Pregunta ${currentQuestionNumber} de ${data.total_questions}`
              }
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
            {status === 'evaluated' ? (
              // Show evaluation scores and feedback button
              <div className="space-y-6">
                <div className="p-4 rounded-lg bg-primary/5 border border-primary/20">
                  <h3 className="text-xl font-semibold mb-4 text-center">¡Todas las Respuestas Evaluadas!</h3>
                  
                  {evaluations.length > 0 ? (
                    <div className="space-y-3 mb-4">
                      {evaluations.map((evaluation, index) => (
                        <div 
                          key={evaluation.question_id}
                          className="p-3 rounded-lg bg-background border border-border"
                        >
                          <div className="flex justify-between items-center mb-2">
                            <span className="font-semibold text-sm">Pregunta {evaluation.question_id}</span>
                            <span className="text-xs text-muted-foreground">
                              General: {evaluation.scores.overall_score.toFixed(1)}/10
                            </span>
                          </div>
                          <div className="grid grid-cols-3 gap-2 text-xs">
                            <div>
                              <span className="text-muted-foreground">Claridad:</span>
                              <span className="ml-1 font-semibold">{evaluation.scores.clarity.toFixed(1)}/10</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Confianza:</span>
                              <span className="ml-1 font-semibold">{evaluation.scores.confidence.toFixed(1)}/10</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Relevancia:</span>
                              <span className="ml-1 font-semibold">{evaluation.scores.relevance.toFixed(1)}/10</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-center mb-4">Cargando evaluaciones...</p>
                  )}

                  <p className="text-muted-foreground text-center text-sm">
                    Haz clic en el botón de abajo para ver tu retroalimentación completa.
                  </p>
                </div>
                <Button
                  onClick={handleGetFeedback}
                  disabled={isProcessing}
                  className="w-full"
                  size="lg"
                >
                  {isProcessing ? 'Cargando Retroalimentación...' : 'Obtener Retroalimentación Detallada'}
                </Button>
              </div>
            ) : isEvaluating ? (
              // Show evaluating state
              <div className="space-y-4 text-center">
                <div className="p-6 rounded-lg bg-primary/5 border border-primary/20">
                  <h3 className="text-xl font-semibold mb-2">Evaluando tus Respuestas</h3>
                  <p className="text-muted-foreground">
                    Por favor espera mientras evaluamos todas tus respuestas...
                  </p>
                </div>
              </div>
            ) : (
              // Show question and answer input
              <>
                <div className="space-y-4">
                  <div>
                    <h3 className="text-xl font-semibold leading-relaxed">
                      {currentQuestion.question_text}
                    </h3>
                    {currentQuestion.category && (
                      <span className="text-xs text-muted-foreground mt-1 inline-block">
                        Categoría: {currentQuestion.category}
                      </span>
                    )}
                  </div>
                  <Textarea
                    placeholder="Tu respuesta aquí... (mínimo 10 caracteres)"
                    value={currentAnswer}
                    onChange={(e) => setCurrentAnswer(e.target.value)}
                    className="min-h-32 resize-none"
                    disabled={isProcessing}
                  />
                  {currentAnswer.length > 0 && currentAnswer.length < 10 && (
                    <p className="text-xs text-muted-foreground">
                      {10 - currentAnswer.length} caracteres más necesarios
                    </p>
                  )}
                </div>

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
                      ? 'Enviando...'
                      : questionsAnswered === data.total_questions - 1
                        ? 'Enviar Respuesta Final'
                        : 'Enviar y Continuar'}
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
