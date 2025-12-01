# YouTube Video Script: Agentic Health

## Google ADK Capstone Submission
**Duration:** Under 3 minutes
**Structure:** Problem → Why Agents → Architecture → Demo → The Build

---

## FULL SCRIPT (2:50)

---

### SECTION 1: PROBLEM STATEMENT (0:00 - 0:35)

**[VISUAL: Statistics on screen, rural India healthcare images]**

**SCRIPT:**

> "3.6 billion people worldwide lack access to essential healthcare. In rural India, this crisis is severe — there's only **one doctor for every 10,000 people**. The WHO recommends one per thousand.
>
> Skin diseases affect **25% of the rural population**, yet most go undiagnosed. Why? The nearest dermatologist is 50 kilometers away, wait times stretch to 6 months, and most health apps require English literacy that 35% of rural Indians don't have.
>
> Simple, treatable conditions like eczema become chronic because people can't access care in time.
>
> **This is the problem we're solving.**"

---

### SECTION 2: WHY AGENTS? (0:35 - 1:05)

**[VISUAL: Comparison chart - chatbots vs agents]**

**SCRIPT:**

> "Why agents? Traditional solutions fail here.
>
> **Rule-based systems** can't handle the variability of how people describe symptoms. **Simple chatbots** don't follow clinical protocols. **Static forms** don't adapt to patient responses.
>
> An **AI agent** is different. It can:
> - Conduct structured medical interviews following the **SOAP clinical framework**
> - **Autonomously decide** when to extract symptoms, request images, or search for similar cases
> - **Maintain context** across the entire consultation
> - Communicate in the **patient's own language**
>
> The agent isn't just answering questions — it's **orchestrating an entire clinical workflow** using specialized tools, exactly like a trained healthcare worker would."

---

### SECTION 3: ARCHITECTURE (1:05 - 1:35)

**[VISUAL: Architecture diagram - animate each component as mentioned]**

**SCRIPT:**

> "Here's our architecture.
>
> At the center is the **SOAP Orchestrator Agent**, powered by **Google Gemini 2.0 Flash**. SOAP stands for Subjective, Objective, Assessment, Plan — the standard clinical framework.
>
> The agent has access to **seven custom MCP tools**:
> - **MedGemma** analyzes dermatology images
> - **SigLIP RAG** searches our Qdrant vector database of 10,000 historical cases
> - **Safety tools** ensure appropriate responses
> - **Speech tools** enable voice interaction
>
> Everything is tied together with **session state management** — the `ConsultationState` class tracks symptoms, analysis results, similar cases, and conversation history throughout the consultation.
>
> The agent **autonomously decides** which tools to call based on the conversation context."

---

### SECTION 4: DEMO (1:35 - 2:25)

**[VISUAL: Screen recording of kiosk UI with console visible]**

**SCRIPT:**

> "Let me show you this in action.
>
> I start a consultation and say: 'I have a red rash on my arm that's been itchy for two weeks.'
>
> Watch the console — the agent calls the **safety tool** to check the message, then **extracts symptoms**: red rash, itchy, two weeks, arm.
>
> The agent asks follow-up questions, then requests an image of the affected area.
>
> **Now watch what happens when I upload an image.**
>
> First, the agent searches Qdrant using **SigLIP embeddings** — it finds 3 similar cases from our database.
>
> Then it calls **MedGemma** with enhanced clinical context that includes those similar cases.
>
> The result: **Eczema, 95% confidence**. Contact dermatitis, 80%.
>
> The agent explains this in **simple, patient-friendly language** — no medical jargon — and confirms it's a routine condition, not an emergency.
>
> All of this happened **autonomously**. The agent decided when to search for cases, when to analyze the image, and how to communicate the results."

---

### SECTION 5: THE BUILD (2:25 - 2:50)

**[VISUAL: Tech stack logos, code snippets]**

**SCRIPT:**

> "Here's how we built it:
>
> - **Google Gemini 2.0 Flash** as our agent's reasoning engine using the `google-genai` SDK
> - **MedGemma 4B** via Ollama for medical image analysis
> - **SigLIP embeddings** with **Qdrant** for visual case retrieval
> - **FastAPI** backend, **Next.js** frontend with voice-first UI
> - **Whisper** for speech-to-text, **Google TTS** for responses
>
> The entire system deploys with a single `docker compose up` command.
>
> **Agentic Health** shows how AI agents can transform healthcare delivery — bringing quality dermatological care to anyone, regardless of literacy, language, or location.
>
> Thank you for watching."

---

## TIMING BREAKDOWN

| Section | Duration | Cumulative |
|---------|----------|------------|
| Problem Statement | 35 sec | 0:35 |
| Why Agents | 30 sec | 1:05 |
| Architecture | 30 sec | 1:35 |
| Demo | 50 sec | 2:25 |
| The Build | 25 sec | 2:50 |

**Total: 2 minutes 50 seconds**

---

## VISUAL GUIDE

### Scene 1: Problem Statement (0:00-0:35)

**On Screen:**
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│              HEALTHCARE ACCESS CRISIS                       │
│                                                             │
│         Rural India: 1 doctor per 10,000 people            │
│                                                             │
│              ┌──────────────────────────────┐               │
│              │     WHO Recommends: 1:1,000  │               │
│              │     Reality: 1:10,189        │               │
│              │     Gap: 10x shortage        │               │
│              └──────────────────────────────┘               │
│                                                             │
│         25% affected by skin conditions                     │
│         50+ km to nearest dermatologist                     │
│         3-6 month wait times                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Scene 2: Why Agents? (0:35-1:05)

