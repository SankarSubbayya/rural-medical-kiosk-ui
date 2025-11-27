# Agentic Health - Rural Medical AI Kiosk

A highly intuitive, empathetic UI for a rural medical AI kiosk designed to bridge the gap between advanced technology and low-tech literacy users.

## Features

- **Handshake (Login)**: QR code scanning or phone number entry with large dial pad
- **Consultation (Chat)**: Voice-first AI interaction with friendly avatar
- **Camera Capture**: Dermatology image capture for AI analysis
- **Health Passport**: Visual timeline of health records and next steps

---

## Files to Customize

### Core Services (Primary Integration Point)

| File | Purpose | What to Customize |
|------|---------|-------------------|
| `lib/kiosk-services.ts` | **All backend integrations** | Authentication, AI chat, voice recognition, image analysis, health records |

This is the **main file** you need to modify. It contains placeholder functions for:

- `authenticateWithQR()` - QR code authentication
- `authenticateWithPhone()` - Phone number + OTP authentication
- `startVoiceRecognition()` - Speech-to-text
- `sendMessageToAI()` - AI chat responses
- `speakText()` - Text-to-speech
- `captureAndAnalyzeImage()` - Dermatology image analysis
- `fetchHealthRecords()` - Patient health history
- `syncOfflineData()` - Offline data synchronization

---

### UI Components

#### Login Flow

| File | Purpose | Customization Options |
|------|---------|----------------------|
| `components/kiosk/welcome-screen.tsx` | Landing page with login options | Modify welcome text, add/remove login methods |
| `components/kiosk/dial-pad.tsx` | Phone number input | Change button sizes, colors, validation rules |
| `components/kiosk/diagnostic-flow.tsx` | 4-step visual guide | Update step descriptions, illustrations |

#### Consultation Flow

| File | Purpose | Customization Options |
|------|---------|----------------------|
| `components/kiosk/consultation-screen.tsx` | Main chat interface | Modify AI prompts, button labels, layout |
| `components/kiosk/ai-avatar.tsx` | Animated AI persona header | Change avatar appearance, status messages |
| `components/kiosk/camera-capture.tsx` | Photo capture modal | Adjust camera settings, upload limits |

#### Health Records

| File | Purpose | Customization Options |
|------|---------|----------------------|
| `components/kiosk/health-passport-screen.tsx` | Health timeline view | Customize event types, icons, colors |

#### Branding

| File | Purpose | Customization Options |
|------|---------|----------------------|
| `components/kiosk/agentic-health-logo.tsx` | Logo component | Replace with your brand logo |
| `components/kiosk/kiosk-navigation.tsx` | Bottom navigation bar | Add/remove tabs, change icons |

---

### Styling & Configuration

| File | Purpose | Customization Options |
|------|---------|----------------------|
| `app/globals.css` | Global styles & theme | Colors, fonts, design tokens |
| `app/layout.tsx` | Root layout & fonts | Change font family, metadata |
| `app/page.tsx` | Main app container | Modify screen flow, add new screens |

---

## Environment Variables

Add these to your `.env.local` file or Vercel project settings:

\`\`\`env
# Authentication (Supabase example)
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# AI Services (if not using Vercel AI Gateway)
OPENAI_API_KEY=your_openai_key

# Voice Services (optional - browser API works without this)
DEEPGRAM_API_KEY=your_deepgram_key

# Image Analysis (optional)
GOOGLE_CLOUD_VISION_KEY=your_vision_key
\`\`\`

---

## Quick Start Integration Guide

### Step 1: Authentication

Edit `lib/kiosk-services.ts` - `authenticateWithPhone()`:

\`\`\`typescript
export async function authenticateWithPhone(
  phoneNumber: string
): Promise<AuthResult> {
  // Replace with your auth provider
  const { data, error } = await supabase.auth.signInWithOtp({
    phone: phoneNumber,
  });
  
  return {
    success: !error,
    userId: data?.user?.id,
    sessionToken: data?.session?.access_token,
  };
}
\`\`\`

### Step 2: AI Chat

Edit `lib/kiosk-services.ts` - `sendMessageToAI()`:

\`\`\`typescript
export async function sendMessageToAI(
  message: string,
  conversationHistory: Message[]
): Promise<AIResponse> {
  // Using Vercel AI SDK
  const response = await generateText({
    model: 'openai/gpt-4o',
    messages: [
      { role: 'system', content: 'You are a helpful rural health assistant...' },
      ...conversationHistory,
      { role: 'user', content: message },
    ],
  });
  
  return {
    text: response.text,
    audioUrl: undefined, // Add TTS if needed
  };
}
\`\`\`

### Step 3: Health Records

Edit `lib/kiosk-services.ts` - `fetchHealthRecords()`:

\`\`\`typescript
export async function fetchHealthRecords(
  userId: string
): Promise<HealthRecord[]> {
  // Fetch from your database
  const { data } = await supabase
    .from('health_records')
    .select('*')
    .eq('user_id', userId)
    .order('date', { ascending: false });
  
  return data || [];
}
\`\`\`

---

## Database Schema (Suggested)

If using Supabase or PostgreSQL:

\`\`\`sql
-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  phone_number TEXT UNIQUE,
  qr_code_id TEXT UNIQUE,
  name TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Health records table
CREATE TABLE health_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  type TEXT, -- 'checkup', 'medication', 'test', 'vaccination'
  title TEXT,
  description TEXT,
  date DATE,
  status TEXT, -- 'completed', 'pending', 'upcoming'
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Consultation history
CREATE TABLE consultations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  messages JSONB,
  images TEXT[],
  ai_diagnosis TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
\`\`\`

---

## Folder Structure

\`\`\`
├── app/
│   ├── globals.css          # Theme & styling
│   ├── layout.tsx           # Root layout
│   └── page.tsx             # Main app entry
├── components/
│   └── kiosk/
│       ├── welcome-screen.tsx
│       ├── dial-pad.tsx
│       ├── diagnostic-flow.tsx
│       ├── consultation-screen.tsx
│       ├── ai-avatar.tsx
│       ├── camera-capture.tsx
│       ├── health-passport-screen.tsx
│       ├── agentic-health-logo.tsx
│       └── kiosk-navigation.tsx
├── lib/
│   └── kiosk-services.ts    # ** MAIN INTEGRATION FILE **
└── README.md
\`\`\`

---

## Design Principles

- **Minimum font size**: 20-24px for readability
- **High contrast**: Teal primary, cream background, amber accents
- **Large touch targets**: Minimum 48px, dial pad buttons 60-80px
- **Voice-first**: Microphone button is primary interaction
- **Visual feedback**: Animations for listening, speaking, processing states

---

## Support

For issues or questions, check:
- Vercel deployment logs
- Browser console for `[v0]` debug messages
- Network tab for API call failures
