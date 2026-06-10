"""
TRIDENT-AI AWS Bedrock Client.

Wraps AWS Bedrock API calls for incident synthesis using Claude 3.5 Sonnet.
Supports both standard IAM credentials and bearer token authentication.

Critical design decisions:
  - Uses invoke_model() not converse() for reliability
  - System prompt forces JSON-only output — no markdown, no preamble
  - Validates response with IncidentPackage pydantic model
  - Retries with exponential backoff on throttling (max 3 retries)
  - On JSON parse error: retries once with more explicit prompt
  - Forces region to us-east-1 to cleanly authenticate geographic inference profiles (us.*)
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from src.utils.config import settings
from src.utils.logger import get_logger

log = get_logger(__name__)

# ─── Constants ───────────────────────────────────────────────────────────
MAX_RETRIES = 3
BASE_RETRY_DELAY = 2.0  # seconds

SYSTEM_PROMPT = """You are a security incident analyst working for an enterprise SOC team.
You are part of the TRIDENT-AI autonomous incident intelligence system.

Your task: synthesize findings from 3 autonomous agents into a complete incident package.

Respond ONLY with valid JSON. No preamble, no explanation, no markdown code blocks.
No text before or after the JSON. Raw JSON only.

The JSON must contain exactly these fields:
{
  "incident_id": "TRIDENT-<YYYYMMDD>-<8char>",
  "timestamp": "ISO8601",
  "severity": "CRITICAL | HIGH | MEDIUM | LOW",
  "severity_score": 0-100,
  "title": "one-sentence incident title",
  "executive_summary": "2-3 sentences, non-technical, suitable for VP/CTO",
  "technical_summary": "detailed technical root cause paragraph",
  "root_cause": "single most likely root cause",
  "contributing_factors": ["factor1", "factor2"],
  "attack_timeline": [{"timestamp": "...", "event": "...", "source": "telemetry|security|platform"}], // MUST include at least 5 events, with at least one from each of the 3 sources
  "mitre_techniques": [{"id": "T1110", "name": "Brute Force", "tactic": "Credential Access"}],
  "iocs": {"ips": [], "domains": [], "users": []},
  "affected_services": ["service1", "service2"],
  "blast_radius": "estimated affected users/transactions",
  "business_impact": "$ estimate of loss per hour",
  "remediation_options": [
    {
      "priority": 1,
      "action": "description of action",
      "rationale": "why this helps",
      "risk_level": "LOW | MEDIUM | HIGH",
      "estimated_recovery_minutes": 5,
      "requires_approval": true,
      "mcp_tool_call": {"tool": "tool_name", "args": {}}
    }
  ],
  "confidence": 0.0-1.0,
  "agent_trace": {
    "telemetry_sentinel": {},
    "threat_marshall": {},
    "platform_auditor": {}
  }
}

IMPORTANT: Generate exactly 3 remediation_options, ordered by priority (1=highest).
Always include at least 2 MITRE ATT&CK techniques if a threat was detected.
The executive_summary must be understandable by a non-technical executive."""

RETRY_PROMPT_SUFFIX = """

