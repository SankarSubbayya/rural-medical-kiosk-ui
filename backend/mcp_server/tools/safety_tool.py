"""
MCP Tool: Medical Safety Guardrails

Enforces "Do Not Play Doctor" rules and medical safety checks.
"""

from typing import Optional, Any, Dict, List
from app.services.safety_service import SafetyService

# Lazy-initialized service instance
_safety_service: Optional[SafetyService] = None


def _get_service() -> SafetyService:
    """Get or create service instance (lazy initialization)."""
    global _safety_service
    if _safety_service is None:
        _safety_service = SafetyService()
    return _safety_service


async def check_message_safety(message: str, language: str = "en") -> Dict[str, Any]:
    """Check if message violates safety guardrails."""
    try:
        # SafetyService.check_message_safety returns: (is_safe, flags, guidance)
        is_safe, flags, guidance = _get_service().check_message_safety(message)

        return {
            "success": True,
            "operation": "check_message",
            "is_safe": is_safe,
            "flags": [flag.value for flag in flags],  # Convert enum to string
            "redirect_response": guidance if not is_safe else None,
            "requires_escalation": not is_safe,
            "detected_emergency": any(flag.value == "EMERGENCY_SYMPTOMS" for flag in flags)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def check_condition_criticality(conditions: List[str]) -> Dict[str, Any]:
    """Check if any conditions are critical."""
    try:
        # SafetyService.check_condition_criticality returns: (has_critical, critical_list)
        has_critical, critical_list = _get_service().check_condition_criticality(conditions)

        return {
            "success": True,
            "operation": "check_critical",
            "is_critical": has_critical,  # Test compatibility
            "has_critical": has_critical,
            "critical_conditions": critical_list,
            "critical_findings": critical_list,  # Test compatibility
            "urgency_level": "urgent" if has_critical else "routine",
            "recommended_action": "Immediate referral to healthcare facility" if has_critical else "Continue consultation"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def run(operation: str, **kwargs) -> Dict[str, Any]:
    """
    Main MCP tool entry point for safety guardrails.

    Args:
        operation: One of "check_message", "check_critical"
        **kwargs: Operation-specific parameters

    Returns:
        Dict with operation result
    """
    try:
        if operation == "check_message":
            return await check_message_safety(
                message=kwargs["message"],
                language=kwargs.get("language", "en")
            )

        elif operation == "check_critical":
            return await check_condition_criticality(
                conditions=kwargs["conditions"]
            )

        else:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}"
            }

    except KeyError as e:
        return {
            "success": False,
            "error": f"Missing required parameter: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
