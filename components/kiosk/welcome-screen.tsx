"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { QrCode, Phone, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { DialPad } from "@/components/kiosk/dial-pad"
import { DiagnosticFlow } from "@/components/kiosk/diagnostic-flow"
import { AgenticHealthLogo } from "@/components/kiosk/agentic-health-logo"
import * as KioskServices from "@/lib/kiosk-services"
import type { UserSession } from "@/app/page"

interface WelcomeScreenProps {
  onLogin: (session: UserSession) => void
}

export function WelcomeScreen({ onLogin }: WelcomeScreenProps) {
  const [loginMethod, setLoginMethod] = useState<"choice" | "qr" | "phone">("choice")
  const [phoneNumber, setPhoneNumber] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const handlePhoneSubmit = async () => {
    if (phoneNumber.length >= 10) {
      setIsLoading(true)
      const result = await KioskServices.authenticateWithPhone(phoneNumber)
      setIsLoading(false)

      if (result.success) {
        onLogin({
          phoneNumber,
          name: result.name || "Patient",
        })
      }
    }
  }

  const handleQrScan = async () => {
    setIsLoading(true)
    const result = await KioskServices.authenticateWithQRCode()
    setIsLoading(false)

    if (result.success) {
      onLogin({
        phoneNumber: "1234567890",
        name: result.name || "Patient",
      })
    }
  }

  return (
    <div className="h-screen flex flex-col items-center justify-between p-4 md:p-6 bg-gradient-to-b from-background via-background to-accent/20 overflow-hidden">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center flex-shrink-0">
        <div className="flex items-center justify-center gap-2 mb-2">
          <AgenticHealthLogo size="md" showText={true} animated={true} />
        </div>
        <h1 className="text-3xl md:text-4xl font-bold text-foreground mb-1">Welcome</h1>
        <p className="text-lg md:text-xl text-muted-foreground">Your health companion is here to help</p>
      </motion.div>

      <div className="flex-1 flex items-center justify-center w-full max-w-lg py-2">
        <AnimatePresence mode="wait">
          {loginMethod === "choice" && (
            <motion.div
              key="choice"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full space-y-3"
            >
              <Button
                onClick={() => {
                  setLoginMethod("qr")
                  handleQrScan()
                }}
                className="w-full h-20 md:h-24 text-xl md:text-2xl font-semibold rounded-2xl bg-card border-2 border-border hover:border-primary hover:bg-accent text-card-foreground shadow-lg transition-all"
              >
                <QrCode className="w-8 h-8 mr-3 text-primary" />
                <span>Scan Your Card</span>
              </Button>

              <Button
                onClick={() => setLoginMethod("phone")}
                className="w-full h-20 md:h-24 text-xl md:text-2xl font-semibold rounded-2xl bg-card border-2 border-border hover:border-primary hover:bg-accent text-card-foreground shadow-lg transition-all"
              >
                <Phone className="w-8 h-8 mr-3 text-primary" />
                <span>Enter Phone Number</span>
              </Button>

              <p className="text-center text-lg text-muted-foreground mt-2">Choose how you want to sign in</p>
            </motion.div>
          )}

          {loginMethod === "qr" && (
            <motion.div
              key="qr"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full text-center"
            >
              <div className="bg-card rounded-2xl p-6 shadow-lg border-2 border-border">
                <div className="w-36 h-36 mx-auto bg-muted rounded-xl flex items-center justify-center mb-4 relative overflow-hidden">
                  <QrCode className="w-16 h-16 text-muted-foreground" />
                  <motion.div
                    className="absolute inset-0 bg-primary/20"
                    animate={{ y: ["100%", "-100%"] }}
                    transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY }}
                  />
                </div>
                <p className="text-xl font-semibold text-foreground mb-1">Hold your card to the scanner</p>
                <p className="text-lg text-muted-foreground">We will recognize you automatically</p>
              </div>

              <Button
                onClick={() => setLoginMethod("choice")}
                variant="ghost"
                className="mt-4 text-lg text-muted-foreground hover:text-foreground"
                disabled={isLoading}
              >
                ← Go back
              </Button>
            </motion.div>
          )}

          {loginMethod === "phone" && (
            <motion.div
              key="phone"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full"
            >
              <div className="bg-card rounded-2xl p-4 shadow-lg border-2 border-border">
                <div className="bg-muted rounded-xl p-3 mb-3 min-h-[60px] flex items-center justify-center">
                  <span className="text-3xl font-mono tracking-wider text-foreground">
                    {phoneNumber || "Enter your number"}
                  </span>
                </div>

                <DialPad value={phoneNumber} onChange={setPhoneNumber} maxLength={10} />

                <Button
                  onClick={handlePhoneSubmit}
                  disabled={phoneNumber.length < 10 || isLoading}
                  className="w-full h-16 mt-3 text-xl font-bold rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span>{isLoading ? "Please wait..." : "Continue"}</span>
                  {!isLoading && <ArrowRight className="w-6 h-6 ml-2" />}
                </Button>
              </div>

              <Button
                onClick={() => {
                  setLoginMethod("choice")
                  setPhoneNumber("")
                }}
                variant="ghost"
                className="w-full mt-3 text-lg text-muted-foreground hover:text-foreground"
                disabled={isLoading}
              >
                ← Go back
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {loginMethod === "choice" && (
        <div className="flex-shrink-0 w-full">
          <DiagnosticFlow />
        </div>
      )}
    </div>
  )
}
