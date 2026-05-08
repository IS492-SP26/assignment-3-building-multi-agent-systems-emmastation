"""
Input Guardrail
Checks user inputs for safety violations.
"""

from typing import Dict, Any, List


class InputGuardrail:
    """
    Guardrail for checking input safety.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize input guardrail.

        Args:
            config: Configuration dictionary
        """
        self.config = config

        self.min_query_length = config.get("min_query_length", 5)
        self.max_query_length = config.get("max_query_length", 2000)

        self.allowed_topic_keywords = [
            "hci", "human-ai", "human ai", "ux", "user experience",
            "agent", "agentic", "multi-agent", "interface", "design",
            "transparency", "trust", "citation", "evidence", "uncertainty",
            "explainability", "safety", "guardrail", "refusal", "tool use",
            "planning", "workflow", "usability"
        ]

    def validate(self, query: str) -> Dict[str, Any]:
        """
        Validate input query.

        Args:
            query: User input to validate

        Returns:
            Validation result
        """
        violations = []
        sanitized_input = query.strip()

        if len(sanitized_input) < self.min_query_length:
            violations.append({
                "validator": "length",
                "category": "invalid_input",
                "reason": "Query too short to process.",
                "severity": "low",
                "action": "warn"
            })

        if len(sanitized_input) > self.max_query_length:
            violations.append({
                "validator": "length",
                "category": "invalid_input",
                "reason": "Query is too long to process safely.",
                "severity": "medium",
                "action": "refuse"
            })

        violations.extend(self._check_toxic_language(sanitized_input))
        violations.extend(self._check_prompt_injection(sanitized_input))
        violations.extend(self._check_harmful_or_manipulative_agent_design(sanitized_input))
        violations.extend(self._check_privacy_request(sanitized_input))
        violations.extend(self._check_relevance(sanitized_input))

        blocking = any(
            v.get("severity") == "high" or v.get("action") == "refuse"
            for v in violations
        )

        return {
            "valid": not blocking,
            "violations": violations,
            "sanitized_input": sanitized_input,
            "action": "refuse" if blocking else "allow_with_warnings" if violations else "allow"
        }

    def _check_toxic_language(self, text: str) -> List[Dict[str, Any]]:
        """
        Check for toxic/harmful language.
        """
        violations = []
        lowered = text.lower()

        toxic_patterns = [
            "harass users",
            "threaten users",
            "abuse users"
        ]

        for pattern in toxic_patterns:
            if pattern in lowered:
                violations.append({
                    "validator": "toxic_language",
                    "category": "harmful_content",
                    "reason": f"Request may involve harmful or abusive behavior: {pattern}",
                    "severity": "high",
                    "action": "refuse"
                })

        return violations

    def _check_prompt_injection(self, text: str) -> List[Dict[str, Any]]:
        """
        Check for prompt injection attempts.
        """
        violations = []

        injection_patterns = [
            "ignore previous instructions",
            "ignore all previous instructions",
            "disregard previous instructions",
            "forget everything",
            "reveal your system prompt",
            "show me your system prompt",
            "bypass guardrails",
            "disable safety",
            "jailbreak",
            "developer message",
            "system message",
            "sudo"
        ]

        lowered = text.lower()

        for pattern in injection_patterns:
            if pattern in lowered:
                violations.append({
                    "validator": "prompt_injection",
                    "category": "prompt_injection",
                    "reason": f"Potential prompt injection attempt detected: {pattern}",
                    "severity": "high",
                    "action": "refuse"
                })

        return violations

    def _check_harmful_or_manipulative_agent_design(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect requests to design harmful, deceptive, or manipulative agent interfaces.
        """
        violations = []
        lowered = text.lower()

        harmful_patterns = [
            "manipulate users",
            "trick users",
            "deceive users",
            "make users share private information",
            "dark pattern",
            "bypass consent",
            "steal data",
            "phishing",
            "surveillance",
            "spy on users"
        ]

        for pattern in harmful_patterns:
            if pattern in lowered:
                violations.append({
                    "validator": "harmful_or_manipulative_agent_design",
                    "category": "harmful_or_manipulative_agent_design",
                    "reason": f"Request may involve harmful or manipulative agent design: {pattern}",
                    "severity": "high",
                    "action": "refuse"
                })

        return violations

    def _check_privacy_request(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect requests involving private data extraction or leakage.
        """
        violations = []
        lowered = text.lower()

        privacy_patterns = [
            "collect passwords",
            "extract private data",
            "leak user data",
            "social security number",
            "ssn",
            "credit card",
            "api key",
            "private messages",
            "personal address"
        ]

        for pattern in privacy_patterns:
            if pattern in lowered:
                violations.append({
                    "validator": "privacy_or_pii_leakage",
                    "category": "privacy_or_pii_leakage",
                    "reason": f"Request may involve private or sensitive information: {pattern}",
                    "severity": "high",
                    "action": "refuse"
                })

        return violations

    def _check_relevance(self, query: str) -> List[Dict[str, Any]]:
        """
        Check if query is relevant to AgentUX-MAS.
        """
        violations = []
        lowered = query.lower()

        if not any(keyword in lowered for keyword in self.allowed_topic_keywords):
            violations.append({
                "validator": "topic_relevance",
                "category": "off_topic_queries",
                "reason": "Query may be outside the system scope of agentic UX, HCI, or human-AI interaction research.",
                "severity": "low",
                "action": "warn"
            })

        return violations