"use client"

import { useState } from "react"
import { WelcomeScreen } from "@/components/kiosk/welcome-screen"
import { ConsultationScreen } from "@/components/kiosk/consultation-screen"
import { HealthPassportScreen } from "@/components/kiosk/health-passport-screen"
import { KioskNavigation } from "@/components/kiosk/kiosk-navigation"

export type KioskScreen = "welcome" | "consultation" | "health"

export interface UserSession {
  phoneNumber: string
  name: string
}

export default function MedicalKiosk() {
  const [currentScreen, setCurrentScreen] = useState<KioskScreen>("welcome")
  const [userSession, setUserSession] = useState<UserSession | null>(null)

  const handleLogin = (session: UserSession) => {
    setUserSession(session)
    setCurrentScreen("consultation")
  }

  const handleLogout = () => {
    setUserSession(null)
    setCurrentScreen("welcome")
  }

  return (
    <div className="h-screen bg-background flex flex-col overflow-hidden">
      {currentScreen === "welcome" ? (
        <WelcomeScreen onLogin={handleLogin} />
      ) : (
        <>
          <main className="flex-1 min-h-0 overflow-hidden">
            {currentScreen === "consultation" && <ConsultationScreen userName={userSession?.name || "Friend"} />}
            {currentScreen === "health" && <HealthPassportScreen userName={userSession?.name || "Friend"} />}
          </main>
          <KioskNavigation currentScreen={currentScreen} onNavigate={setCurrentScreen} onLogout={handleLogout} />
        </>
      )}
    </div>
  )
}
