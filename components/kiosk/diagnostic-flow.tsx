"use client"

import type React from "react"

import { motion } from "framer-motion"

interface FlowStep {
  step: number
  title: string
  description: string
  illustration: React.ReactNode
}

function ScanCardIllustration() {
  return (
    <svg viewBox="0 0 120 120" className="w-full h-full">
      {/* Person with friendly face */}
      <ellipse cx="60" cy="85" rx="25" ry="15" fill="#0D9488" opacity="0.3" />
      <circle cx="60" cy="45" r="22" fill="#FBBF24" />
      <circle cx="53" cy="42" r="3" fill="#1F2937" />
      <circle cx="67" cy="42" r="3" fill="#1F2937" />
      <path d="M52 52 Q60 58 68 52" stroke="#1F2937" strokeWidth="2.5" fill="none" strokeLinecap="round" />
      {/* Rosy cheeks */}
      <circle cx="48" cy="48" r="4" fill="#F472B6" opacity="0.5" />
      <circle cx="72" cy="48" r="4" fill="#F472B6" opacity="0.5" />
      {/* Body */}
      <path d="M40 65 Q60 60 80 65 L85 100 L35 100 Z" fill="#0D9488" />
      {/* Card in hand */}
      <motion.g
        animate={{ x: [0, 5, 0], rotate: [0, 5, 0] }}
        transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
      >
        <rect x="75" y="55" width="30" height="20" rx="3" fill="#FEF3C7" stroke="#FBBF24" strokeWidth="2" />
        <rect x="80" y="60" width="12" height="3" rx="1" fill="#0D9488" />
        <rect x="80" y="66" width="8" height="2" rx="1" fill="#9CA3AF" />
      </motion.g>
      {/* Scanner waves */}
      <motion.path
        d="M20 70 Q10 50 20 30"
        stroke="#0D9488"
        strokeWidth="3"
        fill="none"
        strokeLinecap="round"
        animate={{ opacity: [0.3, 1, 0.3] }}
        transition={{ duration: 1.5, repeat: Number.POSITIVE_INFINITY }}
      />
      <motion.path
        d="M12 65 Q2 50 12 35"
        stroke="#0D9488"
        strokeWidth="2"
        fill="none"
        strokeLinecap="round"
        animate={{ opacity: [0.2, 0.8, 0.2] }}
        transition={{ duration: 1.5, repeat: Number.POSITIVE_INFINITY, delay: 0.3 }}
      />
    </svg>
  )
}

function TalkAssistantIllustration() {
  return (
    <svg viewBox="0 0 120 120" className="w-full h-full">
      {/* AI Assistant character */}
      <motion.g
        animate={{ y: [0, -3, 0] }}
        transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
      >
        <circle cx="40" cy="50" r="20" fill="#0D9488" />
        <circle cx="34" cy="46" r="3" fill="white" />
        <circle cx="46" cy="46" r="3" fill="white" />
        <motion.path
          d="M32 55 Q40 62 48 55"
          stroke="white"
          strokeWidth="2.5"
          fill="none"
          strokeLinecap="round"
          animate={{ d: ["M32 55 Q40 62 48 55", "M32 56 Q40 64 48 56", "M32 55 Q40 62 48 55"] }}
          transition={{ duration: 1, repeat: Number.POSITIVE_INFINITY }}
        />
        {/* Headset */}
        <path d="M22 45 Q20 35 30 30" stroke="#1F2937" strokeWidth="3" fill="none" />
        <path d="M58 45 Q60 35 50 30" stroke="#1F2937" strokeWidth="3" fill="none" />
        <circle cx="22" cy="48" r="5" fill="#1F2937" />
      </motion.g>

      {/* Person speaking */}
      <ellipse cx="85" cy="100" rx="20" ry="10" fill="#FBBF24" opacity="0.3" />
      <circle cx="85" cy="65" r="18" fill="#FBBF24" />
      <circle cx="80" cy="62" r="2.5" fill="#1F2937" />
      <circle cx="90" cy="62" r="2.5" fill="#1F2937" />
      <motion.ellipse
        cx="85"
        cy="72"
        rx="5"
        ry="4"
        fill="#1F2937"
        animate={{ ry: [4, 6, 4], rx: [5, 6, 5] }}
        transition={{ duration: 0.5, repeat: Number.POSITIVE_INFINITY }}
      />
      {/* Body */}
      <path d="M70 80 Q85 75 100 80 L105 110 L65 110 Z" fill="#F472B6" />

      {/* Speech waves */}
      <motion.g
        animate={{ opacity: [0.4, 1, 0.4], scale: [0.9, 1, 0.9] }}
        transition={{ duration: 0.8, repeat: Number.POSITIVE_INFINITY }}
      >
        <path d="M60 55 Q55 50 60 45" stroke="#0D9488" strokeWidth="2" fill="none" strokeLinecap="round" />
        <path d="M65 58 Q58 50 65 42" stroke="#0D9488" strokeWidth="2" fill="none" strokeLinecap="round" />
      </motion.g>
    </svg>
  )
}

