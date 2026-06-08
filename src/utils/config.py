"""
TRIDENT-AI Configuration Loader.

Loads all environment variables from .env using python-dotenv.
This is the SINGLE SOURCE OF TRUTH for all configuration.
No other module should ever read os.environ directly — import from here.

Usage:
    from src.utils.config import settings
    print(settings.SPLUNK_HOST)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

# ─── Load .env file ─────────────────────────────────────────────────────────
# Walk up from this file to find .env at project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"
load_dotenv(_ENV_PATH, override=True)


class TridentSettings(BaseSettings):
    """
    All TRIDENT-AI configuration variables.

    Loaded from .env file via python-dotenv, validated with pydantic.
    Every field has a sensible default where applicable.
    Credentials have no defaults — they must be provided.
    """

    # ─── Splunk Cloud ────────────────────────────────────────────────────
    SPLUNK_HOST: str = Field(..., description="Splunk Cloud instance hostname")
    SPLUNK_PORT: int = Field(default=8089, description="Splunk management port")
    SPLUNK_TOKEN: Optional[str] = Field(default=None, description="Splunk Bearer token")
    SPLUNK_USERNAME: Optional[str] = Field(default=None, description="Splunk username (fallback)")
    SPLUNK_PASSWORD: Optional[str] = Field(default=None, description="Splunk password (fallback)")
    SPLUNK_INDEX: str = Field(default="main", description="Default Splunk index")
    SPLUNK_APP: str = Field(default="trident_ai", description="Splunk app context")
    SPLUNK_VERIFY_SSL: bool = Field(default=True, description="Verify SSL certificates")

    # ─── Splunk MCP Server ───────────────────────────────────────────────
    MCP_BASE_URL: str = Field(
        default="",
        description="Base URL for MCP Server JSON-RPC endpoint",
    )
    MCP_PROTOCOL: str = Field(default="sse", description="MCP transport protocol")

    # ─── CDTSM (Cisco Deep Time Series Model) ───────────────────────────
    CDTSM_MODEL_NAME: str = Field(default="cisco_ai_assistant")
    CDTSM_FORECAST_K: int = Field(default=24, ge=1, le=384)
    CDTSM_HOLDBACK: int = Field(default=12, ge=0, le=384)
    CDTSM_QUANTILE_LOWER: float = Field(default=0.20, ge=0.0, le=1.0)
    CDTSM_QUANTILE_UPPER: float = Field(default=0.80, ge=0.0, le=1.0)
    CDTSM_MAX_DATAPOINTS: int = Field(default=30000, ge=1)
    CDTSM_METRICS_INDEX: str = Field(default="metrics")
    CDTSM_METRICS_SOURCETYPE: str = Field(default="aws:cloudwatch")

    # ─── Foundation AI Security Model ────────────────────────────────────
    FOUNDATION_AI_MODEL: str = Field(default="foundation-sec-1.1-8b-instruct")
    SECURITY_LOGS_INDEX: str = Field(default="main")
    SECURITY_SOURCETYPE: str = Field(default="access_combined")

    # ─── AWS Bedrock ─────────────────────────────────────────────────────
    AWS_ACCESS_KEY_ID: Optional[str] = Field(default=None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(default=None)
    AWS_REGION: str = Field(default="us-east-1")
    AWS_BEARER_TOKEN_BEDROCK: Optional[str] = Field(default=None)
    BEDROCK_MODEL_ID: str = Field(default="anthropic.claude-sonnet-4-5")
    BEDROCK_MAX_TOKENS: int = Field(default=4096, ge=256, le=8192)

    # ─── Autonomous Loop ─────────────────────────────────────────────────
    POLL_INTERVAL_SECONDS: int = Field(default=60, ge=10)
    ANOMALY_COOLDOWN_SECONDS: int = Field(default=300, ge=30)
    ANOMALY_DEVIATION_THRESHOLD: float = Field(default=1.5, gt=0.0)
    MAX_INCIDENTS_IN_QUEUE: int = Field(default=100, ge=1)

    # ─── Demo Mode ───────────────────────────────────────────────────────
    DEMO_MODE: bool = Field(default=False)
    DEMO_DATA_PATH: str = Field(default="./demo/sample_data/")

    # ─── Logging ─────────────────────────────────────────────────────────
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")

    @field_validator("CDTSM_HOLDBACK")
    @classmethod
    def validate_cdtsm_limits(cls, v: int, info) -> int:
        """Enforce CDTSM hard limit: holdback + forecast_k <= 384."""
        # Note: cross-field validation happens at model level
        return v

    @field_validator("MCP_BASE_URL", mode="before")
    @classmethod
    def build_mcp_url(cls, v: str, info) -> str:
        """Auto-build MCP URL from SPLUNK_HOST if not provided."""
        if v:
            return v
        host = os.getenv("SPLUNK_HOST", "")
        port = os.getenv("SPLUNK_PORT", "8089")
        if host:
            return f"https://{host}:{port}/services/mcp"
        return ""

    def model_post_init(self, __context) -> None:
        """Post-init validation for cross-field constraints."""
        total = self.CDTSM_HOLDBACK + self.CDTSM_FORECAST_K
        if total > 384:
            raise ValueError(
                f"CDTSM hard limit exceeded: holdback({self.CDTSM_HOLDBACK}) + "
                f"forecast_k({self.CDTSM_FORECAST_K}) = {total} > 384"
            )

    @property
    def has_splunk_token(self) -> bool:
        """Check if Splunk token authentication is available."""
        return bool(self.SPLUNK_TOKEN)

    @property
    def has_splunk_credentials(self) -> bool:
        """Check if Splunk username/password authentication is available."""
        return bool(self.SPLUNK_USERNAME and self.SPLUNK_PASSWORD)

    @property
    def has_aws_iam_credentials(self) -> bool:
        """Check if standard AWS IAM credentials are available."""
        return bool(self.AWS_ACCESS_KEY_ID and self.AWS_SECRET_ACCESS_KEY)

    @property
    def has_aws_bearer_token(self) -> bool:
        """Check if AWS Bedrock bearer token is available."""
        return bool(self.AWS_BEARER_TOKEN_BEDROCK)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# ─── Singleton settings instance ─────────────────────────────────────────
settings = TridentSettings()
