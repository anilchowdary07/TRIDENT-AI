"""
MITRE ATT&CK Technique Lookup Table.

Provides a comprehensive mapping of MITRE ATT&CK technique IDs (T-codes) to
their human-readable names and associated tactics. Used by the Threat Marshall
agent and the incident package builder to enrich findings with ATT&CK context.

Usage:
    from src.utils.mitre import lookup_technique, get_tactic_chain
    info = lookup_technique("T1110")
    # {"id": "T1110", "name": "Brute Force", "tactic": "Credential Access"}
"""

from __future__ import annotations

from typing import Optional

# ─── MITRE ATT&CK Technique Database ────────────────────────────────────
# Focused on techniques most relevant to TRIDENT-AI's detection scope:
# credential attacks, lateral movement, exfiltration, persistence
MITRE_TECHNIQUES: dict[str, dict[str, str]] = {
    # ─── Reconnaissance ──────────────────────────────────────────────
    "T1595": {"name": "Active Scanning", "tactic": "Reconnaissance"},
    "T1592": {"name": "Gather Victim Host Information", "tactic": "Reconnaissance"},
    "T1590": {"name": "Gather Victim Network Information", "tactic": "Reconnaissance"},
    "T1589": {"name": "Gather Victim Identity Information", "tactic": "Reconnaissance"},
    # ─── Initial Access ──────────────────────────────────────────────
    "T1190": {"name": "Exploit Public-Facing Application", "tactic": "Initial Access"},
    "T1133": {"name": "External Remote Services", "tactic": "Initial Access"},
    "T1078": {"name": "Valid Accounts", "tactic": "Initial Access"},
    "T1566": {"name": "Phishing", "tactic": "Initial Access"},
    "T1199": {"name": "Trusted Relationship", "tactic": "Initial Access"},
    # ─── Execution ───────────────────────────────────────────────────
    "T1059": {"name": "Command and Scripting Interpreter", "tactic": "Execution"},
    "T1203": {"name": "Exploitation for Client Execution", "tactic": "Execution"},
    "T1047": {"name": "Windows Management Instrumentation", "tactic": "Execution"},
    # ─── Persistence ─────────────────────────────────────────────────
    "T1098": {"name": "Account Manipulation", "tactic": "Persistence"},
    "T1136": {"name": "Create Account", "tactic": "Persistence"},
    "T1053": {"name": "Scheduled Task/Job", "tactic": "Persistence"},
    "T1505": {"name": "Server Software Component", "tactic": "Persistence"},
    # ─── Privilege Escalation ────────────────────────────────────────
    "T1068": {"name": "Exploitation for Privilege Escalation", "tactic": "Privilege Escalation"},
    "T1548": {"name": "Abuse Elevation Control Mechanism", "tactic": "Privilege Escalation"},
    # ─── Defense Evasion ─────────────────────────────────────────────
    "T1070": {"name": "Indicator Removal", "tactic": "Defense Evasion"},
    "T1562": {"name": "Impair Defenses", "tactic": "Defense Evasion"},
    "T1036": {"name": "Masquerading", "tactic": "Defense Evasion"},
    # ─── Credential Access ───────────────────────────────────────────
    "T1110": {"name": "Brute Force", "tactic": "Credential Access"},
    "T1110.001": {"name": "Brute Force: Password Guessing", "tactic": "Credential Access"},
    "T1110.003": {"name": "Brute Force: Password Spraying", "tactic": "Credential Access"},
    "T1110.004": {"name": "Brute Force: Credential Stuffing", "tactic": "Credential Access"},
    "T1003": {"name": "OS Credential Dumping", "tactic": "Credential Access"},
    "T1558": {"name": "Steal or Forge Kerberos Tickets", "tactic": "Credential Access"},
    "T1552": {"name": "Unsecured Credentials", "tactic": "Credential Access"},
    # ─── Discovery ───────────────────────────────────────────────────
    "T1046": {"name": "Network Service Discovery", "tactic": "Discovery"},
    "T1087": {"name": "Account Discovery", "tactic": "Discovery"},
    "T1082": {"name": "System Information Discovery", "tactic": "Discovery"},
    "T1018": {"name": "Remote System Discovery", "tactic": "Discovery"},
    # ─── Lateral Movement ────────────────────────────────────────────
    "T1021": {"name": "Remote Services", "tactic": "Lateral Movement"},
    "T1210": {"name": "Exploitation of Remote Services", "tactic": "Lateral Movement"},
    "T1534": {"name": "Internal Spearphishing", "tactic": "Lateral Movement"},
    # ─── Collection ──────────────────────────────────────────────────
    "T1005": {"name": "Data from Local System", "tactic": "Collection"},
    "T1039": {"name": "Data from Network Shared Drive", "tactic": "Collection"},
    "T1114": {"name": "Email Collection", "tactic": "Collection"},
    # ─── Command and Control ─────────────────────────────────────────
    "T1071": {"name": "Application Layer Protocol", "tactic": "Command and Control"},
    "T1105": {"name": "Ingress Tool Transfer", "tactic": "Command and Control"},
    "T1572": {"name": "Protocol Tunneling", "tactic": "Command and Control"},
    # ─── Exfiltration ────────────────────────────────────────────────
    "T1041": {"name": "Exfiltration Over C2 Channel", "tactic": "Exfiltration"},
    "T1048": {"name": "Exfiltration Over Alternative Protocol", "tactic": "Exfiltration"},
    "T1567": {"name": "Exfiltration Over Web Service", "tactic": "Exfiltration"},
    # ─── Impact ──────────────────────────────────────────────────────
    "T1498": {"name": "Network Denial of Service", "tactic": "Impact"},
    "T1499": {"name": "Endpoint Denial of Service", "tactic": "Impact"},
    "T1486": {"name": "Data Encrypted for Impact", "tactic": "Impact"},
    "T1489": {"name": "Service Stop", "tactic": "Impact"},
    "T1529": {"name": "System Shutdown/Reboot", "tactic": "Impact"},
}

