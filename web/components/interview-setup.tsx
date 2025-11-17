'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { apiClient } from '@/lib/api-client'
import type { InterviewSessionResponse, Seniority } from '@/lib/types'

interface InterviewSetupProps {
  onStart: (data: InterviewSessionResponse) => void
  onViewHistory: () => void
  hasHistory: boolean
}

const roles = [
  { id: 'Frontend Engineer', name: 'Frontend Engineer' },
  { id: 'Backend Engineer', name: 'Backend Engineer' },
  { id: 'Full Stack Engineer', name: 'Full Stack Engineer' },
  { id: 'Product Manager', name: 'Product Manager' },
  { id: 'Data Scientist', name: 'Data Scientist' },
]

const seniorities: { id: Seniority; name: string }[] = [
  { id: 'junior', name: 'Junior (0-2 years)' },
  { id: 'mid', name: 'Mid-level (2-5 years)' },
  { id: 'senior', name: 'Senior (5+ years)' },
  { id: 'lead', name: 'Lead (8+ years)' },
]

export function InterviewSetup({ onStart, onViewHistory, hasHistory }: InterviewSetupProps) {
  const [selectedRole, setSelectedRole] = useState('')
  const [selectedSeniority, setSelectedSeniority] = useState<Seniority | ''>('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleStart = async () => {
    if (selectedRole && selectedSeniority) {
      setIsLoading(true)
      setError(null)

      try {
        const session = await apiClient.startInterview({
          role: selectedRole,
          seniority: selectedSeniority as Seniority,
        })
        onStart(session)
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to start interview'
        setError(errorMessage)
        console.error('Error starting interview:', err)
      } finally {
        setIsLoading(false)
      }
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 gap-8">
      <div className="text-center space-y-2 mb-4">
        <h1 className="text-4xl font-bold text-pretty">Interview Coach</h1>
        <p className="text-muted-foreground">AI-powered interview training with real-time feedback</p>
      </div>

      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Start Your Practice Interview</CardTitle>
          <CardDescription>Select your role and experience level</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-3">
            <label className="text-sm font-medium">Position</label>
            <div className="grid gap-2">
              {roles.map((role) => (
                <button
                  key={role.id}
                  onClick={() => setSelectedRole(role.id)}
                  className={`p-3 text-left rounded-lg border transition-all ${
                    selectedRole === role.id
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  {role.name}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <label className="text-sm font-medium">Experience Level</label>
            <div className="grid gap-2">
              {seniorities.map((level) => (
                <button
                  key={level.id}
                  onClick={() => setSelectedSeniority(level.id)}
                  className={`p-3 text-left rounded-lg border transition-all ${
                    selectedSeniority === level.id
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  {level.name}
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
              {error}
            </div>
          )}

          <Button
            onClick={handleStart}
            disabled={!selectedRole || !selectedSeniority || isLoading}
            className="w-full"
            size="lg"
          >
            {isLoading ? 'Starting Interview...' : 'Begin Interview'}
          </Button>

          {hasHistory && (
            <Button
              onClick={onViewHistory}
              variant="outline"
              className="w-full"
              disabled={isLoading}
            >
              View Session History
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
