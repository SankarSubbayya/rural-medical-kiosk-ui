"use client"

import type React from "react"

import { useState, useRef, useCallback, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Camera, X, RotateCcw, Check, Upload, ImageIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import * as KioskServices from "@/lib/kiosk-services"

interface CameraCaptureProps {
  isOpen: boolean
  onClose: () => void
  onCapture: (imageData: string) => void
  onAnalysisComplete?: (result: KioskServices.ImageUploadResult) => void
}

export function CameraCapture({ isOpen, onClose, onCapture, onAnalysisComplete }: CameraCaptureProps) {
  const [mode, setMode] = useState<"camera" | "preview" | "uploading">("camera")
  const [capturedImage, setCapturedImage] = useState<string | null>(null)
  const [cameraError, setCameraError] = useState<string | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Start camera when modal opens
  useEffect(() => {
    if (isOpen && mode === "camera") {
      startCamera()
    }
    return () => {
      stopCamera()
    }
  }, [isOpen, mode])

  const startCamera = async () => {
    try {
      setCameraError(null)
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "environment", // Prefer back camera
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
    } catch (error) {
      console.error("Camera access error:", error)
      setCameraError("Unable to access camera. Please check permissions or upload a photo instead.")
    }
  }

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
  }

  const capturePhoto = useCallback(() => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current
      const canvas = canvasRef.current
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext("2d")
      if (ctx) {
        ctx.drawImage(video, 0, 0)
        const imageData = canvas.toDataURL("image/jpeg", 0.9)
        setCapturedImage(imageData)
        setMode("preview")
        stopCamera()
      }
    }
  }, [])

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        const imageData = e.target?.result as string
        setCapturedImage(imageData)
        setMode("preview")
        stopCamera()
      }
      reader.readAsDataURL(file)
    }
  }

  const retakePhoto = () => {
    setCapturedImage(null)
    setMode("camera")
  }

  const confirmPhoto = async () => {
    if (capturedImage) {
      setIsAnalyzing(true)
      onCapture(capturedImage)

      // Call the analysis service
      const result = await KioskServices.analyzeDermatologyImage(capturedImage)

      setIsAnalyzing(false)
      if (onAnalysisComplete) {
        onAnalysisComplete(result)
      }
      handleClose()
    }
  }

  const handleClose = () => {
    stopCamera()
    setCapturedImage(null)
    setMode("camera")
    setCameraError(null)
    onClose()
  }

  if (!isOpen) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="bg-card rounded-3xl w-full max-w-2xl overflow-hidden shadow-2xl border-2 border-border"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b-2 border-border bg-muted/50">
            <h2 className="text-2xl font-bold text-foreground">
              {mode === "preview" ? "Review Photo" : "Take a Photo"}
            </h2>
            <Button onClick={handleClose} variant="ghost" size="icon" className="rounded-full w-12 h-12">
              <X className="w-6 h-6" />
            </Button>
          </div>

          {/* Content */}
          <div className="p-4">
            {/* Instructions */}
            <div className="bg-accent/50 rounded-2xl p-4 mb-4">
              <p className="text-lg text-foreground text-center">
                {mode === "camera"
                  ? "Position the affected area clearly in the frame"
                  : "Make sure the image is clear and in focus"}
              </p>
            </div>

            {/* Camera / Preview Area */}
            <div className="relative aspect-[4/3] bg-muted rounded-2xl overflow-hidden mb-4">
              {mode === "camera" && !cameraError && (
                <>
                  <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
                  {/* Capture guide overlay */}
                  <div className="absolute inset-0 pointer-events-none">
                    <div className="absolute inset-8 border-4 border-white/50 rounded-3xl" />
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                      <motion.div
                        animate={{ scale: [1, 1.1, 1] }}
                        transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY }}
                        className="w-20 h-20 border-4 border-primary rounded-full"
                      />
                    </div>
                  </div>
                </>
              )}

              {mode === "camera" && cameraError && (
                <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center">
                  <Camera className="w-16 h-16 text-muted-foreground mb-4" />
                  <p className="text-xl text-muted-foreground mb-4">{cameraError}</p>
                  <Button
                    onClick={() => fileInputRef.current?.click()}
                    className="h-14 px-6 text-xl rounded-2xl bg-primary hover:bg-primary/90"
                  >
                    <Upload className="w-6 h-6 mr-2" />
                    Upload Photo
                  </Button>
                </div>
              )}

              {mode === "preview" && capturedImage && (
                <img src={capturedImage || "/placeholder.svg"} alt="Captured" className="w-full h-full object-cover" />
              )}

              {isAnalyzing && (
                <div className="absolute inset-0 bg-black/60 flex flex-col items-center justify-center">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
                    className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full mb-4"
                  />
                  <p className="text-2xl text-white font-semibold">Analyzing image...</p>
                </div>
              )}
            </div>

            {/* Hidden elements */}
            <canvas ref={canvasRef} className="hidden" />
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handleFileUpload}
              className="hidden"
            />

            {/* Action Buttons */}
            <div className="flex gap-4">
              {mode === "camera" && !cameraError && (
                <>
                  {/* Upload alternative */}
                  <Button
                    onClick={() => fileInputRef.current?.click()}
                    variant="outline"
                    className="flex-1 h-16 text-xl rounded-2xl border-2"
                  >
                    <ImageIcon className="w-6 h-6 mr-2" />
                    Upload
                  </Button>

                  {/* Capture button */}
                  <Button
                    onClick={capturePhoto}
                    className="flex-[2] h-16 text-xl rounded-2xl bg-primary hover:bg-primary/90"
                  >
                    <Camera className="w-7 h-7 mr-2" />
                    Take Photo
                  </Button>
                </>
              )}

              {mode === "preview" && (
                <>
                  {/* Retake */}
                  <Button
                    onClick={retakePhoto}
                    variant="outline"
                    className="flex-1 h-16 text-xl rounded-2xl border-2 bg-transparent"
                    disabled={isAnalyzing}
                  >
                    <RotateCcw className="w-6 h-6 mr-2" />
                    Retake
                  </Button>

                  {/* Confirm */}
                  <Button
                    onClick={confirmPhoto}
                    className="flex-[2] h-16 text-xl rounded-2xl bg-primary hover:bg-primary/90"
                    disabled={isAnalyzing}
                  >
                    <Check className="w-7 h-7 mr-2" />
                    {isAnalyzing ? "Analyzing..." : "Use This Photo"}
                  </Button>
                </>
              )}
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}
