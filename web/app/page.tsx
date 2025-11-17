'use client'

import { useState, useEffect } from 'react'
import { InterviewSetup } from '@/components/interview-setup'
import { InterviewSession } from '@/components/interview-session'
import { FeedbackView } from '@/components/feedback-view'
import { SessionHistory } from '@/components/session-history'
import { apiClient } from '@/lib/api-client'
import type { InterviewSessionResponse } from '@/lib/types'

type ViewType = 'setup' | 'session' | 'feedback' | 'history'

export default function Home() {
  const [currentView, setCurrentView] = useState<ViewType>('setup')
  const [sessionData, setSessionData] = useState<InterviewSessionResponse | null>(null)
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [hasHistory, setHasHistory] = useState(false)

  // Check if there's history on mount
  useEffect(() => {
    const checkHistory = async () => {
      try {
        const history = await apiClient.getHistory()
        setHasHistory(history.length > 0)
      } catch (err) {
        console.error('Error checking history:', err)
      }
    }
    checkHistory()
  }, [])

  const handleStartInterview = (data: InterviewSessionResponse) => {
    setSessionData(data)
    setCurrentSessionId(data.session_id)
    setCurrentView('session')
  }

  const handleCompleteInterview = (sessionId: string) => {
    setCurrentSessionId(sessionId)
    setCurrentView('feedback')
    setHasHistory(true)
  }

  const handleViewHistory = () => {
    setCurrentView('history')
  }

  const handleNewInterview = () => {
    setSessionData(null)
    setCurrentSessionId(null)
    setCurrentView('setup')
  }

  const handleViewSession = (sessionId: string) => {
    setCurrentSessionId(sessionId)
    setCurrentView('feedback')
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      {currentView === 'setup' && (
        <InterviewSetup
          onStart={handleStartInterview}
          onViewHistory={handleViewHistory}
          hasHistory={hasHistory}
        />
      )}
      {currentView === 'session' && sessionData && (
        <InterviewSession
          data={sessionData}
          onComplete={handleCompleteInterview}
        />
      )}
      {currentView === 'feedback' && currentSessionId && (
        <FeedbackView
          sessionId={currentSessionId}
          onNewInterview={handleNewInterview}
        />
      )}
      {currentView === 'history' && (
        <SessionHistory
          onNewInterview={handleNewInterview}
          onViewSession={handleViewSession}
        />
      )}
    </main>
  )
}
