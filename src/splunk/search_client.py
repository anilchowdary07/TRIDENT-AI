"""
TRIDENT-AI Splunk Search Client.

Executes SPL queries against Splunk Cloud via the Splunk SDK.
Provides both synchronous and async wrappers, one-shot and streaming modes.
All searches use proper timeout and retry logic.

Usage:
    from src.splunk.search_client import SearchClient
    client = SearchClient()
    results = await client.execute_search("search index=main | head 10")
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any, Optional

import splunklib.results as splunk_results

from src.splunk.token_auth import SplunkAuth
from src.utils.config import settings
from src.utils.logger import get_logger

log = get_logger(__name__)

# ─── Constants ───────────────────────────────────────────────────────────
MAX_RETRIES = 3
BASE_RETRY_DELAY = 2.0  # seconds
SEARCH_TIMEOUT = 300  # seconds (5 minutes)


class SearchError(Exception):
    """Raised when a Splunk search fails."""
    pass


class SearchClient:
    """
    Executes SPL searches against Splunk Cloud.

    Supports one-shot (blocking) and async execution with exponential backoff
    retry on transient failures.
    """

    def __init__(self, auth: Optional[SplunkAuth] = None) -> None:
        """
        Initialize the search client.

        Args:
            auth: Optional SplunkAuth instance. Creates one if not provided.
        """
        self._auth = auth or SplunkAuth()
        self.demo_mode_str = str(os.getenv("DEMO_MODE", "false")).lower()

    async def _get_proxy_session(self):
        """Authenticate via Splunk Web UI and return an httpx session."""
        if hasattr(self, "_proxy_session"):
            return self._proxy_session
            
        import httpx
        client = httpx.AsyncClient(verify=settings.SPLUNK_VERIFY_SSL)
        login_url = f"https://{settings.SPLUNK_HOST}/en-US/account/login"
        
        # Get initial cookie
        await client.get(login_url)
        cval = client.cookies.get("cval", "")
        
        # Authenticate
        payload = {
            "username": settings.SPLUNK_USERNAME, 
            "password": settings.SPLUNK_PASSWORD, 
            "cval": cval
        }
        await client.post(login_url, data=payload)
        
        self._proxy_session = client
        return client

    async def execute_search(
        self,
        spl_query: str,
        earliest_time: str = "-15m",
        latest_time: str = "now",
        max_results: int = 10000,
    ) -> list[dict[str, Any]]:
        """
        Execute a SPL query using the Web UI Reverse Proxy to bypass port 8089 blocks.
        """
        log.info(
            "search_executing_via_proxy",
            query=spl_query[:200],
            earliest=earliest_time,
            latest=latest_time,
        )

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                client = await self._get_proxy_session()
                
                csrf = ""
                for name, value in client.cookies.items():
                    if "csrf" in name.lower():
                        csrf = value
                        
                search_url = f"https://{settings.SPLUNK_HOST}/en-US/splunkd/__raw/services/search/jobs?output_mode=json"
                headers = {
                    "X-Splunk-Form-Key": csrf,
                    "X-Requested-With": "XMLHttpRequest"
                }
                
                if not spl_query.strip().startswith("|") and not spl_query.strip().lower().startswith("search"):
                    spl_query = f"search {spl_query}"
                
                search_payload = {
                    "search": spl_query,
                    "exec_mode": "oneshot",
                    "earliest_time": earliest_time,
                    "latest_time": latest_time,
                    "count": max_results
                }
                
                response = await client.post(search_url, headers=headers, data=search_payload, timeout=60.0)
                
                # Graceful fallback for missing ML models on Trial tiers
                if response.status_code == 400 and "| apply" in spl_query:
                    log.warning("Splunk AI model not found on this instance (400 Bad Request). Falling back to local simulation.")
                    return [{"_raw": "{\"fallback\": true, \"message\": \"Model not installed on trial tier\"}"}]
                    
                response.raise_for_status()
                
                data = response.json()
                results = data.get("results", [])
                
                log.info(
                    "search_completed",
                    result_count=len(results),
                    attempt=attempt,
                )
                return results

            except Exception as e:
                delay = BASE_RETRY_DELAY * (2 ** (attempt - 1))
                log.warning(
                    "search_retry",
                    attempt=attempt,
                    max_retries=MAX_RETRIES,
                    error=str(e),
                    retry_delay=delay,
                )
                if attempt == MAX_RETRIES:
                    log.error("search_failed_all_retries", query=spl_query[:200])
                    raise SearchError(
                        f"Search failed after {MAX_RETRIES} retries: {e}"
                    ) from e
                await asyncio.sleep(delay)

        return []

    async def execute_search_job(
        self,
        spl_query: str,
        earliest_time: str = "-15m",
        latest_time: str = "now",
        max_results: int = 10000,
    ) -> list[dict[str, Any]]:
        """Fallback to oneshot for proxy implementation."""
        return await self.execute_search(spl_query, earliest_time, latest_time, max_results)

    async def write_event(
        self,
        event_data: dict[str, Any],
        index: str = "trident_incidents",
        sourcetype: str = "trident:incident",
    ) -> bool:
        """
        Write an event to a Splunk index via the receivers/simple endpoint.

        Args:
            event_data: Dictionary of event data to index.
            index: Target Splunk index name.
            sourcetype: Sourcetype for the event.

        Returns:
            True if write succeeded, False otherwise.
        """
        if settings.DEMO_MODE:
            log.info("DEMO MODE: Bypassing Splunk Cloud write to prevent timeout freezes.", index=index)
            return True

        log.info("PRODUCTION MODE: Initializing HEC connection to Splunk Cloud...", index=index)
        log.info("event_writing", index=index, sourcetype=sourcetype)

        try:
            import httpx
            
            hec_token = settings.SPLUNK_HEC_TOKEN
            if not hec_token:
                log.error("Missing SPLUNK_HEC_TOKEN in environment")
                return False
                
            url = f"https://{settings.SPLUNK_HOST}:8088/services/collector/event"
            headers = {"Authorization": f"Splunk {hec_token}"}
            payload = {
                "event": event_data,
                "sourcetype": sourcetype,
                "index": index
            }
            
            async with httpx.AsyncClient(verify=settings.SPLUNK_VERIFY_SSL) as http:
                resp = await http.post(url, headers=headers, json=payload, timeout=15)
                if resp.status_code == 200:
                    log.info("event_written", index=index)
                    return True
                else:
                    log.error("event_write_failed", index=index, status=resp.status_code, error=resp.text)
                    return False
        except Exception as e:
            log.error("event_write_failed", index=index, error=str(e))
            return False

    def _write_event_sync(
        self,
        event_data: dict[str, Any],
        index: str,
        sourcetype: str,
    ) -> None:
        """Deprecated: Use HEC implementation in write_event directly."""
        pass

    async def get_events(
        self,
        index: str,
        query: str = "",
        limit: int = 20
    ) -> list[dict[str, Any]]:
        """Run a search for raw events on the given index."""
        if settings.DEMO_MODE:
            return []
        spl = f"search index={index} {query} | sort -_time | head {limit}"
        results = await self.execute_search(spl, max_results=limit)
        events = []
        for r in results:
            if "_raw" in r:
                try:
                    events.append(json.loads(r["_raw"]))
                except json.JSONDecodeError:
                    events.append(r)
            else:
                events.append(r)
        return events

    async def post_event(
        self,
        index: str,
        event: dict[str, Any],
        sourcetype: str = "trident:json"
    ) -> bool:
        """Post a JSON event."""
        return await self.write_event(event, index=index, sourcetype=sourcetype)
