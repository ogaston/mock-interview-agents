'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { apiClient } from '@/lib/api-client'
import type { FeedbackResponse } from '@/lib/types'

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
          <p className="text-muted-foreground">Generating comprehensive feedback...</p>
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
              <p className="text-destructive">{error || 'Failed to load feedback'}</p>
              <Button onClick={onNewInterview}>Start New Interview</Button>
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
          <h1 className="text-3xl font-bold">Interview Complete!</h1>
          <p className="text-muted-foreground">
            Here's your detailed feedback and recommendations
          </p>
        </div>

        {/* Overall Score */}
        <Card className="bg-gradient-to-br from-primary/5 to-primary/10 border-primary/20">
          <CardHeader>
            <CardTitle>Overall Performance</CardTitle>
            <CardDescription>{feedbackData.feedback.overall_summary}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center">
              <div className="text-5xl font-bold text-primary">
                {overallScore.toFixed(1)}
                <span className="text-2xl">/10</span>
              </div>
              {feedbackData.interview_duration_minutes && (
                <p className="text-sm text-muted-foreground mt-2">
                  Completed in {feedbackData.interview_duration_minutes} minutes
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Strengths */}
        {feedbackData.feedback.strengths.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Your Strengths</CardTitle>
              <CardDescription>Areas where you excelled</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {feedbackData.feedback.strengths.map((strength, index) => (
                  <li key={index} className="flex gap-3">
                    <span className="text-green-600">✓</span>
                    <p>{strength}</p>
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
              <CardTitle>Areas for Improvement</CardTitle>
              <CardDescription>Focus on these to enhance your performance</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {feedbackData.feedback.areas_for_improvement.map((area, index) => (
                  <li key={index} className="flex gap-3">
                    <span className="text-primary">→</span>
                    <p>{area}</p>
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
              <CardTitle>Detailed Feedback by Category</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {feedbackData.feedback.feedback_items.map((item, index) => (
                <div key={index} className="border-l-2 border-primary pl-4 space-y-2">
                  <h4 className="font-semibold">{item.category}</h4>
                  {item.strength && (
                    <p className="text-sm">
                      <span className="font-medium text-green-600">Strength:</span> {item.strength}
                    </p>
                  )}
                  {item.weakness && (
                    <p className="text-sm">
                      <span className="font-medium text-amber-600">Area to improve:</span> {item.weakness}
                    </p>
                  )}
                  {item.suggestions.length > 0 && (
                    <div className="text-sm">
                      <span className="font-medium">Suggestions:</span>
                      <ul className="list-disc list-inside ml-2 mt-1">
                        {item.suggestions.map((suggestion, i) => (
                          <li key={i}>{suggestion}</li>
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
              <CardTitle>Recommended Resources</CardTitle>
              <CardDescription>Continue your learning journey</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {feedbackData.feedback.recommended_resources.map((resource, index) => (
                  <li key={index} className="flex gap-3">
                    <span className="text-primary">📚</span>
                    <p>{resource}</p>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          <Button onClick={onNewInterview} className="flex-1" size="lg">
            Start Another Interview
          </Button>
        </div>
      </div>
    </div>
  )
}
