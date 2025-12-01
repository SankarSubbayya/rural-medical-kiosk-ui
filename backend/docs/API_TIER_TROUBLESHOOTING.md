# Gemini API Tier Troubleshooting

## Issue: Still Getting Free Tier Limits After Upgrade

### Symptoms
```
429 RESOURCE_EXHAUSTED
Quota exceeded for metric: generate_content_free_tier_requests
```

### Solutions

#### Solution 1: Generate New API Key (RECOMMENDED)

After upgrading to paid tier, you need to generate a NEW API key:

1. Go to https://aistudio.google.com/apikey
2. **Delete the old API key** (important!)
3. Click "Create API Key"
4. Select your **Cloud project** (not "Create in new project")
5. Copy the new key
6. Update `backend/.env`:
   ```env
   GOOGLE_API_KEY=your_new_key_here
   ```

**Why?** Old keys are tied to free tier. New keys inherit project billing settings.

#### Solution 2: Switch to Gemini 1.5 Flash

Use a more stable model while waiting for upgrade to propagate:

In `backend/agent/soap_agent.py` line 51:
```python
def __init__(
    self,
    model: str = "gemini-1.5-flash",  # Change this
    api_key: Optional[str] = None,
    ollama_host: str = "http://localhost:11434"
):
```

**Benefits**:
- More stable
- Better free tier quotas
- Same pricing
- Slightly slower but very reliable

#### Solution 3: Verify Billing Setup

1. Go to https://console.cloud.google.com/billing
2. Check if billing account is linked to your project
3. Verify "Generative Language API" is enabled
4. Check usage at https://ai.dev/usage

#### Solution 4: Wait for Propagation

Sometimes takes 5-60 minutes for:
- Billing to activate
- Quotas to update
- New limits to apply

**Test in meantime**:
```bash
# Wait 60 seconds between tests
cd backend
source .venv/bin/activate
python tests/test_agent_manual.py
```

## Quick Test

Run this to check your current tier:

```bash
cd backend
source .venv/bin/activate
python -c "
from dotenv import load_dotenv
load_dotenv()
import os
from google import genai

client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

# Try a simple call
try:
    response = client.models.generate_content(
        model='gemini-2.0-flash-exp',
        contents='Hi'
    )
    print('✅ API call successful!')
    print(f'Response: {response.text[:100]}')
    print('\\n🎉 You are on PAID tier!')
except Exception as e:
    if '429' in str(e):
        print('❌ Still on FREE tier')
        print('Action needed: Generate new API key')
    else:
        print(f'❌ Error: {e}')
"
```

## Alternative: Hybrid Mode (Ollama + Gemini)

If you want to use the system NOW without waiting:

### Option A: Use Ollama Only (No Gemini Needed)

Update router to use ChatService directly instead of Google ADK agent.

**Pros**: Works immediately, fully local, no API costs
**Cons**: No intelligent function calling, less sophisticated

### Option B: Fallback Pattern

Modify agent to fall back to Ollama on rate limit:

```python
# In soap_agent.py process_message()
try:
    response = self.client.models.generate_content(...)
except Exception as e:
    if '429' in str(e):
        # Fallback to Ollama
        return await self._fallback_to_ollama(message)
    raise
```

## Recommended Action Plan

**Immediate** (Do this now):
1. Go to Google AI Studio
2. Delete old API key
3. Create NEW API key in your BILLING-ENABLED project
4. Update `.env` with new key
5. Test again

**If still not working**:
1. Switch to `gemini-1.5-flash` model
2. Wait 30-60 minutes
3. Verify billing at console.cloud.google.com

**Long term**:
1. Implement fallback to Ollama
2. Add rate limit retry logic
3. Cache common responses

## Support

- **Billing**: https://console.cloud.google.com/billing
- **API Keys**: https://aistudio.google.com/apikey
- **Usage**: https://ai.dev/usage
- **Pricing**: https://ai.google.dev/pricing
- **Support**: https://support.google.com/