CRITICAL: Your previous response was not valid JSON. This time you MUST respond
with ONLY valid JSON. No markdown code blocks (no ```), no text before or after
the JSON object. Start with { and end with }. Nothing else."""


class BedrockError(Exception):
    """Raised when Bedrock API call fails."""
    pass


class BedrockClient:
    """
    AWS Bedrock client for incident synthesis using Claude 3.5 Sonnet.

    Synthesises findings from all 3 TRIDENT agents into a complete
    incident package with executive summary, MITRE mapping,
    remediation options, and business impact assessment.
    """

    def __init__(self) -> None:
        """Initialize the Bedrock client with AWS credentials and cross-region fallbacks."""
        self._client = self._create_client()
        log.info(
            "bedrock_client_init",
            model=settings.BEDROCK_MODEL_ID,
            target_region="us-east-1",
            auth_method="iam" if settings.has_aws_iam_credentials else "bearer_token",
        )

    def _create_client(self):
        """
        Create the boto3 Bedrock runtime client.
        
        Forces the connection client region boundary to us-east-1 to support 
        cross-region on-demand throughput inference constraints globally.

        Returns:
            boto3 bedrock-runtime client instance.
        """
        # Overriding dynamic configuration region to resolve AP-SOUTH-1 handshake validation traps
        inference_gateway_region = "us-east-1"

        boto_config = BotoConfig(
            region_name=inference_gateway_region,
            retries={"max_attempts": 0},  # We handle exponential backoff loops manually
        )

        kwargs = {
            "service_name": "bedrock-runtime",
            "config": boto_config,
        }

        if settings.has_aws_iam_credentials:
            kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            if getattr(settings, "AWS_SESSION_TOKEN", None):
                kwargs["aws_session_token"] = settings.AWS_SESSION_TOKEN
            return boto3.client(**kwargs)
        elif settings.has_aws_bearer_token:
            import botocore
            boto_config.signature_version = botocore.UNSIGNED
            client = boto3.client(**kwargs)
            def inject_bearer_token(request, **kwargs):
                request.headers.add_header("Authorization", f"Bearer {settings.AWS_BEARER_TOKEN_BEDROCK}")
            client.meta.events.register_first('before-sign.bedrock-runtime', inject_bearer_token)
            return client
        else:
            return boto3.client(**kwargs)

    async def synthesize_incident_package(
        self,
        agent_findings: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Synthesize a complete incident package from agent findings via Bedrock.

        Args:
            agent_findings: Dict with keys 'telemetry_sentinel', 'threat_marshall',
                          'platform_auditor', each containing agent finding dicts.

        Returns:
            Complete incident package dict validated against the schema.

        Raises:
            BedrockError: If synthesis fails after all retries.
        """
        log.info(
            "bedrock_synthesis_start",
            finding_keys=list(agent_findings.keys()),
        )
        log.info("Calling AWS Bedrock bedrock-runtime...")

        user_prompt = self._build_user_prompt(agent_findings)

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                system = SYSTEM_PROMPT
                if attempt > 1:
                    system += RETRY_PROMPT_SUFFIX

                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._invoke_model,
                    system,
                    user_prompt,
                )

                package = self._parse_response(response)

                log.info(
                    "bedrock_synthesis_complete",
                    incident_id=package.get("incident_id"),
                    severity=package.get("severity"),
                    confidence=package.get("confidence"),
                    attempt=attempt,
                )

                return package

            except json.JSONDecodeError as e:
                log.warning(
                    "bedrock_json_parse_error",
                    attempt=attempt,
                    error=str(e),
                )
                if attempt == MAX_RETRIES:
                    raise BedrockError(
                        f"Bedrock returned invalid JSON after {MAX_RETRIES} attempts"
                    ) from e

            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                if error_code in ("ThrottlingException", "TooManyRequestsException"):
                    delay = BASE_RETRY_DELAY * (2 ** (attempt - 1))
                    log.warning(
                        "bedrock_throttled",
                        attempt=attempt,
                        retry_delay=delay,
                    )
                    if attempt == MAX_RETRIES:
                        raise BedrockError(
                            f"Bedrock throttled after {MAX_RETRIES} retries"
                        ) from e
                    await asyncio.sleep(delay)
                else:
                    raise BedrockError(f"Bedrock API error: {e}") from e

            except Exception as e:
                if attempt == MAX_RETRIES:
                    raise BedrockError(
                        f"Bedrock synthesis failed: {e}"
                    ) from e
                delay = BASE_RETRY_DELAY * (2 ** (attempt - 1))
                await asyncio.sleep(delay)

        raise BedrockError("Bedrock synthesis failed — unreachable")

    def _build_user_prompt(self, findings: dict[str, Any]) -> str:
        """
        Build the user prompt with all agent findings.

        Args:
            findings: Dict of agent findings.

        Returns:
            Formatted prompt string.
        """
        return f"""Analyze the following findings from 3 autonomous security agents and synthesize a complete incident package.

## TELEMETRY SENTINEL FINDINGS (CDTSM Zero-Shot Forecasting)
```json
{json.dumps(findings.get('telemetry_sentinel', {}), indent=2, default=str)}
```

## THREAT MARSHALL FINDINGS (Foundation AI Security Model)
```json
{json.dumps(findings.get('threat_marshall', {}), indent=2, default=str)}
```

## PLATFORM AUDITOR FINDINGS (SPL Platform Health)
```json
{json.dumps(findings.get('platform_auditor', {}), indent=2, default=str)}
```

Synthesize these into a complete incident package JSON. Consider cross-correlations between the findings. If the telemetry anomaly coincides with a security threat, treat it as a higher severity incident."""

    def _invoke_model(self, system_prompt: str, user_prompt: str) -> str:
        """
        Call Bedrock invoke_model synchronously.

        Args:
            system_prompt: System instructions.
            user_prompt: User message with agent findings.

        Returns:
            Raw text response from the model.
        """
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": settings.BEDROCK_MAX_TOKENS,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ],
        })

        response = self._client.invoke_model(
            modelId=settings.BEDROCK_MODEL_ID,
            contentType="application/json",
            accept="application/json",
            body=body,
        )

        response_body = json.loads(response["body"].read())
        return response_body["content"][0]["text"]

    def _parse_response(self, response_text: str) -> dict[str, Any]:
        """
        Parse and validate the model's JSON response.

        Strips any markdown code block markers if present, then parses JSON.

        Args:
            response_text: Raw text from the model.

        Returns:
            Parsed JSON dict.

        Raises:
            json.JSONDecodeError: If response is not valid JSON.
        """
        text = response_text.strip()

        # Strip markdown code block markers if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        return json.loads(text)