**On Screen:**
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│              WHY AGENTS?                                    │
│                                                             │
│   Traditional Solutions        vs      AI Agents            │
│   ─────────────────────              ──────────            │
│                                                             │
│   ❌ Rule-based systems              ✅ Adaptive reasoning  │
│      can't handle variability           handles any input   │
│                                                             │
│   ❌ Simple chatbots                 ✅ Clinical protocols   │
│      no medical structure               SOAP framework      │
│                                                             │
│   ❌ Static forms                    ✅ Context-aware        │
│      don't adapt                        multi-turn memory   │
│                                                             │
│   ❌ English-only                    ✅ Voice-first          │
│      excludes 35%                       any language        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Scene 3: Architecture (1:05-1:35)

**On Screen:**
```
┌─────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE                             │
│                                                             │
│                  ┌─────────────────────┐                    │
│                  │  SOAP Orchestrator  │                    │
│                  │   Gemini 2.0 Flash  │                    │
│                  └──────────┬──────────┘                    │
│                             │                               │
│           ┌─────────────────┼─────────────────┐             │
│           │                 │                 │             │
│           ▼                 ▼                 ▼             │
│   ┌───────────────┐ ┌───────────────┐ ┌───────────────┐    │
│   │   MedGemma    │ │  SigLIP RAG   │ │    Safety     │    │
│   │ Image Analysis│ │ Vector Search │ │   Guardrails  │    │
│   └───────────────┘ └───────────────┘ └───────────────┘    │
│                             │                               │
│                             ▼                               │
│                  ┌─────────────────────┐                    │
│                  │ ConsultationState   │                    │
│                  │ • symptoms          │                    │
│                  │ • analysis_results  │                    │
│                  │ • similar_cases     │                    │
│                  │ • message_history   │                    │
│                  └─────────────────────┘                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Scene 4: Demo (1:35-2:25)

**On Screen:** Live screen recording showing:
1. Kiosk UI with AI avatar
2. User typing symptom message
3. Console output showing function calls
4. Image upload interface
5. Qdrant search results in console
6. MedGemma analysis in console
7. Agent response with diagnosis

**Console Output to Capture:**
```
[SOAP Agent] Processing message in stage: SUBJECTIVE
[SOAP Agent] Gemini called function: check_message_safety ✓
[SOAP Agent] Gemini called function: extract_symptoms ✓
[SOAP Agent] Extracted: ['red rash', 'itchy', 'arm', '2 weeks']

[SOAP Agent] Processing message in stage: OBJECTIVE
[SOAP Agent] Has image: True
[SOAP Agent] Searching Qdrant for similar cases...
[SOAP Agent] Found 3 similar cases (similarity > 0.7)
[SOAP Agent] Gemini called function: analyze_image ✓
[SOAP Agent] Result: Eczema (95%), Contact dermatitis (80%)
```

### Scene 5: The Build (2:25-2:50)

**On Screen:**
```
┌─────────────────────────────────────────────────────────────┐
│                    THE BUILD                                │
│                                                             │
│   Agent Engine:    Google Gemini 2.0 Flash (google-genai)  │
│                                                             │
│   Medical Vision:  MedGemma 4B via Ollama                  │
│                                                             │
│   Vector Search:   SigLIP + Qdrant (10,000+ cases)         │
│                                                             │
│   Backend:         FastAPI + Python 3.12                    │
│                                                             │
│   Frontend:        Next.js 16 + Voice-First UI              │
│                                                             │
│   Speech:          Whisper STT + Google TTS                 │
│                                                             │
│   Deployment:      docker compose up                        │
│                                                             │
│              ─────────────────────────────                  │
│              github.com/your-org/agentic-health             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## RECORDING CHECKLIST

### Before Recording

- [ ] Backend running (`localhost:8000`)
- [ ] Frontend running (`localhost:3000`)
- [ ] Qdrant running (`localhost:6333`)
- [ ] Ollama running with MedGemma loaded
- [ ] Console visible in screen recording
- [ ] Test image ready for demo
- [ ] Slides/visuals prepared
- [ ] Script printed for reference

### Recording Setup

- [ ] Resolution: 1920x1080
- [ ] External microphone (if available)
- [ ] Quiet environment
- [ ] Browser in incognito (clean UI)
- [ ] Terminal font size increased (16-18px)
- [ ] Cursor highlighter enabled

### Post-Production

- [ ] Trim dead air
- [ ] Add transitions between sections
- [ ] Ensure audio is clear
- [ ] Add captions (accessibility)
- [ ] Verify total time < 3 minutes
- [ ] Export at 1080p minimum

---

## KEY MESSAGES TO EMPHASIZE

1. **Problem is real and significant** — 10x doctor shortage in rural India
2. **Agents are essential** — not just a chatbot, but autonomous clinical workflow
3. **Architecture is meaningful** — SOAP framework, MCP tools, session state
4. **Demo shows autonomous behavior** — agent decides which tools to call
5. **Built with Google ADK** — Gemini 2.0, production-ready stack

---

## COMMON MISTAKES TO AVOID

| ❌ Don't | ✅ Do |
|---------|------|
| Rush through the demo | Let key moments breathe |
| Use technical jargon | Explain in plain English |
| Skip showing console output | Highlight autonomous function calls |
| Forget to show the architecture | Visual diagram is essential |
| Go over 3 minutes | Rehearse and time yourself |

---

*Script prepared for Google Agent Development Kit Course Capstone YouTube Submission*
