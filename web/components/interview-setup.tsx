'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Code, Server, Layers, Briefcase, BarChart, Star, TrendingUp, Award, Crown } from 'lucide-react'
import type { StartInterviewRequest, Seniority } from '@/lib/types'

interface InterviewSetupProps {
  onStart: (data: StartInterviewRequest) => void
  onViewHistory: () => void
  hasHistory: boolean
}

const roles = [
  { id: 'Frontend Engineer', name: 'Ingeniero Frontend', icon: Code },
  { id: 'Backend Engineer', name: 'Ingeniero Backend', icon: Server },
  { id: 'Full Stack Engineer', name: 'Ingeniero Full Stack', icon: Layers },
  { id: 'Product Manager', name: 'Gerente de Producto', icon: Briefcase },
  { id: 'Data Scientist', name: 'Científico de Datos', icon: BarChart },
]

const seniorities: { id: Seniority; name: string; icon: any }[] = [
  { id: 'junior', name: 'Junior (0-2 años)', icon: Star },
  { id: 'mid', name: 'Intermedio (2-5 años)', icon: TrendingUp },
  { id: 'senior', name: 'Senior (5+ años)', icon: Award },
  { id: 'lead', name: 'Líder (8+ años)', icon: Crown },
]

export function InterviewSetup({ onStart, onViewHistory, hasHistory }: InterviewSetupProps) {
  const [selectedRole, setSelectedRole] = useState('')
  const [selectedSeniority, setSelectedSeniority] = useState<Seniority | ''>('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleStart = () => {
    if (selectedRole && selectedSeniority) {
      onStart({
        role: selectedRole,
        seniority: selectedSeniority as Seniority,
      })
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 gap-8">
      <div className="text-center space-y-2 mb-4">
        <h1 className="text-4xl font-bold text-pretty">Entrenador de Entrevistas</h1>
        <p className="text-muted-foreground">Entrenamiento de entrevistas con IA y retroalimentación en tiempo real</p>
      </div>

      <Card className="w-full max-w-4xl">
        <CardHeader>
          <CardTitle>Inicia tu Entrevista de Práctica</CardTitle>
          <CardDescription>Selecciona tu puesto y nivel de experiencia</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Column 1: Role Selection */}
            <div className="space-y-3">
              <label className="text-sm font-medium flex items-center gap-2">
                <Briefcase className="w-4 h-4" />
                Puesto
              </label>
              <div className="grid gap-2">
                {roles.map((role) => {
                  const Icon = role.icon
                  return (
                    <button
                      key={role.id}
                      onClick={() => setSelectedRole(role.id)}
                      className={`p-3 text-left rounded-lg border transition-all flex items-center gap-3 ${
                        selectedRole === role.id
                          ? 'border-primary bg-primary/10 text-primary font-medium shadow-sm'
                          : 'border-border hover:border-primary/50 hover:bg-accent/50'
                      }`}
                    >
                      <Icon className="w-5 h-5 flex-shrink-0" />
                      <span>{role.name}</span>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Column 2: Seniority Selection */}
            <div className="space-y-3">
              <label className="text-sm font-medium flex items-center gap-2">
                <Award className="w-4 h-4" />
                Nivel de Experiencia
              </label>
              <div className="grid gap-2">
                {seniorities.map((level) => {
                  const Icon = level.icon
                  return (
                    <button
                      key={level.id}
                      onClick={() => setSelectedSeniority(level.id)}
                      className={`p-3 text-left rounded-lg border transition-all flex items-center gap-3 ${
                        selectedSeniority === level.id
                          ? 'border-primary bg-primary/10 text-primary font-medium shadow-sm'
                          : 'border-border hover:border-primary/50 hover:bg-accent/50'
                      }`}
                    >
                      <Icon className="w-5 h-5 flex-shrink-0" />
                      <span>{level.name}</span>
                    </button>
                  )
                })}
              </div>
            </div>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
              {error}
            </div>
          )}

          <div className="flex gap-3 pt-4">

          {hasHistory && (
              <Button
                onClick={onViewHistory}
                variant="outline"
                className="flex-1"
                size="lg"
                disabled={isLoading}
              >
                Ver Historial
              </Button>
            )}

            
            <Button
              onClick={handleStart}
              disabled={!selectedRole || !selectedSeniority || isLoading}
              className="flex-1"
              size="lg"
            >
              {isLoading ? 'Iniciando Entrevista...' : 'Comenzar Entrevista'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
