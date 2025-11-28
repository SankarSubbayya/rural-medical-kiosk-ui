/**
 * Backend API Client
 *
 * TypeScript client for FastAPI backend endpoints
 */

// ============================================
// CONFIGURATION
// ============================================

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

// ============================================
// TYPES
// ============================================

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
}

export interface ConsultationCreateResponse {
  consultation_id: string
  stage: 'subjective' | 'objective' | 'assessment' | 'plan'
}

export interface ChatMessageRequest {
  consultation_id: string
  message: string
  language?: string
}

export interface ChatMessageResponse {
  response: string
  suggestions?: string[]
  stage?: string
}

export interface ImageAnalysisRequest {
  image: File | Blob
  consultation_id?: string
  body_location?: string
}

export interface ImageAnalysisResponse {
  condition?: string
  confidence: number
  severity: 'low' | 'medium' | 'high'
  recommendations: string[]
  requires_followup: boolean
  similar_cases?: SimilarCase[]
}

export interface SimilarCase {
  image_path: string
  condition: string
  similarity_score: number
}

export interface SpeechTranscriptionRequest {
  audio: File | Blob
  language?: string
}

export interface SpeechTranscriptionResponse {
  transcript: string
  language: string
  confidence: number
}

export interface SpeechSynthesisRequest {
  text: string
  language?: string
}

export interface SpeechSynthesisResponse {
  audio_url: string
}

export interface ReportRequest {
  consultation_id: string
  report_type: 'patient' | 'physician'
}

export interface ReportResponse {
  report_id: string
  content: string
  pdf_url?: string
}

// ============================================
// API CLIENT CLASS
// ============================================

class BackendAPI {
  private baseUrl: string

  constructor(baseUrl: string = BACKEND_URL) {
    this.baseUrl = baseUrl
  }

  /**
   * Generic fetch wrapper with error handling
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        return {
          success: false,
          error: errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
        }
      }

      const data = await response.json()
      return {
        success: true,
        data,
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error',
      }
    }
  }

  /**
   * Multipart form data request (for file uploads)
   */
  private async uploadRequest<T>(
    endpoint: string,
    formData: FormData
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        return {
          success: false,
          error: errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
        }
      }

      const data = await response.json()
      return {
        success: true,
        data,
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Network error',
      }
    }
  }

  // ============================================
  // CONSULTATION ENDPOINTS
  // ============================================

  async createConsultation(userId?: string): Promise<ApiResponse<ConsultationCreateResponse>> {
    return this.request<ConsultationCreateResponse>('/consultation/create', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    })
  }

  async getConsultation(consultationId: string): Promise<ApiResponse<any>> {
    return this.request(`/consultation/${consultationId}`)
  }

  // ============================================
  // CHAT ENDPOINTS
  // ============================================

  async sendChatMessage(
    request: ChatMessageRequest
  ): Promise<ApiResponse<ChatMessageResponse>> {
    return this.request<ChatMessageResponse>('/chat/message', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  async startChat(consultationId: string): Promise<ApiResponse<ChatMessageResponse>> {
    return this.request<ChatMessageResponse>(`/chat/${consultationId}/start`, {
      method: 'POST',
    })
  }

  async getChatHistory(consultationId: string): Promise<ApiResponse<any>> {
    return this.request(`/chat/${consultationId}/history`)
  }

  // ============================================
  // IMAGE ANALYSIS ENDPOINTS
  // ============================================

  async analyzeImage(
    request: ImageAnalysisRequest
  ): Promise<ApiResponse<ImageAnalysisResponse>> {
    const formData = new FormData()
    formData.append('image', request.image)

    if (request.consultation_id) {
      formData.append('consultation_id', request.consultation_id)
    }

    if (request.body_location) {
      formData.append('body_location', request.body_location)
    }

    return this.uploadRequest<ImageAnalysisResponse>('/analyze/image', formData)
  }

  async findSimilarCases(
    imageFile: File | Blob,
    limit: number = 5
  ): Promise<ApiResponse<SimilarCase[]>> {
    const formData = new FormData()
    formData.append('image', imageFile)
    formData.append('limit', limit.toString())

    return this.uploadRequest<SimilarCase[]>('/analyze/similar', formData)
  }

  // ============================================
  // SPEECH ENDPOINTS
  // ============================================

  async transcribeSpeech(
    request: SpeechTranscriptionRequest
  ): Promise<ApiResponse<SpeechTranscriptionResponse>> {
    const formData = new FormData()
    formData.append('audio', request.audio)

    if (request.language) {
      formData.append('language', request.language)
    }

    return this.uploadRequest<SpeechTranscriptionResponse>('/speech/transcribe', formData)
  }

  async synthesizeSpeech(
    request: SpeechSynthesisRequest
  ): Promise<ApiResponse<SpeechSynthesisResponse>> {
    return this.request<SpeechSynthesisResponse>('/speech/synthesize', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  async detectLanguage(audioFile: File | Blob): Promise<ApiResponse<{ language: string }>> {
    const formData = new FormData()
    formData.append('audio', audioFile)

    return this.uploadRequest<{ language: string }>('/speech/detect-language', formData)
  }

  async getSupportedLanguages(): Promise<ApiResponse<{ languages: string[] }>> {
    return this.request<{ languages: string[] }>('/speech/languages')
  }

  // ============================================
  // REPORT ENDPOINTS
  // ============================================

  async generateReport(request: ReportRequest): Promise<ApiResponse<ReportResponse>> {
    const endpoint = request.report_type === 'patient'
      ? '/report/patient'
      : '/report/physician'

    return this.request<ReportResponse>(endpoint, {
      method: 'POST',
      body: JSON.stringify({ consultation_id: request.consultation_id }),
    })
  }

  async downloadReportPDF(reportId: string): Promise<Blob | null> {
    try {
      const response = await fetch(`${this.baseUrl}/report/${reportId}/pdf`)

      if (!response.ok) {
        return null
      }

      return await response.blob()
    } catch (error) {
      console.error('PDF download error:', error)
      return null
    }
  }

  // ============================================
  // HEALTH CHECK
  // ============================================

  async healthCheck(): Promise<ApiResponse<{ status: string }>> {
    return this.request<{ status: string }>('/health')
  }
}

// ============================================
// SINGLETON INSTANCE
// ============================================

export const backendAPI = new BackendAPI()

// ============================================
// CONVENIENCE EXPORTS
// ============================================

export const {
  createConsultation,
  getConsultation,
  sendChatMessage,
  startChat,
  getChatHistory,
  analyzeImage,
  findSimilarCases,
  transcribeSpeech,
  synthesizeSpeech,
  detectLanguage,
  getSupportedLanguages,
  generateReport,
  downloadReportPDF,
  healthCheck,
} = backendAPI
