"use client"

import { useState, useRef, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Mic, MicOff, Keyboard, Send, Volume2, Camera, FileText, Download } from "lucide-react"
import { Button } from "@/components/ui/button"
import { AiAvatar } from "@/components/kiosk/ai-avatar"
import { CameraCapture } from "@/components/kiosk/camera-capture"
import { ReportViewer } from "@/components/kiosk/report-viewer"
import * as KioskServices from "@/lib/kiosk-services"
import { generateAndDownloadPDF } from "@/lib/backend-api"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  isPlaying?: boolean
  imageData?: string
}

interface ConsultationScreenProps {
  userName: string
}

export function ConsultationScreen({ userName }: ConsultationScreenProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: `Hello ${userName}! I'm here to help you today. You can tell me what hurts or any health concerns you have. I'm listening.`,
    },
  ])
  const [isListening, setIsListening] = useState(false)
  const [showTextInput, setShowTextInput] = useState(false)
  const [textInput, setTextInput] = useState("")
  const [currentlyPlaying, setCurrentlyPlaying] = useState<string | null>(null)
  const [highlightedWordIndex, setHighlightedWordIndex] = useState(0)
  const [showCamera, setShowCamera] = useState(false)
  const [consultationId, setConsultationId] = useState<string | undefined>(undefined)
  const [pendingImage, setPendingImage] = useState<string | undefined>(undefined)
  const [showReportMenu, setShowReportMenu] = useState(false)
  const [isDownloading, setIsDownloading] = useState(false)
  const [showReportViewer, setShowReportViewer] = useState(false)
  const [viewingReportType, setViewingReportType] = useState<'patient' | 'physician'>('patient')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  // Simulate word-by-word highlighting for the playing message
  useEffect(() => {
    if (currentlyPlaying) {
      const message = messages.find((m) => m.id === currentlyPlaying)
      if (message) {
        const words = message.content.split(" ")
        const interval = setInterval(() => {
          setHighlightedWordIndex((prev) => {
            if (prev >= words.length - 1) {
              clearInterval(interval)
              setTimeout(() => setCurrentlyPlaying(null), 500)
              return 0
            }
            return prev + 1
          })
        }, 200)
        return () => clearInterval(interval)
      }
    }
  }, [currentlyPlaying, messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Function to play text-to-speech for AI messages
  const playTextToSpeech = async (text: string, messageId: string) => {
    try {
      // Stop any currently playing audio
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current = null
      }

      // Get TTS audio from backend
      const ttsResult = await KioskServices.textToSpeech(text, 'en')

      if (ttsResult && ttsResult.audioUrl) {
        // Create and play audio
        const audio = new Audio(ttsResult.audioUrl)
        audioRef.current = audio

        // Set currently playing state
        setCurrentlyPlaying(messageId)
        setHighlightedWordIndex(0)

        // Handle audio events
        audio.onended = () => {
          setCurrentlyPlaying(null)
          setHighlightedWordIndex(0)
          audioRef.current = null
          // Clean up object URL
          URL.revokeObjectURL(ttsResult.audioUrl)
        }

        audio.onerror = () => {
          console.error('Audio playback error')
          setCurrentlyPlaying(null)
          setHighlightedWordIndex(0)
          audioRef.current = null
        }

        // Play the audio
        await audio.play()
      }
    } catch (error) {
      console.error('TTS error:', error)
      setCurrentlyPlaying(null)
    }
  }

  const handleVoiceToggle = async () => {
    setIsListening(!isListening)

    if (!isListening) {
      const result = await KioskServices.startVoiceRecognition()
      setIsListening(false)

      if (result.success && result.transcript) {
        const userMessage: Message = {
          id: Date.now().toString(),
          role: "user",
          content: result.transcript,
        }
        setMessages((prev) => [...prev, userMessage])

        // Get AI response (include pending image if available)
        const aiResult = await KioskServices.sendMessageToAI(
          result.transcript,
          undefined,
          consultationId,
          pendingImage
        )

        // Clear pending image after sending
        if (pendingImage) {
          setPendingImage(undefined)
        }

        // Store consultation ID from first response
        if (aiResult.success && aiResult.consultationId && !consultationId) {
          setConsultationId(aiResult.consultationId)
        }

        if (aiResult.success && aiResult.message) {
          const aiResponse: Message = {
            id: (Date.now() + 1).toString(),
            role: "assistant",
            content: aiResult.message,
          }
          setMessages((prev) => [...prev, aiResponse])
          // Play TTS for AI response
          playTextToSpeech(aiResult.message, aiResponse.id)
        }
      }
    } else {
      KioskServices.stopVoiceRecognition()
    }
  }

  const handleTextSubmit = async () => {
    if (!textInput.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: textInput,
    }
    setMessages((prev) => [...prev, userMessage])
    const messageToSend = textInput
    setTextInput("")

    // Send message with pending image if available
    const aiResult = await KioskServices.sendMessageToAI(
      messageToSend,
      undefined,
      consultationId,
      pendingImage
    )

    // Clear pending image after sending
    if (pendingImage) {
      setPendingImage(undefined)
    }

    // Store consultation ID from first response
    if (aiResult.success && aiResult.consultationId && !consultationId) {
      setConsultationId(aiResult.consultationId)
    }

    if (aiResult.success && aiResult.message) {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: aiResult.message,
      }
      setMessages((prev) => [...prev, aiResponse])
      // Play TTS for AI response
      playTextToSpeech(aiResult.message, aiResponse.id)
    }
  }

  const handleImageCapture = (imageData: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: "I've taken a photo of the affected area.",
      imageData,
    }
    setMessages((prev) => [...prev, userMessage])
    // Store image to be sent with next message
    setPendingImage(imageData)
  }

  const handleAnalysisComplete = (result: KioskServices.ImageUploadResult) => {
    if (result.success && result.analysisResult) {
      const analysis = result.analysisResult
      const messageContent = `I've analyzed the image you shared. ${
        analysis.condition
          ? `It appears to be ${analysis.condition} with ${analysis.severity} severity.`
          : "Let me take a closer look."
      } ${analysis.recommendations.join(" ")} ${
        analysis.requiresFollowUp ? "I recommend scheduling a follow-up with a healthcare provider." : ""
      }`
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: messageContent,
      }
      setMessages((prev) => [...prev, aiResponse])
      // Play TTS for AI response
      playTextToSpeech(messageContent, aiResponse.id)
    }
  }

  const handleDownloadReport = async (reportType: 'patient' | 'physician') => {
    if (!consultationId) {
      alert('No consultation available to generate report')
      return
    }

    setIsDownloading(true)
    setShowReportMenu(false)

    try {
      const result = await generateAndDownloadPDF(consultationId, reportType)

      if (result.success) {
        const reportLabel = reportType === 'patient' ? 'Patient Summary' : 'Physician Report'
        const successMessage: Message = {
          id: Date.now().toString(),
          role: "assistant",
          content: `${reportLabel} has been downloaded successfully. You can find it in your downloads folder.`,
        }
        setMessages((prev) => [...prev, successMessage])
        playTextToSpeech(successMessage.content, successMessage.id)
      } else {
        throw new Error(result.error || 'Failed to download report')
      }
    } catch (error) {
      console.error('Report download error:', error)
      let errorText = `Sorry, I couldn't generate the report.`

      // Provide helpful error message based on the error
      if (error instanceof Error) {
        if (error.message.includes('404')) {
          errorText = `The consultation report is not ready yet. Please complete the consultation first by describing your symptoms and uploading an image.`
        } else if (error.message.includes('500')) {
          errorText = `There was an error generating the report. Please try again later.`
        }
      }

      const errorMessage: Message = {
        id: Date.now().toString(),
        role: "assistant",
        content: errorText,
      }
      setMessages((prev) => [...prev, errorMessage])
      playTextToSpeech(errorMessage.content, errorMessage.id)
    } finally {
      setIsDownloading(false)
    }
  }

  const handleViewReport = (reportType: 'patient' | 'physician') => {
    if (!consultationId) {
      alert('No consultation available to view report')
      return
    }

    setViewingReportType(reportType)
    setShowReportViewer(true)
    setShowReportMenu(false)
  }

  const renderHighlightedText = (message: Message) => {
    if (currentlyPlaying !== message.id) {
      return <span>{message.content}</span>
    }

    const words = message.content.split(" ")
    return (
      <span>
        {words.map((word, index) => (
          <span
            key={index}
            className={`transition-colors duration-150 ${
              index <= highlightedWordIndex ? "text-primary font-semibold" : "text-foreground"
            }`}
          >
            {word}{" "}
          </span>
        ))}
      </span>
    )
  }

  return (
    <div className="h-full flex flex-col bg-background overflow-hidden relative">
      {/* Floating Report Button */}
      {consultationId && (
        <motion.button
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setShowReportMenu(true)}
          className="absolute top-4 right-4 z-10 w-12 h-12 rounded-full bg-primary text-primary-foreground shadow-lg flex items-center justify-center hover:bg-primary/90 transition-colors"
          aria-label="View Reports"
        >
          <FileText className="w-6 h-6" />
        </motion.button>
      )}

      {/* Report Menu Modal */}
      <AnimatePresence>
        {showReportMenu && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/50 z-20 flex items-center justify-center p-4"
            onClick={() => setShowReportMenu(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-card rounded-2xl p-6 max-w-md w-full border-2 border-border shadow-xl"
            >
              <h2 className="text-2xl font-bold text-foreground mb-4">Download Reports</h2>
              <p className="text-base text-muted-foreground mb-6">
                Choose which report you would like to download or view:
              </p>

              <div className="space-y-3">
                {/* Patient Report */}
                <div className="border-2 border-border rounded-xl p-4">
                  <h3 className="font-semibold text-lg text-foreground mb-2">Patient Summary</h3>
                  <p className="text-sm text-muted-foreground mb-3">
                    Easy-to-read summary for patients in simple language
                  </p>
                  <div className="flex gap-2">
                    <Button
                      onClick={() => handleViewReport('patient')}
                      disabled={isDownloading}
                      variant="outline"
                      className="flex-1 h-10 text-base"
                    >
                      <FileText className="w-4 h-4 mr-2" />
                      View
                    </Button>
                    <Button
                      onClick={() => handleDownloadReport('patient')}
                      disabled={isDownloading}
                      className="flex-1 h-10 text-base"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Download PDF
                    </Button>
                  </div>
                </div>

                {/* Physician Report */}
                <div className="border-2 border-border rounded-xl p-4">
                  <h3 className="font-semibold text-lg text-foreground mb-2">Physician Report</h3>
                  <p className="text-sm text-muted-foreground mb-3">
                    Detailed medical report with SOAP format and ICD-10 codes
                  </p>
                  <div className="flex gap-2">
                    <Button
                      onClick={() => handleViewReport('physician')}
                      disabled={isDownloading}
                      variant="outline"
                      className="flex-1 h-10 text-base"
                    >
                      <FileText className="w-4 h-4 mr-2" />
                      View
                    </Button>
                    <Button
                      onClick={() => handleDownloadReport('physician')}
                      disabled={isDownloading}
                      className="flex-1 h-10 text-base"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Download PDF
                    </Button>
                  </div>
                </div>
              </div>

              <Button
                onClick={() => setShowReportMenu(false)}
                variant="ghost"
                className="w-full mt-4 h-10 text-base"
              >
                Close
              </Button>

              {isDownloading && (
                <div className="absolute inset-0 bg-background/80 rounded-2xl flex items-center justify-center">
                  <div className="text-center">
                    <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                    <p className="text-foreground font-semibold">Generating report...</p>
                  </div>
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex-shrink-0 bg-card border-b-2 border-border p-3">
        <AiAvatar isListening={isListening} isSpeaking={currentlyPlaying !== null} />
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto p-3 space-y-3">
        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl p-4 ${
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-card border-2 border-border text-card-foreground"
                }`}
              >
                {message.imageData && (
                  <div className="mb-2 rounded-xl overflow-hidden">
                    <img
                      src={message.imageData || "/placeholder.svg"}
                      alt="Captured"
                      className="w-full max-w-[150px] h-auto"
                    />
                  </div>
                )}
                <p className="text-lg leading-relaxed">
                  {message.role === "assistant" ? renderHighlightedText(message) : message.content}
                </p>
                {message.role === "assistant" && currentlyPlaying === message.id && (
                  <div className="flex items-center gap-2 mt-2 text-primary">
                    <Volume2 className="w-4 h-4 animate-pulse" />
                    <span className="text-sm">Speaking...</span>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={messagesEndRef} />
      </div>

      <div className="flex-shrink-0 bg-card border-t-2 border-border p-3">
        <AnimatePresence mode="wait">
          {showTextInput ? (
            <motion.div
              key="text"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="space-y-2"
            >
              <div className="flex gap-2">
                <input
                  type="text"
                  value={textInput}
                  onChange={(e) => setTextInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleTextSubmit()}
                  placeholder="Type your message here..."
                  className="flex-1 h-12 px-4 text-lg rounded-xl bg-input border-2 border-border focus:border-primary focus:outline-none text-foreground placeholder:text-muted-foreground"
                />
                <Button
                  onClick={handleTextSubmit}
                  disabled={!textInput.trim()}
                  className="h-12 w-12 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground disabled:opacity-50"
                >
                  <Send className="w-5 h-5" />
                </Button>
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={() => setShowCamera(true)}
                  variant="outline"
                  className="flex-1 text-base border-2 h-10 rounded-lg"
                >
                  <Camera className="w-4 h-4 mr-2" />
                  Take Photo
                </Button>
                <Button
                  onClick={() => setShowTextInput(false)}
                  variant="ghost"
                  className="flex-1 text-base text-muted-foreground hover:text-foreground h-10"
                >
                  <Mic className="w-4 h-4 mr-2" />
                  Use voice instead
                </Button>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="voice"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              className="flex flex-col items-center gap-2"
            >
              <div className="flex items-center gap-4">
                {/* Camera button */}
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setShowCamera(true)}
                  className="w-14 h-14 rounded-full flex items-center justify-center bg-accent border-2 border-border hover:border-primary transition-colors"
                  aria-label="Take a photo"
                >
                  <Camera className="w-6 h-6 text-foreground" />
                </motion.button>

                {/* Main voice button */}
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={handleVoiceToggle}
                  className={`w-20 h-20 rounded-full flex items-center justify-center transition-all ${
                    isListening ? "bg-destructive animate-pulse-glow" : "bg-primary animate-pulse-glow"
                  }`}
                  aria-label={isListening ? "Stop listening" : "Start speaking"}
                >
                  {isListening ? (
                    <MicOff className="w-10 h-10 text-primary-foreground" />
                  ) : (
                    <Mic className="w-10 h-10 text-primary-foreground" />
                  )}
                </motion.button>

                {/* Placeholder for symmetry */}
                <div className="w-14 h-14" />
              </div>

              <p className="text-xl font-semibold text-foreground text-center">
                {isListening ? "I'm listening..." : "Tell me what hurts"}
              </p>

              {/* Type instead option */}
              <Button
                onClick={() => setShowTextInput(true)}
                variant="ghost"
                className="text-base text-muted-foreground hover:text-foreground h-8"
              >
                <Keyboard className="w-4 h-4 mr-2" />
                Type instead
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <CameraCapture
        isOpen={showCamera}
        onClose={() => setShowCamera(false)}
        onCapture={handleImageCapture}
        onAnalysisComplete={handleAnalysisComplete}
        consultationId={consultationId}
      />

      {consultationId && (
        <ReportViewer
          consultationId={consultationId}
          reportType={viewingReportType}
          isOpen={showReportViewer}
          onClose={() => setShowReportViewer(false)}
        />
      )}
    </div>
  )
}
