'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { apiClient } from '@/lib/api-client'
import type { SessionHistoryItem } from '@/lib/types'

interface SessionHistoryProps {
  onNewInterview: () => void
  onViewSession?: (sessionId: string) => void
}

export function SessionHistory({ onNewInterview, onViewSession }: SessionHistoryProps) {
  const [sessions, setSessions] = useState<SessionHistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchHistory = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const data = await apiClient.getHistory()
        // Sort by created date, most recent first
        const sortedData = data.sort((a, b) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        )
        setSessions(sortedData)
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load session history'
        setError(errorMessage)
        console.error('Error fetching history:', err)
      } finally {
        setIsLoading(false)
      }
    }

    fetchHistory()
  }, [])

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-4">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto" />
          <p className="text-muted-foreground">Loading session history...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 gap-6">
      <div className="w-full max-w-2xl space-y-6">
        <div className="text-center space-y-2 mb-4">
          <h1 className="text-3xl font-bold">Session History</h1>
          <p className="text-muted-foreground">
            Review your past interviews and track your progress
          </p>
        </div>

        {error && (
          <Card className="bg-destructive/10 border-destructive/20">
            <CardContent className="pt-6">
              <p className="text-destructive text-center">{error}</p>
            </CardContent>
          </Card>
        )}

        {sessions.length === 0 ? (
          <Card>
            <CardContent className="pt-6 text-center space-y-4">
              <p className="text-muted-foreground">No interview sessions yet</p>
              <p className="text-sm text-muted-foreground">
                Start your first practice interview to see your history here
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {sessions.map((session) => {
              const formattedDate = new Date(session.created_at).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
              })

              return (
                <Card
                  key={session.session_id}
                  className="hover:border-primary/50 transition-colors cursor-pointer"
                  onClick={() => onViewSession?.(session.session_id)}
                >
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div className="space-y-1">
                        <p className="font-medium text-lg">{session.role}</p>
                        <p className="text-sm text-muted-foreground">
                          {session.seniority} • {formattedDate}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {session.questions_answered}/{session.total_questions} questions • {session.status}
                        </p>
                      </div>
                      <div className="text-right">
                        {session.overall_score !== null ? (
                          <p className="text-3xl font-bold text-primary">
                            {session.overall_score.toFixed(1)}
                            <span className="text-sm text-muted-foreground">/10</span>
                          </p>
                        ) : (
                          <p className="text-sm text-muted-foreground">
                            {session.status === 'completed' ? 'Evaluating...' : 'In Progress'}
                          </p>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}

        <Button onClick={onNewInterview} className="w-full" size="lg">
          Start New Interview
        </Button>
      </div>
    </div>
  )
}
