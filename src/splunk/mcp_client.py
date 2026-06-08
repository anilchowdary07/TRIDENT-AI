"""
TRIDENT-AI MCP Server JSON-RPC 2.0 Client.

Communicates with the Splunk MCP Server (App ID 7931) via JSON-RPC 2.0 over HTTP.
All agent coordination flows through this client.

Every request and response is logged for the MCP Security Audit Trail.
Every response is validated for security violations (path traversal, SQLi,
prompt injection).

Usage:
    from src.splunk.mcp_client import MCPClient
    client = MCPClient()
    tools = await client.list_tools()
    result = await client.call_tool("search", {"query": "index=main | head 5"})
"""

from __future__ import annotations

import json
import re
import uuid
from typing import Any, Optional

import httpx

from src.utils.config import settings
from src.utils.logger import get_logger

log = get_logger(__name__)

# ─── Constants ───────────────────────────────────────────────────────────
REQUEST_TIMEOUT = 30.0  # seconds
MAX_RETRIES = 3
BASE_RETRY_DELAY = 1.0

# ─── Security patterns to detect in responses ───────────────────────────
PATH_TRAVERSAL_PATTERNS = [
    r"\.\./",
    r"\.\.\\",
    r"%2e%2e%2f",
    r"%2e%2e/",
    r"\.\.%2f",
]

SQL_INJECTION_PATTERNS = [
    r"(?i)union\s+select",
    r"(?i)drop\s+table",
    r"(?i);\s*delete\s+from",
    r"(?i);\s*insert\s+into",
    r"(?i);\s*update\s+.*\s+set",
    r"(?i)or\s+1\s*=\s*1",
    r"(?i)'\s*or\s+'",
]

PROMPT_INJECTION_PATTERNS = [
    r"<\|endoftext\|>",
    r"<\|system\|>",
    r"<\|user\|>",
    r"<\|assistant\|>",
    r"ignore previous instructions",
    r"ignore all previous",
    r"disregard your instructions",
]


class SecurityViolationError(Exception):
    """Raised when a security violation is detected in an MCP response."""
    pass


class MCPError(Exception):
    """Raised when an MCP JSON-RPC call fails."""
    pass


