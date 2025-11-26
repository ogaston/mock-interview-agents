import type {
  StartInterviewRequest,
  SubmitAnswerRequest,
  InterviewSessionResponse,
  AnswerResponse,
  FeedbackResponse,
  SessionHistoryItem,
  HealthCheckResponse,
  APIError,
} from './types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || ''

class APIClient {
  private baseURL: string

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`

    const config: RequestInit = {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    }

    try {
      const response = await fetch(url, config)

      if (!response.ok) {
        let errorMessage = `API Error: ${response.status} ${response.statusText}`

        try {
          const errorData: APIError = await response.json()
          errorMessage = errorData.detail || errorMessage
        } catch {
          // If error response is not JSON, use default message
        }

        throw new Error(errorMessage)
      }

      // Handle 204 No Content
      if (response.status === 204) {
        return {} as T
      }

      return await response.json()
    } catch (error) {
      if (error instanceof Error) {
        throw error
      }
      throw new Error('Ocurrió un error inesperado')
    }
  }

  // Health check
  async healthCheck(): Promise<HealthCheckResponse> {
    return this.request<HealthCheckResponse>('/health')
  }

  // Start a new interview session
  async startInterview(
    data: StartInterviewRequest,
    includeAudio: boolean = false
  ): Promise<InterviewSessionResponse> {
    const url = `/api/interviews/start${includeAudio ? '?include_audio=true' : ''}`
    return this.request<InterviewSessionResponse>(url, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Start a new interview session with streaming
  async startInterviewStream(
    data: StartInterviewRequest,
    onChunk: (chunk: string) => void,
    onMetadata: (metadata: any) => void,
    onComplete: (fullText: string) => void,
    onError: (error: Error) => void
  ): Promise<void> {
    const url = `${this.baseURL}/api/interviews/stream/start`

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error(`Error de API: ${response.status} ${response.statusText}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('El cuerpo de la respuesta es nulo')
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.type === 'metadata') {
                onMetadata(data)
              } else if (data.type === 'chunk') {
                onChunk(data.content)
              } else if (data.type === 'done') {
                onComplete(data.question_text)
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e)
            }
          }
        }
      }
    } catch (error) {
      onError(error instanceof Error ? error : new Error('Ocurrió un error desconocido'))
    }
  }

  // Submit an answer and get evaluation + next question
  async submitAnswer(
    sessionId: string,
    data: SubmitAnswerRequest,
    includeAudio: boolean = false
  ): Promise<AnswerResponse> {
    const url = `/api/interviews/${sessionId}/answer${includeAudio ? '?include_audio=true' : ''}`
    return this.request<AnswerResponse>(url, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Submit an answer and stream the next question
  async submitAnswerStream(
    sessionId: string,
    data: SubmitAnswerRequest,
    onChunk: (chunk: string) => void,
    onMetadata: (metadata: any) => void,
    onComplete: (fullText?: string) => void,
    onError: (error: Error) => void
  ): Promise<void> {
    const url = `${this.baseURL}/api/interviews/stream/${sessionId}/answer`

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error(`Error de API: ${response.status} ${response.statusText}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('El cuerpo de la respuesta es nulo')
      }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.type === 'metadata') {
                onMetadata(data)
              } else if (data.type === 'chunk') {
                onChunk(data.content)
              } else if (data.type === 'done') {
                onComplete(data.question_text)
              } else if (data.type === 'evaluation_complete') {
                onMetadata(data)
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e)
            }
          }
        }
      }
    } catch (error) {
      onError(error instanceof Error ? error : new Error('Ocurrió un error desconocido'))
    }
  }

  // Get comprehensive feedback for completed interview
  async getFeedback(sessionId: string): Promise<FeedbackResponse> {
    return this.request<FeedbackResponse>(
      `/api/interviews/${sessionId}/feedback`
    )
  }

  // Get all interview sessions history
  async getHistory(): Promise<SessionHistoryItem[]> {
    return this.request<SessionHistoryItem[]>('/api/interviews/history')
  }

  // Manually complete an interview early
  async completeInterview(sessionId: string): Promise<{ message: string; session_id: string; questions_answered: number }> {
    return this.request<{ message: string; session_id: string; questions_answered: number }>(
      `/api/interviews/${sessionId}/complete`,
      {
        method: 'POST',
      }
    )
  }

  // Delete an interview session
  async deleteSession(sessionId: string): Promise<void> {
    return this.request<void>(`/api/interviews/${sessionId}`, {
      method: 'DELETE',
    })
  }
}

export const apiClient = new APIClient()
