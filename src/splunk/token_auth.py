"""
TRIDENT-AI Splunk Token Authentication.

Handles Splunk Cloud authentication with dual support:
  - Token-based auth (preferred, required for MCP Server)
  - Username/password session auth (fallback)

All auth state is managed here. No other module handles credentials.

Usage:
    from src.splunk.token_auth import SplunkAuth
    auth = SplunkAuth()
    headers = auth.get_auth_headers()
    service = auth.get_service()
"""

from __future__ import annotations

import ssl
from typing import Optional

import splunklib.client as splunk_client

from src.utils.config import settings
from src.utils.logger import get_logger

log = get_logger(__name__)


class SplunkAuthError(Exception):
    """Raised when Splunk authentication fails."""
    pass


class SplunkAuth:
    """
    Manages Splunk Cloud authentication.

    Supports both token-based and username/password authentication.
    Token auth is preferred as it is required for MCP Server access.
    """

    def __init__(self) -> None:
        """Initialize auth with credentials from config."""
        self._service: Optional[splunk_client.Service] = None
        self._session_key: Optional[str] = None
        log.info(
            "splunk_auth_init",
            host=settings.SPLUNK_HOST,
            port=settings.SPLUNK_PORT,
            has_token=settings.has_splunk_token,
            has_credentials=settings.has_splunk_credentials,
        )

    def get_auth_headers(self) -> dict[str, str]:
        """
        Get HTTP headers for authenticated Splunk API requests.

        Returns:
            Dict with Authorization header using token or session key.

        Raises:
            SplunkAuthError: If no valid authentication method is available.
        """
        if settings.has_splunk_token:
            return {
                "Authorization": f"Bearer {settings.SPLUNK_TOKEN}",
                "Content-Type": "application/json",
            }

        # Fall back to session-based auth
        if self._session_key:
            return {
                "Authorization": f"Splunk {self._session_key}",
                "Content-Type": "application/json",
            }

        # Try to create a session
        service = self.get_service()
        if service and hasattr(service, "token"):
            self._session_key = service.token
            return {
                "Authorization": f"Splunk {self._session_key}",
                "Content-Type": "application/json",
            }

        raise SplunkAuthError(
            "No valid Splunk authentication available. "
            "Provide SPLUNK_TOKEN or SPLUNK_USERNAME/SPLUNK_PASSWORD in .env"
        )

    def get_service(self) -> splunk_client.Service:
        """
        Get an authenticated Splunk SDK Service connection.

        Creates and caches the connection on first call.

        Returns:
            Connected splunklib.client.Service instance.

        Raises:
            SplunkAuthError: If connection cannot be established.
        """
        if self._service is not None:
            return self._service

        try:
            connect_kwargs = {
                "host": settings.SPLUNK_HOST,
                "port": settings.SPLUNK_PORT,
                "app": settings.SPLUNK_APP,
            }

            # SSL verification
            if not settings.SPLUNK_VERIFY_SSL:
                connect_kwargs["verify"] = False

            # Token auth (preferred)
            if settings.has_splunk_token:
                connect_kwargs["splunkToken"] = settings.SPLUNK_TOKEN
                log.info("splunk_connecting", method="token")
            elif settings.has_splunk_credentials:
                connect_kwargs["username"] = settings.SPLUNK_USERNAME
                connect_kwargs["password"] = settings.SPLUNK_PASSWORD
                log.info("splunk_connecting", method="username_password")
            else:
                raise SplunkAuthError(
                    "No Splunk credentials configured. Set SPLUNK_TOKEN or "
                    "SPLUNK_USERNAME/SPLUNK_PASSWORD in .env"
                )

            connect_kwargs["autologin"] = True
            connect_kwargs["timeout"] = 5

            self._service = splunk_client.connect(**connect_kwargs)
            log.info(
                "splunk_connected",
                host=settings.SPLUNK_HOST,
                app=settings.SPLUNK_APP,
            )
            return self._service

        except splunk_client.AuthenticationError as e:
            log.error("splunk_auth_failed", error=str(e))
            raise SplunkAuthError(f"Splunk authentication failed: {e}") from e
        except Exception as e:
            log.error("splunk_connection_failed", error=str(e))
            raise SplunkAuthError(f"Splunk connection failed: {e}") from e

    def validate_connection(self) -> bool:
        """
        Test the Splunk connection by fetching server info.

        Returns:
            True if connection is valid, False otherwise.
        """
        try:
            service = self.get_service()
            info = service.info
            log.info(
                "splunk_connection_validated",
                server_name=info.get("serverName", "unknown"),
                version=info.get("version", "unknown"),
            )
            return True
        except Exception as e:
            log.warning("splunk_connection_invalid", error=str(e))
            return False

    def refresh_session(self) -> None:
        """Force a new authentication session."""
        self._service = None
        self._session_key = None
        log.info("splunk_session_refreshed")
