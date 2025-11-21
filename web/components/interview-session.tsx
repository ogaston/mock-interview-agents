'use client'

import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { VoiceButton, VoiceButtonWithHint } from '@/components/VoiceButton'
import { useVoiceRecording } from '@/hooks/useVoiceRecording'
import { synthesizeSpeech, playAudio, stopAudio } from '@/services/audioService'
import { Volume2, Mic, User, ChevronDown, ChevronUp, MessageSquare, Play } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import type { InterviewSessionResponse, Question, EvaluationScore } from '@/lib/types'
import { AudioVisualizer } from './AudioVisualizer'
import { cn } from '@/lib/utils'

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
  const [isPlayingAudio, setIsPlayingAudio] = useState(false)
  const [useVoiceMode, setUseVoiceMode] = useState(true)
  const [showTranscript, setShowTranscript] = useState(false)
  const [audioPermissionGranted, setAudioPermissionGranted] = useState(true) // Assume true initially

  // Track the currently playing question ID to prevent double-firing/race conditions
  const playingQuestionIdRef = useRef<string | null>(null)

  // Voice recording hook
  const voiceRecording = useVoiceRecording({
    useBrowserSTT: true,
    onTranscript: (text) => {
      setCurrentAnswer(text)
    },
    onError: (error) => {
      setError(`Voice error: ${error.message}`)
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
        setError('Voice features are not enabled. Please check backend configuration.')
        setUseVoiceMode(false)
      } else {
        setError(`Could not play audio: ${errorMessage}`)
      }
    } finally {
      setIsPlayingAudio(false)
    }
  }

  // Play question when it changes
  useEffect(() => {
    if (currentQuestion && useVoiceMode) {
      // Reset permission state on new question to be safe, though usually once granted it stays
      setAudioPermissionGranted(true) 
      
      const timer = setTimeout(() => {
        playQuestion(currentQuestion.question_text, currentQuestion.question_id)
      }, 500)
      return () => {
        clearTimeout(timer)
        stopAudio()
        playingQuestionIdRef.current = null
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentQuestion?.question_id, useVoiceMode])

  const handleNext = async () => {
    if (!currentAnswer.trim() || currentAnswer.length < 10) {
      setError('Por favor proporciona una respuesta de al menos 10 caracteres.')
      return
    }

    stopAudio() // Stop any playing audio
    setIsProcessing(true)
    setError(null)

    try {
      const response = await apiClient.submitAnswer(data.session_id, {
        answer: currentAnswer,
      })

      setQuestionsAnswered(response.question_answered)
      setStatus(response.status)

      // Wait a moment to show evaluation before moving to next question or completing
      await new Promise((resolve) => setTimeout(resolve, 2000))

      if (response.status === 'completed' || response.next_question === null) {
        onComplete(data.session_id)
      } else {
        setCurrentQuestion(response.next_question)
        setCurrentAnswer('')
        setShowEvaluation(false)
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
      if (e.code === 'Space' && !isProcessing) {
        if (document.activeElement?.tagName === 'TEXTAREA' || document.activeElement?.tagName === 'INPUT') {
            return;
        }
        
        e.preventDefault();
        
        if (voiceRecording.isRecording) {
          voiceRecording.stopRecording();
        } else {
          stopAudio(); // Stop TTS if playing
          voiceRecording.startRecording();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [voiceRecording, isProcessing]);

  const progress = ((questionsAnswered + 1) / data.total_questions) * 100

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 gap-6 bg-background transition-colors duration-500">
      <div className="w-full max-w-2xl flex flex-col gap-8">
        
        {/* Header Section */}
        <div className="flex flex-col gap-2">
          <div className="flex justify-between items-center">
            <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
              Question {questionsAnswered + 1} of {data.total_questions}
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
              <div className="relative group cursor-pointer" onClick={() => playQuestion(currentQuestion.question_text, currentQuestion.question_id)}>
                <Avatar className={cn(
                  "h-32 w-32 border-4 transition-all duration-300",
                  isPlayingAudio ? "border-primary shadow-[0_0_30px_rgba(var(--primary),0.3)] scale-105" : "border-muted group-hover:border-primary/50"
                )}>
                  <AvatarImage src="/placeholder-logo.png" alt="AI Interviewer" className="object-cover" />
                  <AvatarFallback className="text-4xl bg-primary/10 text-primary">AI</AvatarFallback>
                </Avatar>
                
                {/* Status Indicator / Play Button Overlay */}
                <div className={cn(
                  "absolute inset-0 flex items-center justify-center rounded-full bg-black/20 transition-opacity duration-200",
                  isPlayingAudio || audioPermissionGranted ? "opacity-0 hover:opacity-100" : "opacity-100"
                )}>
                    {!isPlayingAudio && (
                        <Play className={cn("w-12 h-12 text-white drop-shadow-lg", !audioPermissionGranted && "animate-pulse")} fill="currentColor" />
                    )}
                </div>

                {/* Status Text Badge */}
                 <div className={cn(
                  "absolute -bottom-2 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full text-xs font-semibold shadow-sm transition-all duration-300 whitespace-nowrap",
                  isPlayingAudio ? "bg-primary text-primary-foreground" : 
                  !audioPermissionGranted ? "bg-destructive text-destructive-foreground animate-bounce" :
                  "bg-muted text-muted-foreground opacity-0"
                )}>
                  {isPlayingAudio ? "Speaking" : !audioPermissionGranted ? "Tap to Start Audio" : ""}
                </div>
              </div>

              {/* Audio Visualizer */}
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

              {/* Question Text */}
              <div className="text-center space-y-2 max-w-lg">
                 <h3 className="text-2xl font-semibold leading-relaxed text-foreground/90">
                  {currentQuestion.question_text}
                </h3>
              </div>
            </div>

            {/* Voice Controls */}
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
                      onClick={() => playQuestion(currentQuestion.question_text, currentQuestion.question_id)}
                      disabled={isPlayingAudio || isProcessing}
                      title="Replay question"
                    >
                      <Volume2 className={cn("w-5 h-5", isPlayingAudio && "animate-pulse text-primary")} />
                    </Button>
                  )}
               </div>
               
               <p className={cn(
                 "text-sm font-medium transition-all duration-300 h-6",
                 voiceRecording.isRecording ? "text-red-500 animate-pulse" : "text-muted-foreground"
               )}>
                 {isProcessing ? 'Evaluating Answer...' : 
                  voiceRecording.isRecording ? 'Listening...' : 
                  'Tap microphone to answer'}
               </p>
            </div>

            {/* Transcript Toggle */}
            <div className="flex justify-center">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setShowTranscript(!showTranscript)}
                className="text-xs text-muted-foreground hover:text-foreground gap-2"
              >
                <MessageSquare className="w-4 h-4" />
                {showTranscript ? 'Hide Transcript' : 'Show Transcript / Type Answer'}
                {showTranscript ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </Button>
            </div>

            {/* Transcript / Text Input Area */}
            {/* Always show live transcript if recording, even if "Show Transcript" is off (as a floating caption) */}
            {(showTranscript || voiceRecording.isRecording) && (
              <div className={cn(
                "space-y-2 transition-all duration-300",
                showTranscript ? "animate-in fade-in slide-in-from-top-2" : "absolute bottom-24 left-0 right-0 px-6 z-10"
              )}>
                {showTranscript ? (
                  <>
                    <Textarea
                      placeholder="Your answer will appear here..."
                      value={currentAnswer}
                      onChange={(e) => setCurrentAnswer(e.target.value)}
                      className="min-h-32 resize-none bg-secondary/30 border-secondary focus:border-primary/50 transition-colors"
                      disabled={isProcessing || voiceRecording.isRecording}
                    />
                    <div className="flex justify-between items-center text-xs text-muted-foreground px-1">
                       <span>{currentAnswer.length} chars</span>
                       <span>Min 10 required</span>
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
                {isProcessing ? 'Evaluating...' : 
                 questionsAnswered === data.total_questions - 1 ? 'Complete Interview' : 'Submit Answer'}
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
                   <span className="text-xs font-semibold text-primary uppercase tracking-wider">Assessment</span>
                   <span className="font-bold text-2xl">{lastEvaluation.overall_score.toFixed(1)}<span className="text-sm text-muted-foreground font-normal">/10</span></span>
                 </div>
                 <div className="flex gap-4 text-sm">
                    <div className="flex flex-col items-center">
                      <span className="text-muted-foreground text-xs">Clarity</span>
                      <span className="font-semibold">{lastEvaluation.clarity.toFixed(1)}</span>
                    </div>
                    <div className="flex flex-col items-center">
                      <span className="text-muted-foreground text-xs">Confidence</span>
                      <span className="font-semibold">{lastEvaluation.confidence.toFixed(1)}</span>
                    </div>
                    <div className="flex flex-col items-center">
                      <span className="text-muted-foreground text-xs">Relevance</span>
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
