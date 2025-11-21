'use client'

import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { VoiceButton, VoiceButtonWithHint } from '@/components/VoiceButton'
import { useVoiceRecording } from '@/hooks/useVoiceRecording'
import { synthesizeSpeech, playAudio, stopAudio } from '@/services/audioService'
import { Volume2, Mic, User, ChevronDown, ChevronUp, MessageSquare, Play, Loader2 } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import type { InterviewSessionResponse, Question, EvaluationScore, StartInterviewRequest } from '@/lib/types'
import { AudioVisualizer } from './AudioVisualizer'
import { cn } from '@/lib/utils'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'

interface InterviewSessionProps {
  interviewData: StartInterviewRequest
  onComplete: (sessionId: string) => void
}

export function InterviewSession({ interviewData, onComplete }: InterviewSessionProps) {
  const [sessionData, setSessionData] = useState<InterviewSessionResponse | null>(null)
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null)
  const [currentAnswer, setCurrentAnswer] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [isInitializing, setIsInitializing] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [questionsAnswered, setQuestionsAnswered] = useState(0)
  const [lastEvaluation, setLastEvaluation] = useState<EvaluationScore | null>(null)
  const [showEvaluation, setShowEvaluation] = useState(false)
  const [isPlayingAudio, setIsPlayingAudio] = useState(false)
  const [useVoiceMode, setUseVoiceMode] = useState(interviewData.sessionType === 'voice')
  const [showTranscript, setShowTranscript] = useState(interviewData.sessionType === 'chat')
  const [audioPermissionGranted, setAudioPermissionGranted] = useState(true)

  // Track the currently playing question ID to prevent double-firing/race conditions
  const playingQuestionIdRef = useRef<string | null>(null)

  // Initialize Interview
  useEffect(() => {
    const initInterview = async () => {
      try {
        setIsInitializing(true)
        const response = await apiClient.startInterview(interviewData)
        setSessionData(response)
        setCurrentQuestion(response.current_question)
        setQuestionsAnswered(0)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error al iniciar la entrevista')
      } finally {
        setIsInitializing(false)
      }
    }

    initInterview()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Voice recording hook
  const voiceRecording = useVoiceRecording({
    useBrowserSTT: true,
    onTranscript: (text) => {
      setCurrentAnswer(text)
    },
    onError: (error) => {
      setError(`Error de voz: ${error.message}`)
      setShowTranscript(true)
    },
  })

  // Auto-play question using TTS
  const playQuestion = async (questionText: string, questionId: string) => {
    // Prevent re-playing the same question if it's already in progress
    if (playingQuestionIdRef.current === questionId && isPlayingAudio) return
    
    playingQuestionIdRef.current = questionId

    try {
      setIsPlayingAudio(true)
      setError(null)
      const audioBlob = await synthesizeSpeech(questionText)
      await playAudio(audioBlob)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error'
      
      // Handle Autoplay Policy (NotAllowedError)
      if (errorMessage.includes('NotAllowedError') || errorMessage.includes('user agent')) {
         setAudioPermissionGranted(false)
         setIsPlayingAudio(false)
         return
      }

      if (errorMessage.includes('403') || errorMessage.includes('Voice features are disabled')) {
        setError('Las funciones de voz no están habilitadas. Por favor verifica la configuración del backend.')
        setUseVoiceMode(false)
      } else {
        setError(`No se pudo reproducir el audio: ${errorMessage}`)
      }
    } finally {
      setIsPlayingAudio(false)
    }
  }

  // Handle Mode switching
  useEffect(() => {
    if (!useVoiceMode) {
      stopAudio()
      setShowTranscript(true)
    }
  }, [useVoiceMode])

  // Play question when it changes
  useEffect(() => {
    if (currentQuestion && useVoiceMode && !isInitializing) {
      // Reset permission state on new question to be safe, though usually once granted it stays
      setAudioPermissionGranted(true) 
      
      const timer = setTimeout(() => {
        playQuestion(currentQuestion.question_text, currentQuestion.question_id.toString())
      }, 500)
      return () => {
        clearTimeout(timer)
        stopAudio()
        playingQuestionIdRef.current = null
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentQuestion?.question_id, useVoiceMode, isInitializing])

  const handleNext = async () => {
    if (!currentAnswer.trim() || currentAnswer.length < 10) {
      setError('Por favor proporciona una respuesta de al menos 10 caracteres.')
      return
    }

    if (!sessionData) return

    stopAudio() // Stop any playing audio
    setIsProcessing(true)
    setError(null)
    setShowEvaluation(false)

    try {
      const response = await apiClient.submitAnswer(sessionData.session_id, {
        answer: currentAnswer,
      })

      setLastEvaluation(response.evaluation)
      setShowEvaluation(true)
      setQuestionsAnswered(response.question_answered)

      // Wait a moment to show evaluation before moving to next question or completing
      await new Promise((resolve) => setTimeout(resolve, 2000))

      if (response.status === 'completed' || response.next_question === null) {
        onComplete(sessionData.session_id)
      } else {
        setCurrentQuestion(response.next_question)
        setCurrentAnswer('')
        setShowEvaluation(false)
        // Only hide transcript if we are back in voice mode
        if (useVoiceMode) setShowTranscript(false)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al enviar la respuesta'
      setError(errorMessage)
    } finally {
      setIsProcessing(false)
    }
  }

  // Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Spacebar to toggle recording
      if (e.code === 'Space' && !isProcessing && !isInitializing) {
        if (document.activeElement?.tagName === 'TEXTAREA' || document.activeElement?.tagName === 'INPUT') {
            return;
        }
        
        e.preventDefault();
        
        if (voiceRecording.isRecording) {
          voiceRecording.stopRecording();
        } else {
          stopAudio(); // Stop TTS if playing
          if (useVoiceMode) {
            voiceRecording.startRecording();
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [voiceRecording, isProcessing, useVoiceMode, isInitializing]);

  if (isInitializing) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
        <p className="text-muted-foreground">Inicializando entrevista...</p>
      </div>
    )
  }

  if (error && !sessionData) {
    return (
       <div className="flex flex-col items-center justify-center min-h-screen gap-4 p-4">
        <div className="text-destructive text-center max-w-md">
            <h3 className="text-lg font-bold">Error al Iniciar la Entrevista</h3>
            <p>{error}</p>
        </div>
        <Button onClick={() => window.location.reload()}>Intentar de Nuevo</Button>
      </div>
    )
  }

  if (!sessionData || !currentQuestion) return null;

  const progress = ((questionsAnswered + 1) / sessionData.total_questions) * 100

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 gap-6 bg-background transition-colors duration-500">
      <div className="w-full max-w-2xl flex flex-col gap-8">
        
        {/* Mode Toggle */}
        <div className="flex justify-end w-full">
             <div className="flex items-center space-x-2 bg-secondary p-2 rounded-lg backdrop-blur-sm border shadow-sm">
                <Switch
                  id="voice-mode"
                  checked={useVoiceMode}
                  onCheckedChange={setUseVoiceMode}
                />
                <Label htmlFor="voice-mode" className="cursor-pointer text-sm font-medium">
                    {useVoiceMode ? 'Modo Voz' : 'Modo Texto'}
                </Label>
             </div>
        </div>

        {/* Header Section */}
        <div className="flex flex-col gap-2">
          <div className="flex justify-between items-center">
            <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
              Pregunta {questionsAnswered + 1} de {sessionData.total_questions}
            </h2>
            <div className="flex items-center gap-2">
               <span className="text-xs font-medium text-primary bg-primary/10 px-2 py-1 rounded-full">
                 {currentQuestion.category || 'General'}
               </span>
            </div>
          </div>
          <div className="w-full bg-secondary rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-primary h-full rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Main Interaction Card */}
        <Card className="border-0 shadow-xl bg-card/50 backdrop-blur-sm">
          <CardContent className="pt-8 pb-8 px-6 md:px-10 space-y-8">
            
            {/* Interviewer Avatar & Visualizer */}
            <div className="flex flex-col items-center justify-center gap-6 py-4">
              <div className="relative group cursor-pointer" onClick={() => useVoiceMode && playQuestion(currentQuestion.question_text, currentQuestion.question_id.toString())}>
                <Avatar className={cn(
                  "h-32 w-32 border-4 transition-all duration-300",
                  isPlayingAudio ? "border-primary shadow-[0_0_30px_rgba(var(--primary),0.3)] scale-105" : "border-muted group-hover:border-primary/50"
                )}>
                  <AvatarImage src="/bot.png" alt="AI Interviewer" className="object-cover" />
                  <AvatarFallback className="text-4xl bg-primary/10 text-primary">AI</AvatarFallback>
                </Avatar>
                
                {/* Status Indicator / Play Button Overlay - Only in Voice Mode */}
                {useVoiceMode && (
                    <>
                        <div className={cn(
                        "absolute inset-0 flex items-center justify-center rounded-full bg-black/20 transition-opacity duration-200",
                        isPlayingAudio || audioPermissionGranted ? "opacity-0 hover:opacity-100" : "opacity-100"
                        )}>
                            {!isPlayingAudio && (
                                <Play className={cn("w-12 h-12 text-white drop-shadow-lg", !audioPermissionGranted && "animate-pulse")} fill="currentColor" />
                            )}
                        </div>
                        <div className={cn(
                        "absolute -bottom-2 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-xs font-semibold shadow-sm transition-all duration-300 whitespace-nowrap",
                        isPlayingAudio ? "bg-primary text-primary-foreground" : 
                        !audioPermissionGranted ? "bg-destructive text-destructive-foreground animate-bounce" :
                        "bg-muted text-muted-foreground opacity-0"
                        )}>
                        {isPlayingAudio ? "Hablando" : !audioPermissionGranted ? "Toca para Iniciar Audio" : ""}
                        </div>
                    </>
                )}
              </div>

              {/* Audio Visualizer */}
              {(useVoiceMode || isPlayingAudio || voiceRecording.isRecording) && (
                <div className="h-12 flex items-center justify-center w-full max-w-[200px]">
                    <AudioVisualizer 
                    isActive={isPlayingAudio || voiceRecording.isRecording || isProcessing} 
                    mode={
                        isProcessing ? 'thinking' :
                        voiceRecording.isRecording ? 'listening' : 
                        'speaking'
                    }
                    stream={voiceRecording.mediaStream}
                    />
                </div>
              )}

              {/* Question Text */}
              <div className="text-center space-y-2 max-w-lg">
                 <h3 className="text-2xl font-semibold leading-relaxed text-foreground/90">
                  {currentQuestion.question_text}
                </h3>
              </div>
            </div>

            {/* Voice Controls - Hide if Voice Mode is OFF */}
            {useVoiceMode && (
                <div className="flex flex-col items-center gap-6">
                <div className="relative">
                    <VoiceButton 
                        isRecording={voiceRecording.isRecording}
                        isProcessing={voiceRecording.isProcessing}
                        hasError={voiceRecording.hasError}
                        onStart={() => {
                            stopAudio();
                            voiceRecording.startRecording();
                        }}
                        onStop={voiceRecording.stopRecording}
                        disabled={isProcessing}
                        className="h-20 w-20"
                    />
                    {/* Replay Button (Floating next to mic) */}
                    {!voiceRecording.isRecording && (
                        <Button
                        size="icon"
                        variant="ghost"
                        className="absolute -right-16 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-full h-10 w-10"
                        onClick={() => playQuestion(currentQuestion.question_text, currentQuestion.question_id.toString())}
                        disabled={isPlayingAudio || isProcessing}
                        title="Repetir pregunta"
                        >
                        <Volume2 className={cn("w-5 h-5", isPlayingAudio && "animate-pulse text-primary")} />
                        </Button>
                    )}
                </div>
                
                <p className={cn(
                    "text-sm font-medium transition-all duration-300 h-6",
                    voiceRecording.isRecording ? "text-red-500 animate-pulse" : "text-muted-foreground"
                )}>
                    {isProcessing ? 'Evaluando Respuesta...' : 
                    voiceRecording.isRecording ? 'Escuchando...' : 
                    'Toca el micrófono para responder'}
                </p>
                </div>
            )}

            {/* Transcript Toggle */}
            {useVoiceMode && (
                <div className="flex justify-center">
                <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => setShowTranscript(!showTranscript)}
                    className="text-xs text-muted-foreground hover:text-foreground gap-2"
                >
                    <MessageSquare className="w-4 h-4" />
                    {showTranscript ? 'Ocultar Transcripción' : 'Mostrar Transcripción / Escribir Respuesta'}
                    {showTranscript ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                </Button>
                </div>
            )}

            {/* Transcript / Text Input Area */}
            {(showTranscript || voiceRecording.isRecording) && (
              <div className={cn(
                "space-y-2 transition-all duration-300",
                showTranscript ? "animate-in fade-in slide-in-from-top-2" : "absolute bottom-24 left-0 right-0 px-6 z-10"
              )}>
                {showTranscript ? (
                  <>
                    <Textarea
                      placeholder={useVoiceMode ? "Tu respuesta aparecerá aquí..." : "Escribe tu respuesta aquí..."}
                      value={currentAnswer}
                      onChange={(e) => setCurrentAnswer(e.target.value)}
                      className="min-h-32 resize-none bg-secondary/30 border-secondary focus:border-primary/50 transition-colors"
                      disabled={isProcessing || (voiceRecording.isRecording && useVoiceMode)}
                      autoFocus={!useVoiceMode}
                    />
                    <div className="flex justify-between items-center text-xs text-muted-foreground px-1">
                       <span>{currentAnswer.length} caracteres</span>
                       <span>Mínimo 10 requeridos</span>
                    </div>
                  </>
                ) : (
                  // Live Caption Overlay when transcript is hidden
                  currentAnswer && (
                    <div className="bg-black/60 backdrop-blur-md text-white p-4 rounded-xl text-center text-lg font-medium shadow-2xl mx-auto max-w-xl animate-in fade-in slide-in-from-bottom-4">
                      "{currentAnswer.slice(-100)}{currentAnswer.length > 100 ? '...' : ''}"
                    </div>
                  )
                )}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4">
              <Button
                onClick={handleNext}
                disabled={!currentAnswer.trim() || currentAnswer.length < 10 || isProcessing}
                className="w-full py-6 text-lg font-medium shadow-lg shadow-primary/10 hover:shadow-primary/20 transition-all"
                size="lg"
              >
                {isProcessing ? 'Evaluando...' : 
                 questionsAnswered === sessionData.total_questions - 1 ? 'Completar Entrevista' : 'Enviar Respuesta'}
              </Button>
            </div>

          </CardContent>
        </Card>

        {/* Evaluation Feedback Toast/Card */}
        {showEvaluation && lastEvaluation && (
          <div className="animate-in slide-in-from-bottom-4 fade-in duration-500">
            <Card className="bg-primary/5 border-primary/20 overflow-hidden">
               <CardContent className="p-4 flex items-center justify-between gap-4">
                 <div className="flex flex-col gap-1">
                   <span className="text-xs font-semibold text-primary uppercase tracking-wider">Evaluación</span>
                   <span className="font-bold text-2xl">{lastEvaluation.overall_score.toFixed(1)}<span className="text-sm text-muted-foreground font-normal">/10</span></span>
                 </div>
                 <div className="flex gap-4 text-sm">
                    <div className="flex flex-col items-center">
                      <span className="text-muted-foreground text-xs">Claridad</span>
                      <span className="font-semibold">{lastEvaluation.clarity.toFixed(1)}</span>
                    </div>
                    <div className="flex flex-col items-center">
                      <span className="text-muted-foreground text-xs">Confianza</span>
                      <span className="font-semibold">{lastEvaluation.confidence.toFixed(1)}</span>
                    </div>
                    <div className="flex flex-col items-center">
                      <span className="text-muted-foreground text-xs">Relevancia</span>
                      <span className="font-semibold">{lastEvaluation.relevance.toFixed(1)}</span>
                    </div>
                 </div>
               </CardContent>
            </Card>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-lg bg-destructive/10 text-destructive text-sm text-center animate-in fade-in">
            {error}
          </div>
        )}

      </div>
    </div>
  )
}
