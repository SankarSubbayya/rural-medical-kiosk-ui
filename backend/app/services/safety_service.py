"""
Safety Service - Medical safety guardrails and filtering.

Ensures the system adheres to the "Do Not Play Doctor" rule.
Handles critical condition detection and appropriate escalation.
"""
from typing import List, Tuple, Optional
from enum import Enum

from ..config import CRITICAL_CONDITIONS


class SafetyFlag(Enum):
    """Types of safety flags."""
    CRITICAL_CONDITION = "critical_condition"
    PRESCRIPTION_REQUEST = "prescription_request"
    DIAGNOSIS_REQUEST = "diagnosis_request"
    EMERGENCY_SYMPTOMS = "emergency_symptoms"
    SELF_HARM = "self_harm"
    UNSAFE_ADVICE = "unsafe_advice"


class SafetyService:
    """
    Safety guardrails for medical guidance system.

    Core Rule: DO NOT PLAY DOCTOR
    - Never diagnose
    - Never prescribe
    - Always recommend professional consultation
    - Flag critical conditions for immediate escalation
    """

    # Phrases that indicate requests for diagnosis
    DIAGNOSIS_PATTERNS = [
        "what do i have",
        "diagnose me",
        "tell me what this is",
        "is this cancer",
        "do i have",
        "am i sick",
        "what disease",
        "what condition do i have",
    ]

    # Phrases that indicate requests for prescriptions
    PRESCRIPTION_PATTERNS = [
        "what medicine should i take",
        "prescribe me",
        "what medication",
        "what drug should",
        "give me pills",
        "what cream should i use",
        "what antibiotic",
        "what steroid",
    ]

    # Emergency symptoms requiring immediate attention
    EMERGENCY_SYMPTOMS = [
        "can't breathe",
        "difficulty breathing",
        "chest pain",
        "spreading rapidly",
        "high fever",
        "swelling throat",
        "losing consciousness",
        "severe bleeding",
        "unbearable pain",
        "purple spots",
        "blisters everywhere",
    ]

    # Safe advice that CAN be given (general hygiene, not prescriptions)
    SAFE_ADVICE_PATTERNS = [
        "keep clean",
        "wash with soap",
        "don't scratch",
        "keep dry",
        "wear loose clothing",
        "avoid sun",
        "stay hydrated",
        "get rest",
        "cold compress",
        "warm compress",
    ]

    def __init__(self):
        self.critical_conditions = set(CRITICAL_CONDITIONS)

    def check_message_safety(self, message: str) -> Tuple[bool, List[SafetyFlag], str]:
        """
        Check if a user message triggers any safety flags.

        Args:
            message: The user's message

        Returns:
            Tuple of (is_safe, flags, response_guidance)
        """
        message_lower = message.lower()
        flags = []
        guidance = ""

        # Check for diagnosis requests
        for pattern in self.DIAGNOSIS_PATTERNS:
            if pattern in message_lower:
                flags.append(SafetyFlag.DIAGNOSIS_REQUEST)
                guidance = self._get_diagnosis_redirect()
                break

        # Check for prescription requests
        for pattern in self.PRESCRIPTION_PATTERNS:
            if pattern in message_lower:
                flags.append(SafetyFlag.PRESCRIPTION_REQUEST)
                guidance = self._get_prescription_redirect()
                break

        # Check for emergency symptoms
        for symptom in self.EMERGENCY_SYMPTOMS:
            if symptom in message_lower:
                flags.append(SafetyFlag.EMERGENCY_SYMPTOMS)
                guidance = self._get_emergency_response()
                break

        is_safe = len(flags) == 0
        return is_safe, flags, guidance

    def check_response_safety(self, response: str) -> Tuple[bool, List[str]]:
        """
        Check if an AI response is safe to send.

        Ensures the response doesn't:
        - Provide diagnoses
        - Prescribe medications
        - Give unsafe medical advice

        Args:
            response: The AI's proposed response

        Returns:
            Tuple of (is_safe, issues_found)
        """
        response_lower = response.lower()
        issues = []

        # Check for definitive diagnosis language
        diagnosis_phrases = [
            "you have",
            "this is definitely",
            "this is certainly",
            "i diagnose",
            "my diagnosis is",
            "you are suffering from",
        ]
        for phrase in diagnosis_phrases:
            if phrase in response_lower:
                issues.append(f"Contains definitive diagnosis language: '{phrase}'")

        # Check for prescription language
        prescription_phrases = [
            "take this medication",
            "use this drug",
            "apply this cream",
            "i prescribe",
            "you should take",
            "mg twice daily",
            "mg once daily",
        ]
        for phrase in prescription_phrases:
            if phrase in response_lower:
                issues.append(f"Contains prescription language: '{phrase}'")

        # Check for specific drug recommendations
        drug_names = [
            "ibuprofen", "aspirin", "tylenol", "acetaminophen",
            "hydrocortisone", "betamethasone", "clobetasol",
            "amoxicillin", "azithromycin", "ciprofloxacin",
            "fluconazole", "ketoconazole", "terbinafine",
        ]
        for drug in drug_names:
            if drug in response_lower:
                issues.append(f"Recommends specific medication: '{drug}'")

        is_safe = len(issues) == 0
        return is_safe, issues

    def check_condition_criticality(
        self,
        conditions: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Check if any detected conditions are critical.

        Args:
            conditions: List of condition names

        Returns:
            Tuple of (has_critical, critical_conditions)
        """
        critical_found = []

        for condition in conditions:
            condition_normalized = condition.lower().replace(" ", "_")

            for critical in self.critical_conditions:
                if critical in condition_normalized or condition_normalized in critical:
                    critical_found.append(condition)
                    break

        return len(critical_found) > 0, critical_found

    def sanitize_response(self, response: str) -> str:
        """
        Sanitize an AI response to ensure safety.

        Adds disclaimers and softens definitive language.
        """
        # Replace definitive language with possibilities
        replacements = [
            ("you have", "this may be"),
            ("this is definitely", "this appears to be"),
            ("this is certainly", "this looks like"),
            ("you are suffering from", "you may be experiencing"),
            ("i diagnose", "based on what you've shared, this could be"),
        ]

        sanitized = response
        for old, new in replacements:
            sanitized = sanitized.replace(old, new)
            sanitized = sanitized.replace(old.capitalize(), new.capitalize())

        # Ensure disclaimer is present
        disclaimer = "\n\nRemember: This is not a medical diagnosis. Please consult a healthcare professional for proper evaluation and treatment."

        if "not a medical diagnosis" not in sanitized.lower():
            sanitized += disclaimer

        return sanitized

    def _get_diagnosis_redirect(self) -> str:
        """Get response for diagnosis requests."""
        return """I understand you want to know what this is, but I'm not able to diagnose medical conditions - only a doctor can do that.

What I CAN do is:
1. Help gather information about your symptoms
2. Take photos to document your condition
3. Find similar cases in our medical database
4. Suggest what it MIGHT be (not a diagnosis)
5. Help you prepare to see a doctor

Would you like to continue describing your symptoms so I can help you prepare for a medical consultation?"""

    def _get_prescription_redirect(self) -> str:
        """Get response for prescription requests."""
        return """I'm not able to prescribe or recommend specific medications - that's something only a licensed doctor or pharmacist can do safely.

What I CAN suggest:
- General hygiene practices (keeping the area clean and dry)
- Over-the-counter basics like gentle soap
- When to seek medical attention

For specific treatment, please consult a healthcare provider who can examine you properly and prescribe the right medication.

Is there anything else I can help you with to prepare for your doctor visit?"""

    def _get_emergency_response(self) -> str:
        """Get response for emergency symptoms."""
        return """⚠️ The symptoms you're describing sound serious and may require immediate medical attention.

PLEASE DO NOT WAIT - Go to the nearest hospital or emergency room NOW.

If you're unable to get there yourself, call for emergency medical services or ask someone nearby to help you.

Your health and safety are the priority. We can continue this consultation after you've been seen by medical professionals."""

    def get_safe_advice(self, condition_type: str) -> List[str]:
        """
        Get safe, general advice that doesn't constitute medical prescription.

        Args:
            condition_type: General type of condition

        Returns:
            List of safe advice strings
        """
        general_advice = [
            "Keep the affected area clean",
            "Avoid scratching or picking at the area",
            "Wear loose, comfortable clothing",
            "Stay hydrated and get adequate rest",
        ]

        condition_specific = {
            "rash": [
                "Avoid known irritants and allergens",
                "A cool compress may help with discomfort",
                "Avoid hot showers or baths",
            ],
            "acne": [
                "Wash gently with mild soap twice daily",
                "Avoid touching your face frequently",
                "Change pillowcases regularly",
            ],
            "fungal": [
                "Keep the area dry and well-ventilated",
                "Do not share towels or personal items",
                "Wear breathable fabrics",
            ],
            "sunburn": [
                "Stay out of direct sunlight",
                "Keep the area moisturized",
                "Drink plenty of water",
            ],
            "insect_bite": [
                "Clean the area with soap and water",
                "A cold compress can reduce swelling",
                "Avoid scratching to prevent infection",
            ],
        }

        advice = general_advice.copy()
        if condition_type in condition_specific:
            advice.extend(condition_specific[condition_type])

        return advice


# Middleware for checking all AI responses
class SafetyMiddleware:
    """
    Middleware to check all outgoing responses for safety.
    """

    def __init__(self):
        self.safety_service = SafetyService()

    async def process_response(self, response: str) -> str:
        """
        Process a response through safety checks.

        Args:
            response: The AI's response

        Returns:
            Sanitized response
        """
        is_safe, issues = self.safety_service.check_response_safety(response)

        if not is_safe:
            # Log issues for review
            print(f"Safety issues found: {issues}")

            # Sanitize the response
            return self.safety_service.sanitize_response(response)

        return response
