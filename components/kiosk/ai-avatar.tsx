"use client"

import { motion } from "framer-motion"
import { Heart } from "lucide-react"

interface AiAvatarProps {
  isListening: boolean
  isSpeaking: boolean
}

export function AiAvatar({ isListening, isSpeaking }: AiAvatarProps) {
  return (
    <div className="flex items-center gap-4">
      <div className="relative">
        <motion.div
          animate={{
            scale: isSpeaking ? [1, 1.05, 1] : isListening ? [1, 1.02, 1] : 1,
          }}
          transition={{
            duration: isSpeaking ? 0.5 : 1,
            repeat: isSpeaking || isListening ? Number.POSITIVE_INFINITY : 0,
          }}
          className="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary via-primary/90 to-accent flex items-center justify-center shadow-lg overflow-hidden"
        >
          {/* Agentic Health Logo */}
          <div className="relative w-full h-full flex items-center justify-center">
            {/* Background pulse rings */}
            <motion.div
              className="absolute inset-0 rounded-2xl border-2 border-primary-foreground/20"
              animate={{
                scale: isSpeaking ? [1, 1.1, 1] : [1, 1.05, 1],
                opacity: [0.3, 0.1, 0.3],
              }}
              transition={{
                duration: 2,
                repeat: Number.POSITIVE_INFINITY,
              }}
            />

            {/* Central health cross */}
            <div className="relative z-10">
              {/* Horizontal bar */}
              <motion.div
                className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-3 bg-primary-foreground rounded-sm"
                animate={{
                  opacity: isSpeaking ? [1, 0.8, 1] : 1,
                }}
                transition={{
                  duration: 0.5,
                  repeat: isSpeaking ? Number.POSITIVE_INFINITY : 0,
                }}
              />
              {/* Vertical bar */}
              <motion.div
                className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-8 bg-primary-foreground rounded-sm"
                animate={{
                  opacity: isSpeaking ? [1, 0.8, 1] : 1,
                }}
                transition={{
                  duration: 0.5,
                  repeat: isSpeaking ? Number.POSITIVE_INFINITY : 0,
                }}
              />
            </div>

            {/* Agentic connection dots */}
            <motion.div
              className="absolute top-2 right-2 w-2 h-2 bg-amber-300 rounded-full"
              animate={{
                scale: [1, 1.3, 1],
                opacity: [0.7, 1, 0.7],
              }}
              transition={{
                duration: 1.5,
                repeat: Number.POSITIVE_INFINITY,
                delay: 0,
              }}
            />
            <motion.div
              className="absolute bottom-2 left-2 w-2 h-2 bg-amber-300 rounded-full"
              animate={{
                scale: [1, 1.3, 1],
                opacity: [0.7, 1, 0.7],
              }}
              transition={{
                duration: 1.5,
                repeat: Number.POSITIVE_INFINITY,
                delay: 0.5,
              }}
            />
            <motion.div
              className="absolute top-2 left-2 w-1.5 h-1.5 bg-primary-foreground/60 rounded-full"
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.5, 0.8, 0.5],
              }}
              transition={{
                duration: 1.5,
                repeat: Number.POSITIVE_INFINITY,
                delay: 0.25,
              }}
            />
            <motion.div
              className="absolute bottom-2 right-2 w-1.5 h-1.5 bg-primary-foreground/60 rounded-full"
              animate={{
                scale: [1, 1.2, 1],
                opacity: [0.5, 0.8, 0.5],
              }}
              transition={{
                duration: 1.5,
                repeat: Number.POSITIVE_INFINITY,
                delay: 0.75,
              }}
            />

            {/* Person silhouette arc at bottom */}
            <div className="absolute bottom-1 left-1/2 -translate-x-1/2">
              <div className="w-6 h-3 bg-primary-foreground/40 rounded-t-full" />
            </div>
          </div>
        </motion.div>

        {/* Status indicator */}
        <motion.div
          className={`absolute -bottom-1 -right-1 w-6 h-6 rounded-full flex items-center justify-center ${
            isListening ? "bg-destructive" : isSpeaking ? "bg-success" : "bg-primary"
          }`}
          animate={{ scale: isListening || isSpeaking ? [1, 1.2, 1] : 1 }}
          transition={{ duration: 0.5, repeat: isListening || isSpeaking ? Number.POSITIVE_INFINITY : 0 }}
        >
          <Heart className="w-3 h-3 text-primary-foreground" fill="currentColor" />
        </motion.div>
      </div>

      <div>
        <h2 className="text-2xl font-bold text-foreground">Agentic Health</h2>
        <p className="text-lg text-muted-foreground">
          {isListening ? "Listening to you..." : isSpeaking ? "Speaking..." : "Ready to help"}
        </p>
      </div>
    </div>
  )
}
