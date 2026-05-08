"""
Output Guardrail
Checks system outputs for safety violations.
"""

from typing import Dict, Any, List
import re


class OutputGuardrail:
    """
    Guardrail for checking output safety.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize output guardrail.

        Args:
            config: Configuration dictionary
        """
        self.config = config

    def validate(self, response: str, sources: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate output response.

        Args:
            response: Generated response to validate
            sources: Optional list of sources used

        Returns:
            Validation result
        """
        violations = []

        pii_violations = self._check_pii(response)
        violations.extend(pii_violations)

        harmful_violations = self._check_harmful_content(response)
        violations.extend(harmful_violations)

        citation_violations = self._check_citation_support(response)
        violations.extend(citation_violations)

        certainty_violations = self._check_overconfident_claims(response)
        violations.extend(certainty_violations)

        bias_violations = self._check_bias(response)
        violations.extend(bias_violations)

        if sources:
            consistency_violations = self._check_factual_consistency(response, sources)
            violations.extend(consistency_violations)

        severe_violation = any(v.get("severity") == "high" for v in violations)
        sanitized_output = self._sanitize(response, violations) if violations else response

        return {
            "valid": not severe_violation,
            "violations": violations,
            "sanitized_output": sanitized_output,
            "action": "refuse" if severe_violation else "sanitize" if sanitized_output != response else "allow_with_warnings" if violations else "allow"
        }

    def _check_pii(self, text: str) -> List[Dict[str, Any]]:
        """
        Check for personally identifiable information.
        """
        violations = []

        patterns = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            "phone": r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "api_key": r"\b(?:sk-|pk-|api[_-]?key)[A-Za-z0-9_\-]{12,}\b",
        }

        for pii_type, pattern in patterns.items():
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            if matches:
                violations.append({
                    "validator": "pii",
                    "category": "privacy_or_pii_leakage",
                    "pii_type": pii_type,
                    "reason": f"Output contains possible {pii_type}.",
                    "severity": "high" if pii_type in ["ssn", "api_key"] else "medium",
                    "matches": matches
                })

        return violations

    def _check_harmful_content(self, text: str) -> List[Dict[str, Any]]:
        """
        Check for harmful or inappropriate content in the output.
        """
        violations = []
        lowered = text.lower()

        harmful_patterns = [
            "manipulate users",
            "trick users",
            "deceive users",
            "steal data",
            "bypass consent",
            "phishing",
            "spy on users",
            "collect passwords",
            "extract private data",
            "dark pattern to force"
        ]

        for pattern in harmful_patterns:
            if pattern in lowered:
                violations.append({
                    "validator": "harmful_content",
                    "category": "harmful_or_manipulative_agent_design",
                    "reason": f"Output may contain harmful agent design guidance: {pattern}",
                    "severity": "high"
                })

        return violations

    def _check_citation_support(self, text: str) -> List[Dict[str, Any]]:
        """
        Warn when a long research-style answer does not include visible citations or sources.
        """
        violations = []
        lowered = text.lower()

        citation_markers = ["source", "sources", "references", "http", "doi", "paper", "study", "["]
        has_citation_marker = any(marker in lowered for marker in citation_markers)

        if len(text) > 800 and not has_citation_marker:
            violations.append({
                "validator": "citation_support",
                "category": "misinformation_or_unsupported_claims",
                "reason": "Long research response does not show clear citation or source markers.",
                "severity": "medium"
            })

        return violations

    def _check_overconfident_claims(self, text: str) -> List[Dict[str, Any]]:
        """
        Warn when the answer uses overly absolute language that may overstate evidence.
        """
        violations = []
        lowered = text.lower()

        overconfident_phrases = [
            "guarantees",
            "proves that",
            "no risk",
            "completely safe",
            "everyone agrees",
            "always works",
            "never fails"
        ]

        matches = [phrase for phrase in overconfident_phrases if phrase in lowered]

        if matches:
            violations.append({
                "validator": "overconfident_claims",
                "category": "misinformation_or_unsupported_claims",
                "reason": f"Response may overstate certainty: {', '.join(matches)}",
                "severity": "low"
            })

        return violations

    def _check_factual_consistency(
        self,
        response: str,
        sources: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Lightweight factual consistency check.

        This implementation does not perform full claim verification.
        It flags a warning when sources are expected but the response does not
        visibly connect claims to evidence.
        """
        violations = []

        if sources and len(response) > 800:
            lowered = response.lower()
            if "source" not in lowered and "references" not in lowered and "[" not in lowered:
                violations.append({
                    "validator": "factual_consistency",
                    "category": "misinformation_or_unsupported_claims",
                    "reason": "Response may not clearly ground claims in the provided sources.",
                    "severity": "medium"
                })

        return violations

    def _check_bias(self, text: str) -> List[Dict[str, Any]]:
        """
        Check for biased or discriminatory language.
        """
        violations = []
        lowered = text.lower()

        biased_patterns = [
            "all users are",
            "everyone should",
            "no user will",
            "users are too"
        ]

        for pattern in biased_patterns:
            if pattern in lowered:
                violations.append({
                    "validator": "bias",
                    "category": "misinformation_or_unsupported_claims",
                    "reason": f"Output may contain overgeneralized user assumptions: {pattern}",
                    "severity": "low"
                })

        return violations

    def _sanitize(self, text: str, violations: List[Dict[str, Any]]) -> str:
        """
        Sanitize text by removing or redacting violations.
        """
        sanitized = text

        for violation in violations:
            if violation.get("validator") == "pii":
                for match in violation.get("matches", []):
                    sanitized = sanitized.replace(match, "[REDACTED]")

        return sanitized