'use client'

import { useState, useEffect } from 'react'
import { InterviewSetup } from '@/components/interview-setup'
import { InterviewSession } from '@/components/interview-session'
import { FeedbackView } from '@/components/feedback-view'
import { SessionHistory } from '@/components/session-history'
import { apiClient } from '@/lib/api-client'
import type { StartInterviewRequest } from '@/lib/types'
import { InterviewChatSession } from '@/components/interview-chat-session'

type ViewType = 'setup' | 'session' | 'feedback' | 'history'

export default function Home() {
  const [currentView, setCurrentView] = useState<ViewType>('setup')
  const [interviewRequest, setInterviewRequest] = useState<StartInterviewRequest | null>(null)
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

  const handleStartInterview = (request: StartInterviewRequest) => {
    setInterviewRequest(request)
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
    setInterviewRequest(null)
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
      {currentView === 'session' && interviewRequest && interviewRequest.sessionType === 'voice' && (
        <InterviewSession
          interviewData={interviewRequest}
          onComplete={handleCompleteInterview}
        />
      )}
      {currentView === 'session' && interviewRequest && interviewRequest.sessionType === 'chat' && (
        <InterviewChatSession
          interviewData={interviewRequest}
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
