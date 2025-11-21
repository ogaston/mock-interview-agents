'use client'

import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { apiClient } from '@/lib/api-client'
import { Send, Bot, User } from 'lucide-react'
import type { StartInterviewRequest } from '@/lib/types'

interface Message {
  id: string
  type: 'question' | 'answer' | 'system'
  content: string
  isStreaming?: boolean
  timestamp: Date
  questionId?: number
  category?: string
}

interface InterviewChatSessionProps {
  interviewData: StartInterviewRequest
  onComplete: (sessionId: string) => void
}

export function InterviewChatSession({ interviewData, onComplete }: InterviewChatSessionProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [currentAnswer, setCurrentAnswer] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [totalQuestions, setTotalQuestions] = useState(0)
  const [questionsAnswered, setQuestionsAnswered] = useState(0)
  const [isComplete, setIsComplete] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const hasInitialized = useRef(false)

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Initialize interview with streaming
  useEffect(() => {
    // Prevent double initialization in React Strict Mode
    if (hasInitialized.current) {
      return
    }
    hasInitialized.current = true

    let streamingMessageId: string | null = null
    
    const initInterview = async () => {
      setIsProcessing(true)
      
      // Add system message
      setMessages([{
        id: `system-${Date.now()}`,
        type: 'system',
        content: 'Iniciando entrevista...',
        timestamp: new Date()
      }])

      try {
        await apiClient.startInterviewStream(
          interviewData,
          // onChunk
          (chunk: string) => {
            if (!streamingMessageId) {
              streamingMessageId = `question-${Date.now()}`
              setMessages(prev => [
                ...prev,
                {
                  id: streamingMessageId!,
                  type: 'question',
                  content: chunk,
                  isStreaming: true,
                  timestamp: new Date()
                }
              ])
            } else {
              setMessages(prev => prev.map(msg => 
                msg.id === streamingMessageId
                  ? { ...msg, content: msg.content + chunk }
                  : msg
              ))
            }
          },
          // onMetadata
          (metadata: any) => {
            setSessionId(metadata.session_id)
            setTotalQuestions(metadata.total_questions)
            
            // Remove "Iniciando entrevista..." message
            setMessages(prev => prev.filter(msg => !msg.content.includes('Iniciando entrevista')))
          },
          // onComplete
          (fullText: string) => {
            if (streamingMessageId) {
              setMessages(prev => prev.map(msg => 
                msg.id === streamingMessageId
                  ? { ...msg, content: fullText, isStreaming: false }
                  : msg
              ))
            }
            setIsProcessing(false)
            textareaRef.current?.focus()
          },
          // onError
          (err: Error) => {
            setError(err.message)
            setIsProcessing(false)
          }
        )
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error al iniciar la entrevista')
        setIsProcessing(false)
      }
    }

    initInterview()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleSubmit = async () => {
    if (!currentAnswer.trim() || currentAnswer.length < 10 || !sessionId) {
      setError('Por favor proporciona una respuesta de al menos 10 caracteres.')
      return
    }

    setIsProcessing(true)
    setError(null)

    // Add user's answer to messages
    const answerMessage: Message = {
      id: `answer-${Date.now()}`,
      type: 'answer',
      content: currentAnswer,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, answerMessage])
    setCurrentAnswer('')

    let streamingMessageId: string | null = null

    try {
      await apiClient.submitAnswerStream(
        sessionId,
        { answer: currentAnswer },
        // onChunk
        (chunk: string) => {
          if (!streamingMessageId) {
            streamingMessageId = `question-${Date.now()}`
            setMessages(prev => [
              ...prev,
              {
                id: streamingMessageId!,
                type: 'question',
                content: chunk,
                isStreaming: true,
                timestamp: new Date()
              }
            ])
          } else {
            setMessages(prev => prev.map(msg => 
              msg.id === streamingMessageId
                ? { ...msg, content: msg.content + chunk }
                : msg
            ))
          }
        },
        // onMetadata
        (metadata: any) => {
          setQuestionsAnswered(metadata.question_answered)
          
          if (metadata.all_completed) {
            setIsComplete(true)
            setMessages(prev => [
              ...prev,
              {
                id: `system-complete-${Date.now()}`,
                type: 'system',
                content: '¡Entrevista completa! Evaluando tus respuestas...',
                timestamp: new Date()
              }
            ])
          }
          
          if (metadata.status === 'evaluated') {
            setMessages(prev => [
              ...prev,
              {
                id: `system-evaluated-${Date.now()}`,
                type: 'system',
                content: '✓ Evaluación completada. Haz clic en el botón de abajo para ver tu retroalimentación.',
                timestamp: new Date()
              }
            ])
          }
        },
        // onComplete
        (fullText?: string) => {
          if (streamingMessageId && fullText) {
            setMessages(prev => prev.map(msg => 
              msg.id === streamingMessageId
                ? { ...msg, content: fullText, isStreaming: false }
                : msg
            ))
          }
          setIsProcessing(false)
          if (!isComplete) {
            textareaRef.current?.focus()
          }
        },
        // onError
        (err: Error) => {
          setError(err.message)
          setIsProcessing(false)
        }
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al enviar la respuesta')
      setIsProcessing(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (!isProcessing && currentAnswer.trim().length >= 10) {
        handleSubmit()
      }
    }
  }

  const progress = totalQuestions > 0 ? (questionsAnswered / totalQuestions) * 100 : 0

  return (
    <div className="flex flex-col h-screen max-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-card px-6 py-4 flex-shrink-0">
        <div className="max-w-4xl mx-auto">
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-xl font-bold">
              {isComplete ? 'Entrevista Completa' : 'Entrevista en Progreso'}
            </h2>
            <span className="text-sm text-muted-foreground">
              {questionsAnswered} de {totalQuestions} preguntas
            </span>
          </div>
          <div className="w-full bg-secondary rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${
                message.type === 'answer' ? 'justify-end' : 'justify-start'
              } ${message.type === 'system' ? 'justify-center' : ''}`}
            >
              {message.type === 'question' && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                  <Bot className="w-5 h-5 text-primary" />
                </div>
              )}
              
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  message.type === 'question'
                    ? 'bg-card border border-border'
                    : message.type === 'answer'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted/50 text-muted-foreground text-sm italic'
                }`}
              >
                <p className="whitespace-pre-wrap break-words">
                  {message.content}
                  {message.isStreaming && (
                    <span className="inline-block w-1 h-4 ml-1 bg-current animate-pulse" />
                  )}
                </p>
                {message.category && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Categoría: {message.category}
                  </p>
                )}
              </div>

              {message.type === 'answer' && (
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                  <User className="w-5 h-5 text-primary-foreground" />
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t bg-card px-4 py-4 flex-shrink-0">
        <div className="max-w-4xl mx-auto">
          {error && (
            <div className="mb-3 p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
              {error}
            </div>
          )}

          {isComplete ? (
            <Button
              onClick={() => sessionId && onComplete(sessionId)}
              className="w-full"
              size="lg"
            >
              Ver Retroalimentación Detallada
            </Button>
          ) : (
            <div className="flex gap-2">
              <Textarea
                ref={textareaRef}
                placeholder="Escribe tu respuesta aquí... (mínimo 10 caracteres, Enter para enviar, Shift+Enter para nueva línea)"
                value={currentAnswer}
                onChange={(e) => setCurrentAnswer(e.target.value)}
                onKeyDown={handleKeyPress}
                className="min-h-[60px] max-h-[200px] resize-none"
                disabled={isProcessing}
              />
              <Button
                onClick={handleSubmit}
                disabled={!currentAnswer.trim() || currentAnswer.length < 10 || isProcessing}
                size="lg"
                className="px-4"
              >
                <Send className="w-5 h-5" />
              </Button>
            </div>
          )}
          
          {currentAnswer.length > 0 && currentAnswer.length < 10 && !isComplete && (
            <p className="text-xs text-muted-foreground mt-2">
              {10 - currentAnswer.length} caracteres más necesarios
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

