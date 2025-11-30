"use client"

import { motion } from "framer-motion"
import { X, Download, User, Stethoscope } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useState, useEffect } from "react"
import { getTextReport, generateAndDownloadPDF } from "@/lib/backend-api"

interface ReportViewerProps {
  consultationId: string
  reportType: 'patient' | 'physician'
  isOpen: boolean
  onClose: () => void
}

export function ReportViewer({ consultationId, reportType, isOpen, onClose }: ReportViewerProps) {
  const [reportText, setReportText] = useState<string>("")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [downloading, setDownloading] = useState(false)

  useEffect(() => {
    if (isOpen) {
      loadReport()
    }
  }, [isOpen, consultationId, reportType])

  const loadReport = async () => {
    setLoading(true)
    setError(null)

    try {
      const result = await getTextReport(consultationId, reportType)

      if (result.success && result.data) {
        setReportText(result.data.report_text)
      } else {
        throw new Error(result.error || 'Failed to load report')
      }
    } catch (err) {
      console.error('Report load error:', err)
      if (err instanceof Error && err.message.includes('404')) {
        setError('Report not ready yet. Please complete the consultation first.')
      } else {
        setError('Failed to load report. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadPDF = async () => {
    setDownloading(true)
    try {
      await generateAndDownloadPDF(consultationId, reportType)
    } catch (err) {
      console.error('Download error:', err)
    } finally {
      setDownloading(false)
    }
  }

  const formatReportText = (text: string) => {
    // Split by lines
    const lines = text.split('\n')
    const formatted: JSX.Element[] = []

    lines.forEach((line, index) => {
      const trimmed = line.trim()

      // Skip empty lines but add spacing
      if (!trimmed) {
        formatted.push(<div key={`space-${index}`} className="h-2" />)
        return
      }

      // Headers (all caps or lines with === or ---)
      if (trimmed.match(/^={3,}/) || trimmed.match(/^-{3,}/)) {
        formatted.push(<div key={index} className="border-t-2 border-border my-3" />)
      } else if (trimmed === trimmed.toUpperCase() && trimmed.length > 3 && !trimmed.includes(':')) {
        formatted.push(
          <h2 key={index} className="text-xl font-bold text-primary mt-4 mb-2">
            {trimmed}
          </h2>
        )
      }
      // Subheaders (ends with :)
      else if (trimmed.endsWith(':') && !trimmed.startsWith('-') && !trimmed.startsWith('•')) {
        formatted.push(
          <h3 key={index} className="text-lg font-semibold text-foreground mt-3 mb-1">
            {trimmed}
          </h3>
        )
      }
      // Bullet points
      else if (trimmed.startsWith('-') || trimmed.startsWith('•') || trimmed.match(/^\d+\./)) {
        formatted.push(
          <li key={index} className="ml-6 mb-1 text-foreground leading-relaxed">
            {trimmed.replace(/^[-•]\s*/, '').replace(/^\d+\.\s*/, '')}
          </li>
        )
      }
      // Key-value pairs (contains : but not at end)
      else if (trimmed.includes(':') && !trimmed.endsWith(':')) {
        const [key, ...valueParts] = trimmed.split(':')
        const value = valueParts.join(':').trim()
        formatted.push(
          <p key={index} className="mb-2">
            <span className="font-semibold text-foreground">{key}:</span>{' '}
            <span className="text-muted-foreground">{value}</span>
          </p>
        )
      }
      // Regular paragraph
      else {
        formatted.push(
          <p key={index} className="text-foreground leading-relaxed mb-2">
            {trimmed}
          </p>
        )
      }
    })

    return formatted
  }

  if (!isOpen) return null

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.95, opacity: 0 }}
        onClick={(e) => e.stopPropagation()}
        className="bg-background rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl border-2 border-border"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b-2 border-border bg-card rounded-t-2xl">
          <div className="flex items-center gap-3">
            {reportType === 'patient' ? (
              <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                <User className="w-6 h-6 text-primary" />
              </div>
            ) : (
              <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                <Stethoscope className="w-6 h-6 text-primary" />
              </div>
            )}
            <div>
              <h2 className="text-2xl font-bold text-foreground">
                {reportType === 'patient' ? 'Patient Summary' : 'Physician Report'}
              </h2>
              <p className="text-sm text-muted-foreground">
                {reportType === 'patient'
                  ? 'Easy-to-understand health summary'
                  : 'Detailed medical consultation report'}
              </p>
            </div>
          </div>
          <Button
            onClick={onClose}
            variant="ghost"
            size="icon"
            className="rounded-full w-10 h-10"
          >
            <X className="w-6 h-6" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                <p className="text-lg text-muted-foreground">Loading report...</p>
              </div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-center max-w-md">
                <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center mx-auto mb-4">
                  <X className="w-8 h-8 text-destructive" />
                </div>
                <p className="text-lg font-semibold text-foreground mb-2">Error Loading Report</p>
                <p className="text-muted-foreground">{error}</p>
                <Button onClick={loadReport} className="mt-4">
                  Try Again
                </Button>
              </div>
            </div>
          ) : (
            <div className="prose prose-sm max-w-none">
              <div className="bg-card rounded-xl p-6 border border-border">
                {formatReportText(reportText)}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between gap-3 p-6 border-t-2 border-border bg-card rounded-b-2xl">
          <p className="text-sm text-muted-foreground">
            Case ID: <span className="font-mono text-foreground">{consultationId.substring(0, 8)}</span>
          </p>
          <div className="flex gap-2">
            <Button onClick={onClose} variant="outline" className="h-10">
              Close
            </Button>
            <Button
              onClick={handleDownloadPDF}
              disabled={downloading || loading || !!error}
              className="h-10"
            >
              {downloading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                  Downloading...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4 mr-2" />
                  Download PDF
                </>
              )}
            </Button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}
