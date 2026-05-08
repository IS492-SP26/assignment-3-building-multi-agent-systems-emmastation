"""
Safety Manager
Coordinates safety guardrails and logs safety events.
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import json

from src.guardrails.input_guardrail import InputGuardrail
from src.guardrails.output_guardrail import OutputGuardrail


class SafetyManager:
    """
    Manages safety guardrails for the multi-agent system.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize safety manager.

        Args:
            config: Safety configuration
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.log_events = config.get("log_events", True)
        self.logger = logging.getLogger("safety")

        self.safety_events: List[Dict[str, Any]] = []

        self.prohibited_categories = config.get("prohibited_categories", [
            "prompt_injection",
            "harmful_or_manipulative_agent_design",
            "privacy_or_pii_leakage",
            "misinformation_or_unsupported_claims",
            "off_topic_queries"
        ])

        self.on_violation = config.get("on_violation", {})
        self.input_guardrail = InputGuardrail(config)
        self.output_guardrail = OutputGuardrail(config)

        self.safety_log_file = (
            config.get("safety_log_file")
            or config.get("safety_log")
            or "logs/safety_events.log"
        )

    def check_input_safety(self, query: str) -> Dict[str, Any]:
        """
        Check if input query is safe to process.

        Args:
            query: User query to check

        Returns:
            Dictionary with safety status, violations, action, and sanitized query.
        """
        if not self.enabled:
            return {
                "safe": True,
                "query": query,
                "violations": [],
                "action": "allow"
            }

        validation = self.input_guardrail.validate(query)
        violations = validation.get("violations", [])
        action = validation.get("action", "allow")
        is_safe = validation.get("valid", True)

        if violations and self.log_events:
            self._log_safety_event("input", query, violations, is_safe)

        result = {
            "safe": is_safe,
            "query": validation.get("sanitized_input", query),
            "violations": violations,
            "action": action
        }

        if not is_safe:
            result["response"] = self.on_violation.get(
                "message",
                "I cannot process this request due to safety policies."
            )

        return result

    def check_output_safety(
        self,
        response: str,
        sources: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Check if output response is safe to return.

        Args:
            response: Generated response to check
            sources: Optional source metadata used by output validation

        Returns:
            Dictionary with safety status, violations, action, and sanitized response.
        """
        if not self.enabled:
            return {
                "safe": True,
                "response": response,
                "violations": [],
                "action": "allow"
            }

        validation = self.output_guardrail.validate(response, sources)
        violations = validation.get("violations", [])
        sanitized_output = validation.get("sanitized_output", response)
        action = validation.get("action", "allow")

        severe_violation = any(v.get("severity") == "high" for v in violations)
        is_safe = not severe_violation

        if violations and self.log_events:
            self._log_safety_event("output", response, violations, is_safe)

        if severe_violation:
            return {
                "safe": False,
                "violations": violations,
                "response": self.on_violation.get(
                    "message",
                    "I cannot provide this response due to safety policies."
                ),
                "action": "refuse"
            }

        if sanitized_output != response:
            return {
                "safe": True,
                "violations": violations,
                "response": sanitized_output,
                "action": "sanitize"
            }

        return {
            "safe": True,
            "violations": violations,
            "response": response,
            "action": action
        }

    def _sanitize_response(self, response: str, violations: List[Dict[str, Any]]) -> str:
        """
        Sanitize response by removing or redacting unsafe content.
        """
        sanitized = response

        for violation in violations:
            if violation.get("validator") == "pii":
                for match in violation.get("matches", []):
                    sanitized = sanitized.replace(match, "[REDACTED]")

        return sanitized

    def _log_safety_event(
        self,
        event_type: str,
        content: str,
        violations: List[Dict[str, Any]],
        is_safe: bool
    ):
        """
        Log a safety event.

        Args:
            event_type: "input" or "output"
            content: The content that was checked
            violations: List of violations found
            is_safe: Whether content passed safety checks
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "safe": is_safe,
            "violations": violations,
            "content_preview": content[:100] + "..." if len(content) > 100 else content
        }

        self.safety_events.append(event)
        self.logger.warning(f"Safety event: {event_type} - safe={is_safe}")

        if self.safety_log_file and self.log_events:
            try:
                import os
                os.makedirs(os.path.dirname(self.safety_log_file), exist_ok=True)

                with open(self.safety_log_file, "a") as f:
                    f.write(json.dumps(event) + "\n")
            except Exception as e:
                self.logger.error(f"Failed to write safety log: {e}")

    def get_safety_events(self) -> List[Dict[str, Any]]:
        """Get all logged safety events."""
        return self.safety_events

    def get_safety_stats(self) -> Dict[str, Any]:
        """
        Get statistics about safety events.

        Returns:
            Dictionary with safety statistics
        """
        total = len(self.safety_events)
        input_events = sum(1 for e in self.safety_events if e["type"] == "input")
        output_events = sum(1 for e in self.safety_events if e["type"] == "output")
        violations = sum(1 for e in self.safety_events if not e["safe"])

        return {
            "total_events": total,
            "input_checks": input_events,
            "output_checks": output_events,
            "violations": violations,
            "violation_rate": violations / total if total > 0 else 0
        }

    def clear_events(self):
        """Clear safety event log."""
        self.safety_events = []