function TakePhotoIllustration() {
  return (
    <svg viewBox="0 0 120 120" className="w-full h-full">
      {/* Person showing arm */}
      <ellipse cx="45" cy="100" rx="22" ry="12" fill="#0D9488" opacity="0.3" />
      <circle cx="45" cy="45" r="20" fill="#FBBF24" />
      <circle cx="39" cy="42" r="3" fill="#1F2937" />
      <circle cx="51" cy="42" r="3" fill="#1F2937" />
      <path d="M38 52 Q45 56 52 52" stroke="#1F2937" strokeWidth="2" fill="none" strokeLinecap="round" />
      {/* Body */}
      <path d="M28 62 Q45 58 62 62 L65 105 L25 105 Z" fill="#0D9488" />
      {/* Extended arm */}
      <path d="M62 70 Q75 68 90 75" stroke="#FBBF24" strokeWidth="12" fill="none" strokeLinecap="round" />
      <circle cx="90" cy="75" r="8" fill="#FBBF24" />
      {/* Spot on arm to photograph */}
      <circle cx="78" cy="72" r="4" fill="#EF4444" opacity="0.7" />

      {/* Camera/Phone */}
      <motion.g animate={{ scale: [1, 1.05, 1] }} transition={{ duration: 1.5, repeat: Number.POSITIVE_INFINITY }}>
        <rect x="85" y="35" width="25" height="35" rx="4" fill="#1F2937" />
        <rect x="88" y="38" width="19" height="24" rx="2" fill="#60A5FA" />
        <circle cx="97" cy="50" r="6" stroke="white" strokeWidth="2" fill="none" />
        {/* Camera flash */}
        <motion.circle
          cx="97"
          cy="50"
          r="10"
          fill="white"
          opacity="0"
          animate={{ opacity: [0, 0.8, 0], scale: [0.5, 1.5, 0.5] }}
          transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, delay: 1 }}
        />
      </motion.g>

      {/* Focus lines */}
      <motion.g animate={{ opacity: [0.3, 1, 0.3] }} transition={{ duration: 1, repeat: Number.POSITIVE_INFINITY }}>
        <line x1="70" y1="65" x2="70" y2="60" stroke="#EF4444" strokeWidth="2" />
        <line x1="86" y1="79" x2="86" y2="84" stroke="#EF4444" strokeWidth="2" />
        <line x1="70" y1="79" x2="65" y2="79" stroke="#EF4444" strokeWidth="2" />
        <line x1="86" y1="65" x2="91" y2="65" stroke="#EF4444" strokeWidth="2" />
      </motion.g>
    </svg>
  )
}

