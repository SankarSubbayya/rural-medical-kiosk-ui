"use client"

import { motion } from "framer-motion"
import { MessageCircle, Heart, LogOut } from "lucide-react"
import { Button } from "@/components/ui/button"
import type { KioskScreen } from "@/app/page"

interface KioskNavigationProps {
  currentScreen: KioskScreen
  onNavigate: (screen: KioskScreen) => void
  onLogout: () => void
}

export function KioskNavigation({ currentScreen, onNavigate, onLogout }: KioskNavigationProps) {
  const navItems = [
    {
      id: "consultation" as const,
      label: "Talk",
      icon: MessageCircle,
    },
    {
      id: "health" as const,
      label: "My Health",
      icon: Heart,
    },
  ]

  return (
    <nav className="flex-shrink-0 bg-card border-t-2 border-border p-2 safe-area-inset-bottom">
      <div className="flex items-center justify-around gap-2 max-w-lg mx-auto">
        {navItems.map((item) => {
          const isActive = currentScreen === item.id
          const Icon = item.icon
          return (
            <motion.button
              key={item.id}
              whileTap={{ scale: 0.95 }}
              onClick={() => onNavigate(item.id)}
              className={`flex-1 flex flex-col items-center gap-0.5 py-2 px-3 rounded-xl transition-colors ${
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-secondary-foreground hover:bg-accent"
              }`}
            >
              <Icon className="w-6 h-6" />
              <span className="text-base font-semibold">{item.label}</span>
            </motion.button>
          )
        })}

        {/* Logout button */}
        <Button
          variant="ghost"
          onClick={onLogout}
          className="flex flex-col items-center gap-0.5 py-2 px-3 h-auto rounded-xl text-destructive hover:bg-destructive/10"
        >
          <LogOut className="w-6 h-6" />
          <span className="text-base font-semibold">Exit</span>
        </Button>
      </div>
    </nav>
  )
}