class MCPClient:
    """
    JSON-RPC 2.0 client for Splunk MCP Server.

    Implements the Model Context Protocol for tool discovery and invocation.
    All calls are logged for audit trail. All responses are security-validated.
    """

    def __init__(self) -> None:
        """Initialize the MCP client with configuration from settings."""
        self._base_url = settings.MCP_BASE_URL
        self._headers = self._build_headers()
        self._client: Optional[httpx.AsyncClient] = None
        log.info(
            "mcp_client_init",
            base_url=self._base_url,
            protocol=settings.MCP_PROTOCOL,
        )

    def _build_headers(self) -> dict[str, str]:
        """Build HTTP headers for MCP Server requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if settings.has_splunk_token:
            headers["Authorization"] = f"Bearer {settings.SPLUNK_TOKEN}"
        return headers

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers=self._headers,
                timeout=REQUEST_TIMEOUT,
                verify=settings.SPLUNK_VERIFY_SSL,
            )
        return self._client

    async def _send_rpc(
        self,
        method: str,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Send a JSON-RPC 2.0 request to the MCP Server.

        Args:
            method: The JSON-RPC method name.
            params: Optional parameters for the method.

        Returns:
            The result field from the JSON-RPC response.

        Raises:
            MCPError: If the RPC call returns an error.
            SecurityViolationError: If a security violation is detected.
        """
        request_id = str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params:
            payload["params"] = params

        # Log the full request for audit trail
        log.info(
            "mcp_request",
            rpc_id=request_id,
            method=method,
            params=params,
        )

        client = await self._get_client()
        last_error = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = await client.post("/", json=payload)
                response.raise_for_status()
                result = response.json()

                # Log the full response for audit trail
                log.info(
                    "mcp_response",
                    rpc_id=request_id,
                    method=method,
                    status_code=response.status_code,
                    has_error="error" in result,
                )

                # Security validation on response
                self._validate_security(result, request_id, method)

                # Check for JSON-RPC error
                if "error" in result:
                    error = result["error"]
                    log.error(
                        "mcp_rpc_error",
                        rpc_id=request_id,
                        error_code=error.get("code"),
                        error_message=error.get("message"),
                    )
                    raise MCPError(
                        f"MCP RPC error {error.get('code')}: {error.get('message')}"
                    )

                return result.get("result", {})

            except SecurityViolationError:
                raise  # Never retry on security violations
            except httpx.HTTPStatusError as e:
                last_error = e
                log.warning(
                    "mcp_http_error",
                    attempt=attempt,
                    status_code=e.response.status_code,
                    error=str(e),
                )
            except httpx.RequestError as e:
                last_error = e
                log.warning(
                    "mcp_request_error",
                    attempt=attempt,
                    error=str(e),
                )
            except MCPError:
                raise  # Don't retry on RPC-level errors

            if attempt < MAX_RETRIES:
                import asyncio
                delay = BASE_RETRY_DELAY * (2 ** (attempt - 1))
                await asyncio.sleep(delay)

        raise MCPError(f"MCP call failed after {MAX_RETRIES} retries: {last_error}")

    def _validate_security(
        self,
        response_data: dict[str, Any],
        request_id: str,
        method: str,
    ) -> None:
        """
        Validate MCP response for security violations.

        Checks for path traversal, SQL injection, and prompt injection patterns.

        Args:
            response_data: The full JSON-RPC response.
            request_id: The request ID for logging.
            method: The RPC method name.

        Raises:
            SecurityViolationError: If any violation is detected.
        """
        response_str = json.dumps(response_data)

        # Check path traversal
        for pattern in PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, response_str):
                log.critical(
                    "mcp_security_violation",
                    violation_type="path_traversal",
                    pattern=pattern,
                    rpc_id=request_id,
                    method=method,
                )
                raise SecurityViolationError(
                    f"Path traversal detected in MCP response: {pattern}"
                )

        # Check SQL injection
        for pattern in SQL_INJECTION_PATTERNS:
            if re.search(pattern, response_str):
                log.critical(
                    "mcp_security_violation",
                    violation_type="sql_injection",
                    pattern=pattern,
                    rpc_id=request_id,
                    method=method,
                )
                raise SecurityViolationError(
                    f"SQL injection pattern detected in MCP response: {pattern}"
                )

        # Check prompt injection
        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, response_str, re.IGNORECASE):
                log.critical(
                    "mcp_security_violation",
                    violation_type="prompt_injection",
                    pattern=pattern,
                    rpc_id=request_id,
                    method=method,
                )
                raise SecurityViolationError(
                    f"Prompt injection marker detected in MCP response: {pattern}"
                )

    # ─── Public MCP Methods ──────────────────────────────────────────────

    async def list_tools(self) -> dict[str, Any]:
        """
        List all available tools on the MCP Server.

        Returns:
            Dict containing tool definitions and metadata.
        """
        return await self._send_rpc("tools/list")

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Invoke a tool on the MCP Server.

        Args:
            tool_name: Name of the MCP tool to invoke.
            arguments: Arguments to pass to the tool.

        Returns:
            Tool execution result.
        """
        log.info(
            "mcp_tool_call",
            tool=tool_name,
            arguments=arguments,
        )
        return await self._send_rpc(
            "tools/call",
            {"name": tool_name, "arguments": arguments},
        )

    async def list_resources(self) -> dict[str, Any]:
        """
        List all available resources on the MCP Server.

        Returns:
            Dict containing resource definitions.
        """
        return await self._send_rpc("resources/list")

    async def read_resource(self, uri: str) -> dict[str, Any]:
        """
        Read a resource from the MCP Server.

        Args:
            uri: Resource URI to read.

        Returns:
            Resource content.
        """
        return await self._send_rpc("resources/read", {"uri": uri})

    async def close(self) -> None:
        """Close the HTTP client connection."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            log.info("mcp_client_closed")
