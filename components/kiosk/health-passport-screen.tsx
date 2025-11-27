"use client"

import { motion } from "framer-motion"
import { Thermometer, Pill, Activity, Calendar, ChevronRight, AlertCircle, CheckCircle2 } from "lucide-react"
import { Card } from "@/components/ui/card"

interface HealthPassportScreenProps {
  userName: string
}

interface HealthEvent {
  id: string
  date: string
  type: "symptom" | "medication" | "checkup" | "action"
  title: string
  description: string
  icon: "thermometer" | "pill" | "activity" | "calendar"
  status?: "pending" | "completed"
}

const healthTimeline: HealthEvent[] = [
  {
    id: "1",
    date: "Today",
    type: "action",
    title: "Take Medicine",
    description: "Paracetamol 500mg - Morning dose",
    icon: "pill",
    status: "pending",
  },
  {
    id: "2",
    date: "Yesterday",
    type: "symptom",
    title: "Fever Recorded",
    description: "Temperature: 101°F (38.3°C)",
    icon: "thermometer",
  },
  {
    id: "3",
    date: "2 Days Ago",
    type: "checkup",
    title: "Health Checkup",
    description: "Blood pressure: 120/80 mmHg - Normal",
    icon: "activity",
  },
  {
    id: "4",
    date: "Last Week",
    type: "medication",
    title: "Prescription Started",
    description: "Antibiotics for 5 days - Completed",
    icon: "pill",
    status: "completed",
  },
  {
    id: "5",
    date: "2 Weeks Ago",
    type: "checkup",
    title: "Follow-up Visit",
    description: "Discussed ongoing symptoms",
    icon: "calendar",
    status: "completed",
  },
]

const iconMap = {
  thermometer: Thermometer,
  pill: Pill,
  activity: Activity,
  calendar: Calendar,
}

const typeColors = {
  symptom: "bg-destructive/10 text-destructive border-destructive/30",
  medication: "bg-primary/10 text-primary border-primary/30",
  checkup: "bg-success/10 text-success border-success/30",
  action: "bg-warning/10 text-warning border-warning/30",
}

export function HealthPassportScreen({ userName }: HealthPassportScreenProps) {
  const pendingActions = healthTimeline.filter((event) => event.status === "pending")

  return (
    <div className="h-full flex flex-col bg-background overflow-hidden">
      <div className="flex-shrink-0 bg-card border-b-2 border-border p-4">
        <h1 className="text-2xl md:text-3xl font-bold text-foreground">My Health</h1>
        <p className="text-lg text-muted-foreground">Your health journey at a glance</p>
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto p-3 space-y-4">
        {/* Action Items Section */}
        {pendingActions.length > 0 && (
          <section>
            <h2 className="text-xl font-bold text-foreground mb-3 flex items-center gap-2">
              <AlertCircle className="w-6 h-6 text-warning" />
              Next Steps
            </h2>
            <div className="space-y-2">
              {pendingActions.map((action) => {
                const IconComponent = iconMap[action.icon]
                return (
                  <motion.div key={action.id} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }}>
                    <Card className="p-4 bg-warning/5 border-2 border-warning/40 rounded-xl">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-warning/20 flex items-center justify-center flex-shrink-0">
                          <IconComponent className="w-6 h-6 text-warning" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-xl font-bold text-foreground">{action.title}</h3>
                          <p className="text-base text-muted-foreground">{action.description}</p>
                        </div>
                        <ChevronRight className="w-6 h-6 text-warning flex-shrink-0" />
                      </div>
                    </Card>
                  </motion.div>
                )
              })}
            </div>
          </section>
        )}

        {/* Timeline Section */}
        <section>
          <h2 className="text-xl font-bold text-foreground mb-3">Timeline of Health</h2>
          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-border rounded-full" />

            <div className="space-y-3">
              {healthTimeline.map((event, index) => {
                const IconComponent = iconMap[event.icon]
                return (
                  <motion.div
                    key={event.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="relative pl-14"
                  >
                    <div
                      className={`absolute left-3 w-7 h-7 rounded-full flex items-center justify-center border-4 border-background ${
                        event.status === "completed"
                          ? "bg-success"
                          : event.status === "pending"
                            ? "bg-warning"
                            : "bg-muted"
                      }`}
                    >
                      {event.status === "completed" ? (
                        <CheckCircle2 className="w-4 h-4 text-success-foreground" />
                      ) : (
                        <div className="w-1.5 h-1.5 rounded-full bg-foreground/50" />
                      )}
                    </div>

                    <Card className={`p-3 rounded-xl border-2 ${typeColors[event.type]}`}>
                      <div className="flex items-start gap-3">
                        <div
                          className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                            event.type === "symptom"
                              ? "bg-destructive/20"
                              : event.type === "medication"
                                ? "bg-primary/20"
                                : event.type === "action"
                                  ? "bg-warning/20"
                                  : "bg-success/20"
                          }`}
                        >
                          <IconComponent
                            className={`w-5 h-5 ${
                              event.type === "symptom"
                                ? "text-destructive"
                                : event.type === "medication"
                                  ? "text-primary"
                                  : event.type === "action"
                                    ? "text-warning"
                                    : "text-success"
                            }`}
                          />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2 mb-0.5">
                            <h3 className="text-lg font-bold text-foreground">{event.title}</h3>
                            <span className="text-sm text-muted-foreground flex-shrink-0">{event.date}</span>
                          </div>
                          <p className="text-base text-muted-foreground">{event.description}</p>
                        </div>
                      </div>
                    </Card>
                  </motion.div>
                )
              })}
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
