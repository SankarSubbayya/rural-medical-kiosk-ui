# Video Script: Agentic Health Demo

## Course Submission Video (3-5 minutes)

**Target Duration:** 4 minutes
**Bonus Points:** Tooling, Model Use, Deployment, Video (20 points total)

---

## SCENE 1: Introduction (30 seconds)

### [Screen: Title card with project name]

**NARRATION:**

> "Hi, I'm [Your Name], and this is Agentic Health — an AI-powered medical kiosk designed to bring dermatological healthcare to underserved rural communities in India.
>
> In rural India, there's only 1 doctor for every 10,000 people. Skin conditions affect 25% of the population, but most go undiagnosed because the nearest dermatologist is 50 kilometers away.
>
> Today, I'll show you how we're solving this problem using Google's Agent Development Kit and Gemini 2.0."

### [Action: Show the problem statistics briefly, then transition to the kiosk UI]

---

## SCENE 2: Architecture Overview (45 seconds)

### [Screen: Architecture diagram from PROJECT_WRITEUP.md]

**NARRATION:**

> "Let me walk you through our architecture. At the core is the **SOAP Orchestrator Agent** — powered by Google Gemini 2.0 Flash.
>
> SOAP stands for Subjective, Objective, Assessment, and Plan — it's the clinical framework doctors use for patient consultations.
>
> The agent has access to **seven custom MCP tools**:
> - **MedGemma** for medical image analysis
> - **SigLIP RAG** for finding similar cases in our vector database
> - **Safety tools** for content moderation
> - And more...
>
> All of this is tied together with **session state management** — the agent remembers the entire consultation, from symptoms to diagnosis."

### [Action: Point to each component in the diagram as you mention it]

---

## SCENE 3: Three Course Concepts (60 seconds)

### [Screen: Split view - code on left, UI on right]

**NARRATION:**

> "Let me highlight the **three key course concepts** we've implemented:
>
> **First: Agent Powered by LLM.**"

### [Show: soap_agent.py lines 163-174]

> "Here's our Gemini client initialization. The agent uses automatic function calling — Gemini autonomously decides which tools to invoke based on the conversation."

### [Show: soap_agent.py lines 399-408]

> "Notice how we pass all seven tools to the model. It decides when to extract symptoms, when to analyze images, and when to search for similar cases."

---

> "**Second: Custom MCP Tools.**"

### [Show: medgemma_tool.py]

> "Each tool follows the MCP pattern with a standard `run()` entry point. Here's our MedGemma tool — it takes a base64 image and returns structured predictions with confidence scores."

### [Show: siglip_rag_tool.py]

> "And here's our Visual RAG tool. It converts images to 768-dimensional embeddings using SigLIP, then searches Qdrant for similar dermatology cases from the Harvard SCIN dataset."

---

> "**Third: Sessions and Memory.**"

### [Show: ConsultationState dataclass in soap_agent.py lines 49-90]

> "The ConsultationState class tracks everything — the current SOAP stage, extracted symptoms, image analysis results, similar cases, and the full conversation history. This enables coherent, multi-turn consultations."

---

## SCENE 4: Live Demo (90 seconds)

### [Screen: Full kiosk UI]

**NARRATION:**

> "Now let's see it in action. I'll start a new consultation."

### [Action: Click to start consultation]

> "The agent greets me and asks how it can help."

### [Action: Type or speak: "I have a red rash on my arm that's been itchy for two weeks"]

> "Watch the console — you'll see the agent calling the **safety tool** to check the message, then the **symptom extraction tool** to identify 'red rash', 'itchy', 'two weeks', and 'arm'."

### [Show: Console output with function calls]

> "The agent is now in the SUBJECTIVE stage, gathering more information about my symptoms."

### [Action: Respond to follow-up questions]

> "Now it's asking me to show the affected area. Let me capture an image."

### [Action: Use camera capture or upload a test image]

> "Here's where the magic happens. Watch the console..."

### [Show: Console output]

> "The agent first calls **find_similar_cases** using SigLIP embeddings to search Qdrant. It found 3 similar cases from our database.
>
> Then it calls **analyze_image** with MedGemma, passing the enhanced clinical context that includes those similar cases.
>
> The result: **Eczema with 95% confidence**, followed by contact dermatitis at 80%."

### [Show: Agent response explaining the diagnosis in simple terms]

> "Notice how the agent explains this in simple, patient-friendly language — no medical jargon. It also mentions this is a routine condition, not an emergency."

---

## SCENE 5: Tooling & Model Highlights (30 seconds)

### [Screen: Terminal showing services]

**NARRATION:**

> "Let me quickly show our tooling stack:
>
> - **Qdrant** running on port 6333 with 10,000+ dermatology cases
> - **Ollama** serving MedGemma 4B for medical image analysis
> - **Google Gemini 2.0 Flash** as our agent's reasoning engine
> - **FastAPI** backend with WebSocket support
> - **Next.js 16** frontend with voice-first UI
>
> All of this can be deployed with a single `docker compose up` command."

### [Show: docker compose output or running containers]

---

## SCENE 6: Value & Impact (30 seconds)

### [Screen: Before/After comparison slide]

**NARRATION:**

> "The impact is significant:
>
> **Before**: Travel 50+ kilometers, wait 3-6 months for an appointment, struggle with English-only apps.
>
> **After**: Walk to local kiosk, get immediate consultation, speak in your native language, receive actionable care recommendations.
>
> Our voice-first, multilingual design means anyone can use it — regardless of literacy or technical expertise."

---

## SCENE 7: Conclusion (15 seconds)

### [Screen: Project summary with GitHub link]

