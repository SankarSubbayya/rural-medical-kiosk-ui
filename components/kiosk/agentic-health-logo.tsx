"use client"

import { motion } from "framer-motion"

interface AgenticHealthLogoProps {
  size?: "sm" | "md" | "lg"
  showText?: boolean
  animated?: boolean
}

export function AgenticHealthLogo({ size = "md", showText = true, animated = true }: AgenticHealthLogoProps) {
  const sizes = {
    sm: { icon: 40, text: "text-lg" },
    md: { icon: 64, text: "text-2xl" },
    lg: { icon: 96, text: "text-4xl" },
  }

  const currentSize = sizes[size]

  return (
    <div className="flex items-center gap-3">
      {/* Logo Icon */}
      <motion.div
        initial={animated ? { scale: 0.8, opacity: 0 } : false}
        animate={animated ? { scale: 1, opacity: 1 } : false}
        className="relative"
        style={{ width: currentSize.icon, height: currentSize.icon }}
      >
        <svg viewBox="0 0 100 100" className="w-full h-full" aria-label="Agentic Health Logo">
          {/* Background circle with gradient */}
          <defs>
            <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#0D9488" />
              <stop offset="100%" stopColor="#14B8A6" />
            </linearGradient>
            <linearGradient id="pulseGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#FBBF24" />
              <stop offset="100%" stopColor="#F59E0B" />
            </linearGradient>
          </defs>

          {/* Main circle background */}
          <circle cx="50" cy="50" r="46" fill="url(#logoGradient)" />

          {/* Inner decorative ring */}
          <circle cx="50" cy="50" r="38" fill="none" stroke="white" strokeWidth="1.5" strokeOpacity="0.3" />

          {/* Stylized "A" for Agentic - formed by health cross and person */}
          {/* Central cross - health symbol */}
          <rect x="44" y="28" width="12" height="32" rx="2" fill="white" />
          <rect x="34" y="38" width="32" height="12" rx="2" fill="white" />

          {/* Person silhouette integrated into design */}
          <motion.g
            animate={animated ? { y: [0, -2, 0] } : {}}
            transition={{ duration: 3, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
          >
            {/* Head */}
            <circle cx="50" cy="22" r="8" fill="url(#pulseGradient)" />

            {/* Connectivity dots - representing "agentic" AI connections */}
            <motion.circle
              cx="28"
              cy="50"
              r="4"
              fill="#FBBF24"
              animate={animated ? { opacity: [0.5, 1, 0.5], scale: [0.8, 1, 0.8] } : {}}
              transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, delay: 0 }}
            />
            <motion.circle
              cx="72"
              cy="50"
              r="4"
              fill="#FBBF24"
              animate={animated ? { opacity: [0.5, 1, 0.5], scale: [0.8, 1, 0.8] } : {}}
              transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, delay: 0.5 }}
            />
            <motion.circle
              cx="50"
              cy="74"
              r="4"
              fill="#FBBF24"
              animate={animated ? { opacity: [0.5, 1, 0.5], scale: [0.8, 1, 0.8] } : {}}
              transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, delay: 1 }}
            />
          </motion.g>

          {/* Connection lines from center to dots */}
          <motion.line
            x1="40"
            y1="44"
            x2="32"
            y2="50"
            stroke="#FBBF24"
            strokeWidth="2"
            strokeLinecap="round"
            animate={animated ? { opacity: [0.3, 0.8, 0.3] } : {}}
            transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY }}
          />
          <motion.line
            x1="60"
            y1="44"
            x2="68"
            y2="50"
            stroke="#FBBF24"
            strokeWidth="2"
            strokeLinecap="round"
            animate={animated ? { opacity: [0.3, 0.8, 0.3] } : {}}
            transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, delay: 0.5 }}
          />
          <motion.line
            x1="50"
            y1="60"
            x2="50"
            y2="70"
            stroke="#FBBF24"
            strokeWidth="2"
            strokeLinecap="round"
            animate={animated ? { opacity: [0.3, 0.8, 0.3] } : {}}
            transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, delay: 1 }}
          />

          {/* Pulse ring animation */}
          {animated && (
            <motion.circle
              cx="50"
              cy="50"
              r="46"
              fill="none"
              stroke="#14B8A6"
              strokeWidth="2"
              initial={{ scale: 1, opacity: 0.6 }}
              animate={{ scale: 1.15, opacity: 0 }}
              transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, ease: "easeOut" }}
            />
          )}
        </svg>
      </motion.div>

      {/* Text */}
      {showText && (
        <motion.div
          initial={animated ? { opacity: 0, x: -10 } : false}
          animate={animated ? { opacity: 1, x: 0 } : false}
          transition={{ delay: 0.2 }}
          className="flex flex-col"
        >
          <span className={`${currentSize.text} font-bold text-foreground leading-tight`}>Agentic</span>
          <span className={`${currentSize.text} font-bold text-primary leading-tight`}>Health</span>
        </motion.div>
      )}
    </div>
  )
}
