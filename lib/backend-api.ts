/**
 * Backend API Client
 *
 * TypeScript client for FastAPI backend endpoints
 */

// ============================================
// CONFIGURATION
// ============================================

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

// Debug: Log the backend URL on load
if (typeof window !== 'undefined') {
  console.log('[BackendAPI] BACKEND_URL:', BACKEND_URL)
  console.log('[BackendAPI] ENV:', process.env.NEXT_PUBLIC_BACKEND_URL)
}

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
  message: string
  message_type?: string
  audio_url?: string | null
  audio_base64?: string | null
  current_stage?: string
  stage_progress?: number
  suggested_actions?: string[]
  requires_image?: boolean
  requires_confirmation?: boolean
  consultation_complete?: boolean
  detected_language?: string
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
      const url = `${this.baseUrl}${endpoint}`
      console.log('[BackendAPI] Fetching:', url)
      const response = await fetch(url, {
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
      body: JSON.stringify({
        patient_id: userId || 'anonymous-' + Date.now(),
        language: 'en'
      }),
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
    // Convert image file to base64
    const imageBase64 = await this.fileToBase64(request.image)

    const payload = {
      consultation_id: request.consultation_id,
      image_base64: imageBase64,
      body_location: {
        primary: request.body_location || 'unknown',
        specific: null
      }
    }

    return this.postRequest<ImageAnalysisResponse>('/analyze/image', payload)
  }

  // Helper method to convert File/Blob to base64
  private async fileToBase64(file: File | Blob): Promise<string> {
    if (!file) {
      throw new Error('No file provided to fileToBase64')
    }

    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onloadend = () => {
        const result = reader.result as string
        if (!result) {
          reject(new Error('FileReader returned empty result'))
          return
        }
        // Remove the data URL prefix (e.g., "data:image/jpeg;base64,")
        const base64 = result.split(',')[1]
        if (!base64) {
          reject(new Error('Failed to extract base64 from data URL'))
          return
        }
        resolve(base64)
      }
      reader.onerror = (error) => {
        console.error('FileReader error:', error)
        reject(error)
      }
      reader.readAsDataURL(file)
    })
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
    // Convert audio blob to base64
    const audioBase64 = await this.blobToBase64(request.audio)

    return this.request<SpeechTranscriptionResponse>('/speech/transcribe', {
      method: 'POST',
      body: JSON.stringify({
        audio_base64: audioBase64,
        language: request.language || null
      }),
    })
  }

  /**
   * Convert Blob/File to base64 string
   */
  private async blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onloadend = () => {
        const result = reader.result as string
        // Remove data URL prefix (e.g., "data:audio/webm;base64,")
        const base64 = result.split(',')[1] || result
        resolve(base64)
      }
      reader.onerror = reject
      reader.readAsDataURL(blob)
    })
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
    const audioBase64 = await this.blobToBase64(audioFile)

    return this.request<{ language: string }>('/speech/detect-language', {
      method: 'POST',
      body: JSON.stringify({
        audio_base64: audioBase64
      }),
    })
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

  async downloadReportPDF(consultationId: string): Promise<Blob | null> {
    try {
      const response = await fetch(`${this.baseUrl}/report/${consultationId}/pdf`)

      if (!response.ok) {
        return null
      }

      return await response.blob()
    } catch (error) {
      console.error('PDF download error:', error)
      return null
    }
  }

  /**
   * Generate and download PDF report for a consultation
   */
  async generateAndDownloadPDF(consultationId: string, reportType: 'patient' | 'physician' = 'physician'): Promise<{ success: boolean; error?: string }> {
    try {
      // Fetch PDF directly
      const response = await fetch(`${this.baseUrl}/report/${consultationId}/pdf`)

      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown error')
        console.error('PDF generation failed:', response.status, errorText)
        return {
          success: false,
          error: `Failed to generate PDF report: ${response.status} ${response.statusText}`
        }
      }

      const blob = await response.blob()

      // Create download link
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      const reportLabel = reportType === 'patient' ? 'patient-summary' : 'physician-report'
      link.download = `medical-${reportLabel}-${consultationId.substring(0, 8)}.pdf`
      document.body.appendChild(link)
      link.click()

      // Cleanup
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      return { success: true }
    } catch (error) {
      console.error('PDF download error:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }

  /**
   * Generate text report (patient or physician)
   */
  async getTextReport(consultationId: string, reportType: 'patient' | 'physician' = 'patient'): Promise<ApiResponse<{ report_text: string }>> {
    const endpoint = reportType === 'patient' ? '/report/patient' : '/report/physician'

    return this.request<{ report_text: string }>(endpoint, {
      method: 'POST',
      body: JSON.stringify({
        consultation_id: consultationId,
        language: 'en'
      }),
    })
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

// Bind methods to preserve 'this' context
export const createConsultation = backendAPI.createConsultation.bind(backendAPI)
export const getConsultation = backendAPI.getConsultation.bind(backendAPI)
export const sendChatMessage = backendAPI.sendChatMessage.bind(backendAPI)
export const startChat = backendAPI.startChat.bind(backendAPI)
export const getChatHistory = backendAPI.getChatHistory.bind(backendAPI)
export const analyzeImage = backendAPI.analyzeImage.bind(backendAPI)
export const findSimilarCases = backendAPI.findSimilarCases.bind(backendAPI)
export const transcribeSpeech = backendAPI.transcribeSpeech.bind(backendAPI)
export const synthesizeSpeech = backendAPI.synthesizeSpeech.bind(backendAPI)
export const detectLanguage = backendAPI.detectLanguage.bind(backendAPI)
export const getSupportedLanguages = backendAPI.getSupportedLanguages.bind(backendAPI)
export const generateReport = backendAPI.generateReport.bind(backendAPI)
export const downloadReportPDF = backendAPI.downloadReportPDF.bind(backendAPI)
export const generateAndDownloadPDF = backendAPI.generateAndDownloadPDF.bind(backendAPI)
export const getTextReport = backendAPI.getTextReport.bind(backendAPI)
export const healthCheck = backendAPI.healthCheck.bind(backendAPI)
