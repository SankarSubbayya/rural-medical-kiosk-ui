/**
 * Kiosk Services - Integration Placeholders
 *
 * This file contains all the business logic and API integration points
 * for the medical kiosk application. Replace placeholder implementations
 * with actual API calls for production use.
 */

// ============================================
// TYPES & INTERFACES
// ============================================

export interface UserSession {
  phoneNumber: string
  name: string
  healthCardId?: string
}

export interface QRScanResult {
  success: boolean
  userId?: string
  name?: string
  healthCardId?: string
  error?: string
}

export interface VoiceRecognitionResult {
  success: boolean
  transcript?: string
  confidence?: number
  error?: string
}

export interface AIResponse {
  success: boolean
  message?: string
  audioUrl?: string
  suggestedActions?: string[]
  consultationId?: string
  error?: string
}

export interface ImageUploadResult {
  success: boolean
  imageId?: string
  analysisResult?: DermatologyAnalysis
  error?: string
}

export interface DermatologyAnalysis {
  condition?: string
  confidence: number
  severity: "low" | "medium" | "high"
  recommendations: string[]
  requiresFollowUp: boolean
}

export interface HealthReport {
  id: string
  date: string
  type: "consultation" | "dermatology" | "vitals" | "prescription"
  summary: string
  details: Record<string, unknown>
  nextSteps?: string[]
}

// ============================================
// AUTHENTICATION SERVICES
// ============================================

/**
 * Authenticate user via QR code scan
 * @placeholder Replace with actual QR scanning and backend authentication
 */
export async function authenticateWithQRCode(): Promise<QRScanResult> {
  // PLACEHOLDER: Integrate with QR scanner hardware/library
  // Example: const scanResult = await QRScanner.scan()

  // PLACEHOLDER: Validate scanned data with backend
  // Example: const authResult = await fetch('/api/auth/qr', { ... })

  // Simulated response for development
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        success: true,
        userId: "user_123",
        name: "Patient",
        healthCardId: "HC-2024-001234",
      })
    }, 1500)
  })
}

/**
 * Authenticate user via phone number
 * @placeholder Replace with actual OTP/SMS verification
 */
export async function authenticateWithPhone(phoneNumber: string): Promise<QRScanResult> {
  // PLACEHOLDER: Send OTP to phone number
  // Example: await fetch('/api/auth/send-otp', { body: { phoneNumber } })

  // PLACEHOLDER: Verify OTP entered by user
  // Example: await fetch('/api/auth/verify-otp', { body: { phoneNumber, otp } })

  // Simulated response for development
  return new Promise((resolve) => {
    setTimeout(() => {
      if (phoneNumber.length >= 10) {
        resolve({
          success: true,
          userId: "user_" + phoneNumber.slice(-4),
          name: "Patient",
        })
      } else {
        resolve({
          success: false,
          error: "Invalid phone number",
        })
      }
    }, 1000)
  })
}

// ============================================
// VOICE INTERACTION SERVICES
// ============================================

// Active recording state
let mediaRecorder: MediaRecorder | null = null
let audioChunks: Blob[] = []

/**
 * Start voice recognition
 * Uses browser MediaRecorder API to capture audio, then sends to FastAPI backend with Whisper
 */
export async function startVoiceRecognition(language: string = 'en'): Promise<VoiceRecognitionResult> {
  try {
    // Request microphone access
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

    // Create MediaRecorder
    audioChunks = []
    mediaRecorder = new MediaRecorder(stream)

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.push(event.data)
      }
    }

    // Start recording
    mediaRecorder.start()

    // Return a promise that resolves when recording is stopped
    return new Promise((resolve) => {
      if (!mediaRecorder) {
        resolve({
          success: false,
          error: 'MediaRecorder not initialized',
        })
        return
      }

      mediaRecorder.onstop = async () => {
        // Stop all tracks to release microphone
        stream.getTracks().forEach((track) => track.stop())

        // Create audio blob
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })

        // Send to backend for transcription
        try {
          const { transcribeSpeech } = await import('./backend-api')
          const response = await transcribeSpeech({
            audio: audioBlob,
            language,
          })

          if (!response.success || !response.data) {
            resolve({
              success: false,
              error: response.error || 'Transcription failed',
            })
            return
          }

          resolve({
            success: true,
            transcript: response.data.transcript,
            confidence: response.data.confidence,
          })
        } catch (error) {
          resolve({
            success: false,
            error: error instanceof Error ? error.message : 'Transcription error',
          })
        }
      }
    })
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Microphone access denied',
    }
  }
}