function WaitReportIllustration() {
  return (
    <svg viewBox="0 0 120 120" className="w-full h-full">
      {/* Happy person with report */}
      <ellipse cx="60" cy="105" rx="25" ry="10" fill="#0D9488" opacity="0.3" />
      <circle cx="60" cy="50" r="22" fill="#FBBF24" />
      <circle cx="53" cy="47" r="3" fill="#1F2937" />
      <circle cx="67" cy="47" r="3" fill="#1F2937" />
      {/* Big happy smile */}
      <path d="M48 56 Q60 68 72 56" stroke="#1F2937" strokeWidth="2.5" fill="none" strokeLinecap="round" />
      {/* Rosy cheeks */}
      <circle cx="45" cy="53" r="4" fill="#F472B6" opacity="0.5" />
      <circle cx="75" cy="53" r="4" fill="#F472B6" opacity="0.5" />
      {/* Body */}
      <path d="M42 70 Q60 65 78 70 L82 110 L38 110 Z" fill="#0D9488" />

      {/* Report/clipboard in hands */}
      <motion.g
        animate={{ rotate: [-3, 3, -3], y: [0, -2, 0] }}
        transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
      >
        <rect x="45" y="80" width="30" height="38" rx="3" fill="white" stroke="#D1D5DB" strokeWidth="2" />
        <rect x="50" y="86" width="20" height="3" rx="1" fill="#0D9488" />
        <rect x="50" y="92" width="15" height="2" rx="1" fill="#9CA3AF" />
        <rect x="50" y="97" width="18" height="2" rx="1" fill="#9CA3AF" />
        {/* Checkmark */}
        <motion.path
          d="M52 106 L57 111 L68 100"
          stroke="#10B981"
          strokeWidth="3"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
          animate={{ pathLength: [0, 1], opacity: [0, 1] }}
          transition={{ duration: 0.8, repeat: Number.POSITIVE_INFINITY, repeatDelay: 2 }}
        />
      </motion.g>

      {/* Celebration sparkles */}
      <motion.g
        animate={{ opacity: [0, 1, 0], scale: [0.5, 1, 0.5] }}
        transition={{ duration: 1.5, repeat: Number.POSITIVE_INFINITY, staggerChildren: 0.2 }}
      >
        <circle cx="30" cy="40" r="3" fill="#FBBF24" />
        <circle cx="90" cy="35" r="2" fill="#F472B6" />
        <circle cx="25" cy="60" r="2" fill="#0D9488" />
        <circle cx="95" cy="55" r="3" fill="#60A5FA" />
      </motion.g>

      {/* Stars */}
      <motion.path
        d="M20 30 L22 35 L27 35 L23 38 L25 43 L20 40 L15 43 L17 38 L13 35 L18 35 Z"
        fill="#FBBF24"
        animate={{ rotate: [0, 360], scale: [0.8, 1, 0.8] }}
        transition={{ duration: 4, repeat: Number.POSITIVE_INFINITY }}
      />
      <motion.path
        d="M100 25 L101 28 L104 28 L102 30 L103 33 L100 31 L97 33 L98 30 L96 28 L99 28 Z"
        fill="#F472B6"
        animate={{ rotate: [0, -360], scale: [0.8, 1, 0.8] }}
        transition={{ duration: 3, repeat: Number.POSITIVE_INFINITY }}
      />
    </svg>
  )
}

const flowSteps: FlowStep[] = [
  {
    step: 1,
    title: "Scan Your Card",
    description: "Hold your health card to login",
    illustration: <ScanCardIllustration />,
  },
  {
    step: 2,
    title: "Talk to Assistant",
    description: "Tell us how you feel",
    illustration: <TalkAssistantIllustration />,
  },
  {
    step: 3,
    title: "Take a Photo",
    description: "Show us the problem area",
    illustration: <TakePhotoIllustration />,
  },
  {
    step: 4,
    title: "Get Your Report",
    description: "Receive guidance and next steps",
    illustration: <WaitReportIllustration />,
  },
]

export function DiagnosticFlow() {
  return (
    <div className="w-full max-w-5xl mx-auto px-2">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="text-center mb-3"
      >
        <h2 className="text-xl md:text-2xl font-bold text-foreground mb-1">How It Works</h2>
        <p className="text-base md:text-lg text-muted-foreground">Simple steps to get the care you need</p>
      </motion.div>

      <div className="grid grid-cols-4 gap-2 md:gap-4">
        {flowSteps.map((step, index) => (
          <motion.div
            key={step.step}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 + index * 0.1 }}
            className="relative"
          >
            {/* Connector line */}
            {index < flowSteps.length - 1 && (
              <div className="hidden md:block absolute top-12 left-[60%] w-[80%] h-0.5 bg-gradient-to-r from-primary/40 to-primary/20 rounded-full" />
            )}

            <div className="bg-card rounded-xl md:rounded-2xl p-2 md:p-3 border-2 border-border hover:border-primary/50 transition-colors shadow-sm">
              {/* Step number badge - smaller */}
              <div className="absolute -top-2 -left-1 w-7 h-7 md:w-8 md:h-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold text-sm md:text-base shadow-md">
                {step.step}
              </div>

              <div className="w-full aspect-square mb-2 rounded-lg md:rounded-xl bg-accent/30 p-1 overflow-hidden">
                {step.illustration}
              </div>

              <h3 className="text-sm md:text-base font-bold text-foreground text-center mb-0.5 leading-tight">
                {step.title}
              </h3>
              <p className="text-xs md:text-sm text-muted-foreground text-center leading-tight hidden md:block">
                {step.description}
              </p>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