**NARRATION:**

> "Agentic Health demonstrates how AI agents can transform healthcare delivery in underserved communities.
>
> By combining Gemini's reasoning capabilities with custom medical tools and persistent session state, we've created something that could genuinely save lives.
>
> Thank you for watching!"

### [Show: GitHub repo URL, documentation links]

---

## Video Production Checklist

### Pre-Recording Setup

- [ ] Backend running on `localhost:8000`
- [ ] Frontend running on `localhost:3000`
- [ ] Qdrant running on `localhost:6333`
- [ ] Ollama running with MedGemma loaded
- [ ] Console/terminal visible for showing function calls
- [ ] Test image ready for demo
- [ ] Screen recording software configured (OBS, Loom, etc.)

### Recording Tips

1. **Resolution**: 1920x1080 minimum
2. **Audio**: Use external microphone if possible
3. **Browser**: Chrome in incognito mode (clean UI)
4. **Font Size**: Increase terminal/code font to 16-18px for visibility
5. **Cursor**: Use a cursor highlighter tool

### Key Moments to Capture

| Timestamp | What to Show |
|-----------|--------------|
| 0:00 | Title card |
| 0:30 | Architecture diagram |
| 1:15 | Code: Gemini client initialization |
| 1:30 | Code: MCP tools |
| 1:45 | Code: ConsultationState |
| 2:00 | Live demo: Start consultation |
| 2:30 | Live demo: Symptom extraction |
| 3:00 | Live demo: Image capture & analysis |
| 3:30 | Console: Function calls visible |
| 3:45 | Tooling overview |
| 4:00 | Closing |

### Console Output to Highlight

```
[SOAP Agent - Gemini] Processing message in stage: SUBJECTIVE
[SOAP Agent - Gemini] Gemini called function: check_message_safety
[SOAP Agent - Gemini] Gemini called function: extract_symptoms
[SOAP Agent - Gemini] Functions called: ['check_message_safety', 'extract_symptoms']
[SOAP Agent - Gemini] Extracted symptoms: ['red rash', 'itchy', 'arm']

[SOAP Agent - Gemini] Processing message in stage: OBJECTIVE
[SOAP Agent - Gemini] Has image: True
[SOAP Agent - Gemini] Searching Qdrant for similar cases...
[SOAP Agent - Gemini] Found 3 similar cases from Qdrant
[SOAP Agent - Gemini] Gemini called function: analyze_image
[SOAP Agent - Gemini] Image analysis result: Success
[SOAP Agent - Gemini] Predictions: Eczema (95%), Contact dermatitis (80%)
```

---

## Slide Templates

### Slide 1: Title

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                     AGENTIC HEALTH                          │
│                                                             │
│         AI-Powered Medical Kiosk for Rural India            │
│                                                             │
│              Google ADK Capstone Project                    │
│                                                             │
│                     [Your Name]                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Slide 2: The Problem

```
┌─────────────────────────────────────────────────────────────┐
│                     THE PROBLEM                             │
│                                                             │
│   Rural India Healthcare Crisis:                            │
│                                                             │
│   • 1 doctor per 10,189 people (WHO recommends 1:1,000)    │
│   • 75% of healthcare infrastructure in urban areas        │
│   • 25% of rural population affected by skin conditions    │
│   • Average 50+ km travel to see a dermatologist           │
│   • 3-6 month wait times for specialist appointments       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Slide 3: Three Course Concepts

```
┌─────────────────────────────────────────────────────────────┐
│              THREE COURSE CONCEPTS                          │
│                                                             │
│   1. AGENT POWERED BY LLM                                   │
│      └── SOAP Orchestrator with Gemini 2.0 Flash           │
│                                                             │
│   2. CUSTOM MCP TOOLS                                       │
│      └── 7 specialized medical tools                        │
│                                                             │
│   3. SESSIONS & MEMORY                                      │
│      └── ConsultationState for persistent context           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Slide 4: Tech Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    TECH STACK                               │
│                                                             │
│   Agent:     Google Gemini 2.0 Flash (google-genai)        │
│   Vision:    MedGemma 4B via Ollama                        │
│   Embeddings: SigLIP (google/siglip-base-patch16-224)      │
│   Vector DB:  Qdrant (10,000+ SCIN cases)                  │
│   Backend:   FastAPI + Python 3.12                          │
│   Frontend:  Next.js 16 + TypeScript                        │
│   Speech:    Whisper STT + Google TTS                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Slide 5: Impact

```
┌─────────────────────────────────────────────────────────────┐
│                      IMPACT                                 │
│                                                             │
│   BEFORE                    AFTER                           │
│   ──────                    ─────                           │
│   Travel 50+ km       →     Walk to local kiosk            │
│   Wait 3-6 months     →     Immediate consultation         │
│   English-only apps   →     Voice in native language       │
│   Conditions worsen   →     Early detection & care         │
│                                                             │
│   90% lower cost than in-person consultations              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Alternative Short Version (2 minutes)

If you need a shorter video:

1. **0:00-0:15** - Quick intro + problem statement
2. **0:15-0:45** - Show the three concepts (code snippets only)
3. **0:45-1:45** - Live demo (abbreviated: one symptom → image → result)
4. **1:45-2:00** - Closing with impact statement

---

## Recording Software Recommendations

| Tool | Platform | Best For |
|------|----------|----------|
| OBS Studio | All | Full control, free |
| Loom | All | Quick recording + sharing |
| QuickTime | Mac | Simple screen recording |
| Camtasia | All | Professional editing |
| Screencastify | Chrome | Browser-based |

---

*Script prepared for Google Agent Development Kit Course Capstone Submission*