/**
 * Stop voice recognition and trigger transcription
 */
export function stopVoiceRecognition(): void {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
  }
}

/**
 * Send message to AI health assistant and get response
 * Uses FastAPI backend with Ollama (gpt-oss:20b)
 */
export async function sendMessageToAI(
  message: string,
  conversationHistory?: Array<{ role: string; content: string }>,
  consultationId?: string,
  imageBase64?: string,
): Promise<AIResponse> {
  try {
    console.log('=== CALLING BACKEND API ===', { hasImage: !!imageBase64 })

    // Call the agent endpoint directly (Ollama SOAP agent)
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

    const requestBody: any = {
      message,
      consultation_id: consultationId,
      patient_id: 'web-user-' + Date.now(),
      language: 'en',
    }

    // Include image if provided
    if (imageBase64) {
      requestBody.image_base64 = imageBase64
    }

    const response = await fetch(`${BACKEND_URL}/agent/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      return {
        success: false,
        error: errorData.detail || `HTTP ${response.status}`,
      }
    }

    const data = await response.json()
    console.log('=== AI RESULT ===', data)

    return {
      success: data.success || true,
      message: data.message,
      consultationId: data.consultation_id,
      suggestedActions: data.suggested_actions,
    }
  } catch (error) {
    console.error('=== AI ERROR ===', error)
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Network error',
    }
  }
}

/**
 * Convert text to speech for AI responses
 * Uses FastAPI backend with gTTS
 */
export async function textToSpeech(text: string, language: string = 'en'): Promise<{ audioUrl: string } | null> {
  try {
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

    const response = await fetch(`${BACKEND_URL}/speech/synthesize`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text, language }),
    })

    if (!response.ok) {
      console.error('TTS error: HTTP', response.status)
      return null
    }

    const data = await response.json()

    // Convert base64 audio to blob URL for playback
    if (data.audio_base64) {
      // Convert base64 to blob
      const byteCharacters = atob(data.audio_base64)
      const byteNumbers = new Array(byteCharacters.length)
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i)
      }
      const byteArray = new Uint8Array(byteNumbers)
      const audioBlob = new Blob([byteArray], { type: 'audio/mp3' })

      // Create object URL
      const audioUrl = URL.createObjectURL(audioBlob)
      return { audioUrl }
    }

    return null
  } catch (error) {
    console.error('TTS error:', error)
    return null
  }
}

// ============================================
// CAMERA & IMAGE SERVICES
// ============================================

/**
 * Capture image from device camera
 * @placeholder Replace with actual camera integration
 */
export async function captureImage(): Promise<{ imageData: string } | null> {
  // PLACEHOLDER: Access device camera
  // Example:
  // const stream = await navigator.mediaDevices.getUserMedia({ video: true })
  // const track = stream.getVideoTracks()[0]
  // const imageCapture = new ImageCapture(track)
  // const blob = await imageCapture.takePhoto()

  return null
}

/**
 * Upload and analyze dermatology image
 * Uses FastAPI backend with MedGemma + SigLIP RAG
 */
export async function analyzeDermatologyImage(
  imageData: string | Blob | File,
  bodyLocation?: string,
  consultationId?: string,
): Promise<ImageUploadResult> {
  try {
    const { analyzeImage } = await import('./backend-api')

    // Convert base64 to Blob if needed
    let imageBlob: Blob | File
    if (typeof imageData === 'string') {
      // Handle data URL (e.g., "data:image/jpeg;base64,...")
      const base64Data = imageData.includes(',') ? imageData.split(',')[1] : imageData
      const byteCharacters = atob(base64Data)
      const byteNumbers = new Array(byteCharacters.length)
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i)
      }
      const byteArray = new Uint8Array(byteNumbers)
      imageBlob = new Blob([byteArray], { type: 'image/jpeg' })
    } else {
      imageBlob = imageData
    }

    // Analyze image
    const response = await analyzeImage({
      image: imageBlob,
      body_location: bodyLocation,
      consultation_id: consultationId,
    })

    if (!response.success || !response.data) {
      return {
        success: false,
        error: response.error || 'Failed to analyze image',
      }
    }

    const analysis = response.data

    return {
      success: true,
      imageId: consultationId || 'img_' + Date.now(),
      analysisResult: {
        condition: analysis.condition,
        confidence: analysis.confidence,
        severity: analysis.severity,
        recommendations: analysis.recommendations,
        requiresFollowUp: analysis.requires_followup,
      },
    }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Image analysis failed',
    }
  }
}

// ============================================
// HEALTH RECORDS SERVICES
// ============================================

/**
 * Fetch user's health history/timeline
 * @placeholder Replace with actual health records API
 */
export async function fetchHealthHistory(userId: string): Promise<HealthReport[]> {
  // PLACEHOLDER: Fetch from health records database
  // Example:
  // const reports = await fetch(`/api/health-records/${userId}`)

  // PLACEHOLDER: Consider:
  // - FHIR-compliant data structures
  // - HL7 integration for hospital systems
  // - Secure data encryption

  // Simulated response for development
  return [
    {
      id: "1",
      date: "2024-01-15",
      type: "consultation",
      summary: "Fever and headache",
      details: { temperature: 101.2, symptoms: ["headache", "fatigue"] },
      nextSteps: ["Take prescribed medicine", "Rest for 2 days"],
    },
    {
      id: "2",
      date: "2024-01-10",
      type: "dermatology",
      summary: "Skin rash examination",
      details: { location: "arm", severity: "mild" },
      nextSteps: ["Apply cream twice daily"],
    },
  ]
}

/**
 * Save consultation report
 * @placeholder Replace with actual save functionality
 */
export async function saveConsultationReport(
  userId: string,
  consultationData: Record<string, unknown>,
): Promise<{ reportId: string }> {
  // PLACEHOLDER: Save to health records database
  // Example:
  // const result = await fetch('/api/health-records', {
  //   method: 'POST',
  //   body: JSON.stringify({ userId, ...consultationData }),
  // })

  return { reportId: "report_" + Date.now() }
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

/**
 * Check network connectivity for offline support
 */
export function checkConnectivity(): boolean {
  // PLACEHOLDER: Implement robust connectivity check
  return typeof navigator !== "undefined" ? navigator.onLine : true
}

/**
 * Queue action for later sync (offline support)
 * @placeholder Replace with actual offline queue implementation
 */
export function queueForSync(action: Record<string, unknown>): void {
  // PLACEHOLDER: Store in IndexedDB or localStorage
  // Example:
  // const queue = JSON.parse(localStorage.getItem('syncQueue') || '[]')
  // queue.push({ ...action, timestamp: Date.now() })
  // localStorage.setItem('syncQueue', JSON.stringify(queue))
}

/**
 * Sync queued actions when online
 * @placeholder Replace with actual sync implementation
 */
export async function syncQueuedActions(): Promise<void> {
  // PLACEHOLDER: Process queued actions
  // Example:
  // const queue = JSON.parse(localStorage.getItem('syncQueue') || '[]')
  // for (const action of queue) {
  //   await processAction(action)
  // }
  // localStorage.setItem('syncQueue', '[]')
}
