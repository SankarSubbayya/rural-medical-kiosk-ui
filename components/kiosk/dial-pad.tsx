"use client"

import { motion } from "framer-motion"
import { Delete } from "lucide-react"

interface DialPadProps {
  value: string
  onChange: (value: string) => void
  maxLength?: number
}

export function DialPad({ value, onChange, maxLength = 10 }: DialPadProps) {
  const handlePress = (digit: string) => {
    if (value.length < maxLength) {
      onChange(value + digit)
    }
  }

  const handleDelete = () => {
    onChange(value.slice(0, -1))
  }

  const digits = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "", "0", "delete"]

  return (
    <div className="grid grid-cols-3 gap-2">
      {digits.map((digit, index) => {
        if (digit === "") {
          return <div key={`empty-${index}`} className="h-14 md:h-16" />
        }

        if (digit === "delete") {
          return (
            <motion.button
              key="delete"
              whileTap={{ scale: 0.95 }}
              onClick={handleDelete}
              className="h-14 md:h-16 rounded-xl bg-destructive/10 hover:bg-destructive/20 flex items-center justify-center transition-colors"
              aria-label="Delete"
            >
              <Delete className="w-7 h-7 md:w-8 md:h-8 text-destructive" />
            </motion.button>
          )
        }

        return (
          <motion.button
            key={digit}
            whileTap={{ scale: 0.95 }}
            onClick={() => handlePress(digit)}
            className="h-14 md:h-16 rounded-xl bg-secondary hover:bg-accent text-2xl md:text-3xl font-bold text-secondary-foreground transition-colors border-2 border-transparent hover:border-primary"
          >
            {digit}
          </motion.button>
        )
      })}
    </div>
  )
}
