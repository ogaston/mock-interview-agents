'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { apiClient } from '@/lib/api-client'
import type { FeedbackResponse } from '@/lib/types'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface FeedbackViewProps {
  sessionId: string
  onNewInterview: () => void
}

export function FeedbackView({ sessionId, onNewInterview }: FeedbackViewProps) {
  const [feedbackData, setFeedbackData] = useState<FeedbackResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchFeedback = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const data = await apiClient.getFeedback(sessionId)
        setFeedbackData(data)
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load feedback'
        setError(errorMessage)
        console.error('Error fetching feedback:', err)
      } finally {
        setIsLoading(false)
      }
    }

    fetchFeedback()
  }, [sessionId])

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-4">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto" />
          <p className="text-muted-foreground">Generando retroalimentación completa...</p>
        </div>
      </div>
    )
  }

  if (error || !feedbackData) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="text-center space-y-4">
              <p className="text-destructive">{error || 'Error al cargar la retroalimentación'}</p>
              <Button onClick={onNewInterview}>Iniciar Nueva Entrevista</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const overallScore = feedbackData.feedback.overall_score

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 gap-6">
      <div className="w-full max-w-2xl space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold">¡Entrevista Completa!</h1>
          <p className="text-muted-foreground">
            Aquí está tu retroalimentación detallada y recomendaciones
          </p>
        </div>

        {/* Overall Score */}
        <Card className="bg-gradient-to-br from-primary/5 to-primary/10 border-primary/20">
          <CardHeader>
            <CardTitle>Desempeño General</CardTitle>
            <CardDescription className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {feedbackData.feedback.overall_summary}
              </ReactMarkdown>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center">
              <div className="text-5xl font-bold text-primary">
                {overallScore.toFixed(1)}
                <span className="text-2xl">/10</span>
              </div>
              {feedbackData.interview_duration_minutes && (
                <p className="text-sm text-muted-foreground mt-2">
                  Completado en {feedbackData.interview_duration_minutes} minutos
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Strengths */}
        {feedbackData.feedback.strengths.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Tus Fortalezas</CardTitle>
              <CardDescription>Áreas en las que sobresaliste</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {feedbackData.feedback.strengths.map((strength, index) => (
                  <li key={index} className="flex gap-3">
                    <span className="text-green-600">✓</span>
                    <div className="prose prose-sm dark:prose-invert max-w-none flex-1">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {strength}
                      </ReactMarkdown>
                    </div>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Areas for Improvement */}
        {feedbackData.feedback.areas_for_improvement.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Áreas de Mejora</CardTitle>
              <CardDescription>Enfócate en estas para mejorar tu desempeño</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {feedbackData.feedback.areas_for_improvement.map((area, index) => (
                  <li key={index} className="flex gap-3">
                    <span className="text-primary">→</span>
                    <div className="prose prose-sm dark:prose-invert max-w-none flex-1">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {area}
                      </ReactMarkdown>
                    </div>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Detailed Feedback by Category */}
        {feedbackData.feedback.feedback_items.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Retroalimentación Detallada por Categoría</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {feedbackData.feedback.feedback_items.map((item, index) => (
                <div key={index} className="border-l-2 border-primary pl-4 space-y-2">
                  <h4 className="font-semibold">{item.category}</h4>
                  {item.strength && (
                    <div className="text-sm">
                      <span className="font-medium text-green-600">Fortaleza:</span>
                      <div className="prose prose-sm dark:prose-invert max-w-none inline">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {item.strength}
                        </ReactMarkdown>
                      </div>
                    </div>
                  )}
                  {item.weakness && (
                    <div className="text-sm">
                      <span className="font-medium text-amber-600">Área a mejorar:</span>
                      <div className="prose prose-sm dark:prose-invert max-w-none inline">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {item.weakness}
                        </ReactMarkdown>
                      </div>
                    </div>
                  )}
                  {item.suggestions.length > 0 && (
                    <div className="text-sm">
                      <span className="font-medium">Sugerencias:</span>
                      <ul className="list-disc list-inside ml-2 mt-1">
                        {item.suggestions.map((suggestion, i) => (
                          <li key={i}>
                            <div className="prose prose-sm dark:prose-invert max-w-none inline">
                              {/* <ReactMarkdown remarkPlugins={[remarkGfm]}> */}
                                {suggestion}
                              {/* </ReactMarkdown> */}
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Recommended Resources */}
        {feedbackData.feedback.recommended_resources.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Recursos Recomendados</CardTitle>
              <CardDescription>Continúa tu viaje de aprendizaje</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {feedbackData.feedback.recommended_resources.map((resource, index) => (
                  <li key={index} className="flex gap-3">
                    <span className="text-primary">📚</span>
                    <div className="prose prose-sm dark:prose-invert max-w-none flex-1">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {resource}
                      </ReactMarkdown>
                    </div>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          <Button onClick={onNewInterview} className="flex-1" size="lg">
            Iniciar Otra Entrevista
          </Button>
        </div>
      </div>
    </div>
  )
}
