#!/usr/bin/env python3
"""
TRIDENT-AI — Autonomous Incident Intelligence System.

Entry point. Starts the autonomous loop as a daemon thread and
keeps the main thread alive for graceful shutdown handling.

Usage:
    python main.py
    DEMO_MODE=true python main.py
"""

from __future__ import annotations

import signal
import sys
import time

from src.coordinator.autonomous_loop import AutonomousLoop
from src.utils.config import settings
from src.utils.logger import get_logger

log = get_logger(__name__)


def main() -> None:
    """
    Start the TRIDENT-AI autonomous coordinator.

    Initializes all components and starts the background polling loop.
    The main thread blocks until interrupted (Ctrl+C or SIGTERM).
    """
    log.info(
        "trident_ai_starting",
        version="1.0.0",
        demo_mode=settings.DEMO_MODE,
        poll_interval=settings.POLL_INTERVAL_SECONDS,
        splunk_host=settings.SPLUNK_HOST,
    )

    print(r"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   ████████╗██████╗ ██╗██████╗ ███████╗███╗   ██╗████████╗   ║
    ║   ╚══██╔══╝██╔══██╗██║██╔══██╗██╔════╝████╗  ██║╚══██╔══╝   ║
    ║      ██║   ██████╔╝██║██║  ██║█████╗  ██╔██╗ ██║   ██║      ║
    ║      ██║   ██╔══██╗██║██║  ██║██╔══╝  ██║╚██╗██║   ██║      ║
    ║      ██║   ██║  ██║██║██████╔╝███████╗██║ ╚████║   ██║      ║
    ║      ╚═╝   ╚═╝  ╚═╝╚═╝╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝      ║
    ║                                                              ║
    ║              AUTONOMOUS INCIDENT INTELLIGENCE                ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    mode = "🧪 DEMO MODE" if settings.DEMO_MODE else "🔴 LIVE MODE"
    print(f"    Mode: {mode}")
    print(f"    Splunk: {settings.SPLUNK_HOST}:{settings.SPLUNK_PORT}")
    print(f"    Poll interval: {settings.POLL_INTERVAL_SECONDS}s")
    print(f"    Bedrock model: {settings.BEDROCK_MODEL_ID}")
    print()

    # Initialize and start the autonomous loop
    loop = AutonomousLoop()

    # Handle graceful shutdown
    def signal_handler(signum, frame):
        """Handle shutdown signals."""
        sig_name = signal.Signals(signum).name
        log.info("shutdown_signal_received", signal=sig_name)
        print(f"\n    ⚡ Received {sig_name} — shutting down TRIDENT-AI...")
        loop.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start the autonomous loop
    loop.start()
    print("    ✅ Autonomous loop ACTIVE — agents are watching.")
    print("    Press Ctrl+C to stop.\n")

    # Keep main thread alive
    try:
        while loop.is_running:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("keyboard_interrupt")
        loop.stop()
        print("\n    TRIDENT-AI stopped. Stay vigilant. ⚡")


if __name__ == "__main__":
    main()