# ─── Ordered tactic kill chain ───────────────────────────────────────────
TACTIC_ORDER: list[str] = [
    "Reconnaissance",
    "Resource Development",
    "Initial Access",
    "Execution",
    "Persistence",
    "Privilege Escalation",
    "Defense Evasion",
    "Credential Access",
    "Discovery",
    "Lateral Movement",
    "Collection",
    "Command and Control",
    "Exfiltration",
    "Impact",
]


def lookup_technique(technique_id: str) -> Optional[dict[str, str]]:
    """
    Look up a MITRE ATT&CK technique by its T-code.

    Args:
        technique_id: MITRE technique ID (e.g., "T1110", "T1110.001").

    Returns:
        Dict with keys {id, name, tactic} or None if not found.
    """
    entry = MITRE_TECHNIQUES.get(technique_id)
    if entry:
        return {"id": technique_id, **entry}
    return None


def enrich_techniques(technique_ids: list[str]) -> list[dict[str, str]]:
    """
    Enrich a list of T-codes with full names and tactics.

    Args:
        technique_ids: List of MITRE technique IDs.

    Returns:
        List of enriched technique dicts, ordered by kill chain phase.
    """
    enriched = []
    for tid in technique_ids:
        info = lookup_technique(tid)
        if info:
            enriched.append(info)
        else:
            enriched.append({"id": tid, "name": "Unknown Technique", "tactic": "Unknown"})

    # Sort by kill chain order
    tactic_rank = {t: i for i, t in enumerate(TACTIC_ORDER)}
    enriched.sort(key=lambda x: tactic_rank.get(x["tactic"], 999))
    return enriched


def get_tactic_chain(technique_ids: list[str]) -> list[str]:
    """
    Extract unique tactics from a list of techniques, ordered by kill chain.

    Args:
        technique_ids: List of MITRE technique IDs.

    Returns:
        Ordered list of unique tactic names present in the attack.
    """
    tactics = set()
    for tid in technique_ids:
        info = MITRE_TECHNIQUES.get(tid)
        if info:
            tactics.add(info["tactic"])

    tactic_rank = {t: i for i, t in enumerate(TACTIC_ORDER)}
    return sorted(tactics, key=lambda t: tactic_rank.get(t, 999))
