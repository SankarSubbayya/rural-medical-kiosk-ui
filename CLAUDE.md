# Agentic Health - Rural Medical AI Kiosk

A Next.js 16 application providing an intuitive, voice-first UI for rural medical AI kiosks, designed for low-tech literacy users.

## Tech Stack

- **Framework**: Next.js 16 with App Router
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS 4 with `tw-animate-css`
- **UI Components**: Radix UI primitives + shadcn/ui pattern
- **Animation**: Framer Motion
- **Forms**: React Hook Form + Zod validation
- **Charts**: Recharts

## Project Structure

```
app/                    # Next.js App Router pages
├── page.tsx            # Main kiosk app entry
├── layout.tsx          # Root layout with fonts
└── globals.css         # Theme & CSS variables

components/
├── kiosk/              # Kiosk-specific components
│   ├── welcome-screen.tsx       # Landing with login options
│   ├── consultation-screen.tsx  # Voice-first AI chat
│   ├── camera-capture.tsx       # Dermatology image capture
│   ├── health-passport-screen.tsx # Health records timeline
│   ├── ai-avatar.tsx            # Animated AI persona
│   ├── diagnostic-flow.tsx      # Visual step guide
│   ├── kiosk-navigation.tsx     # Bottom nav bar
│   └── agentic-health-logo.tsx  # Brand logo
└── ui/                 # shadcn/ui components

lib/
├── kiosk-services.ts   # ** PRIMARY INTEGRATION FILE **
└── utils.ts            # Utility functions (cn helper)

hooks/                  # Custom React hooks
```

## Commands

```bash
pnpm dev      # Start development server
pnpm build    # Production build
pnpm start    # Start production server
pnpm lint     # Run ESLint
```

## Key Integration Points

The main file for backend integrations is `lib/kiosk-services.ts`. It contains placeholder functions for:

- `authenticateWithQR()` / `authenticateWithPhone()` - Authentication
- `startVoiceRecognition()` - Speech-to-text
- `sendMessageToAI()` - AI chat responses
- `speakText()` - Text-to-speech
- `captureAndAnalyzeImage()` - Image analysis
- `fetchHealthRecords()` - Patient health history

## Design System

- **Primary color**: Teal
- **Background**: Cream
- **Accents**: Amber
- **Min font size**: 20-24px for accessibility
- **Touch targets**: Min 48px, dial pad 60-80px
- **Voice-first**: Microphone button is primary interaction

## Path Aliases

- `@/*` maps to project root (e.g., `@/components/ui/button`)
