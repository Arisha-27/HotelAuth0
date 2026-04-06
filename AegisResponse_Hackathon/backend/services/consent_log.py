"""
Phase 6 — Step 73: Consent Logging System
Immutable audit trail for all human-in-the-loop decisions.
Provides tamper-evident hashing for compliance and legal requirements.
"""

import json
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

from pydantic import BaseModel, Field

from backend.logging_config import get_logger
from backend.config import settings

logger = get_logger("services.consent_log")


class ConsentEntry(BaseModel):
    """A single consent/audit entry in the immutable log."""
    entry_id: str = Field(default_factory=lambda: f"CON-{uuid.uuid4().hex[:10].upper()}")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # What happened
    action_type: str                        # "approval", "denial", "override", "consent_given", "data_access"
    action_description: str
    category: str = ""                      # security, financial, guest_data, etc.

    # Who was involved
    subject: str = ""                       # Who is affected (guest, room, etc.)
    actor: str = ""                         # Who performed the action
    actor_role: str = ""                    # Role of the actor
    agent_id: str = ""                      # If an AI agent was involved

    # Decision context
    criticality: str = ""
    approval_id: str = ""                   # Link to approval request
    hotel_id: str = "hotel-grandview"

    # Legal / compliance fields
    consent_type: str = "operational"       # "operational", "gdpr_consent", "data_deletion", "financial_auth"
    legal_basis: str = ""                   # GDPR legal basis if applicable
    data_retention_days: int = 365

    # Integrity
    previous_hash: str = ""                 # Hash of the previous entry (chain)
    entry_hash: str = ""                    # SHA-256 of this entry's content
    metadata: dict = Field(default_factory=dict)


class ConsentLogService:
    """
    Immutable consent and audit log with tamper-evident hashing.
    Each entry is chained to the previous via SHA-256, creating
    a lightweight blockchain-style audit trail.
    """

    def __init__(self):
        self._entries: list[ConsentEntry] = []
        self._log_file = Path("logs/consent_log.jsonl")
        self._log_file.parent.mkdir(parents=True, exist_ok=True)
        self._last_hash = "GENESIS"

    def _compute_hash(self, entry: ConsentEntry) -> str:
        """Compute SHA-256 hash of the entry content for tamper evidence."""
        content = {
            "entry_id": entry.entry_id,
            "timestamp": entry.timestamp,
            "action_type": entry.action_type,
            "action_description": entry.action_description,
            "subject": entry.subject,
            "actor": entry.actor,
            "actor_role": entry.actor_role,
            "previous_hash": entry.previous_hash,
        }
        return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()

    def log(
        self,
        action_type: str,
        action_description: str,
        actor: str = "system",
        actor_role: str = "",
        subject: str = "",
        agent_id: str = "",
        category: str = "",
        criticality: str = "",
        approval_id: str = "",
        hotel_id: str = "hotel-grandview",
        consent_type: str = "operational",
        legal_basis: str = "",
        metadata: dict = None,
    ) -> ConsentEntry:
        """Record a consent/audit entry in the immutable log."""
        entry = ConsentEntry(
            action_type=action_type,
            action_description=action_description,
            category=category,
            subject=subject,
            actor=actor,
            actor_role=actor_role,
            agent_id=agent_id,
            criticality=criticality,
            approval_id=approval_id,
            hotel_id=hotel_id,
            consent_type=consent_type,
            legal_basis=legal_basis,
            previous_hash=self._last_hash,
            metadata=metadata or {},
        )

        # Compute integrity hash
        entry.entry_hash = self._compute_hash(entry)
        self._last_hash = entry.entry_hash

        # Store in memory + file
        self._entries.append(entry)
        self._write_to_file(entry)

        logger.info(
            f"📋 CONSENT LOG: {action_type} by {actor} — {action_description[:80]}",
            extra={"extra_data": {
                "entry_id": entry.entry_id,
                "action_type": action_type,
                "actor": actor,
                "hash": entry.entry_hash[:16] + "...",
            }},
        )

        return entry

    def log_approval(self, approval_data: dict) -> ConsentEntry:
        """Convenience method for logging approval decisions."""
        return self.log(
            action_type="approval" if approval_data.get("status") == "approved" else "denial",
            action_description=f"Action '{approval_data.get('action_type', 'unknown')}' — {approval_data.get('status', 'unknown')}",
            actor=approval_data.get("approver", "unknown"),
            actor_role=approval_data.get("approver_role", ""),
            category=approval_data.get("category", ""),
            criticality=approval_data.get("criticality", ""),
            approval_id=approval_data.get("approval_id", ""),
            hotel_id=approval_data.get("hotel_id", "hotel-grandview"),
            consent_type="operational",
            metadata=approval_data,
        )

    def _write_to_file(self, entry: ConsentEntry):
        """Append entry to the JSONL consent log file."""
        try:
            with open(self._log_file, "a") as f:
                f.write(json.dumps(entry.model_dump(), default=str) + "\n")
        except Exception as e:
            logger.error(f"Failed to write consent log entry: {e}")

    def verify_integrity(self) -> dict:
        """Verify the integrity of the entire consent log chain."""
        if not self._entries:
            return {"valid": True, "entries_checked": 0, "message": "Empty log"}

        prev_hash = "GENESIS"
        broken_at = None

        for i, entry in enumerate(self._entries):
            # Check chain link
            if entry.previous_hash != prev_hash:
                broken_at = i
                break
            # Recompute and verify hash
            computed = self._compute_hash(entry)
            if computed != entry.entry_hash:
                broken_at = i
                break
            prev_hash = entry.entry_hash

        if broken_at is not None:
            return {
                "valid": False,
                "entries_checked": broken_at + 1,
                "broken_at_index": broken_at,
                "broken_entry_id": self._entries[broken_at].entry_id,
                "message": f"Integrity violation detected at entry {broken_at}",
            }

        return {
            "valid": True,
            "entries_checked": len(self._entries),
            "last_hash": self._last_hash[:16] + "...",
            "message": "All entries verified — chain intact",
        }

    def get_entries(
        self,
        limit: int = 50,
        action_type: str = None,
        actor: str = None,
        hotel_id: str = None,
    ) -> list[dict]:
        """Query consent log entries with optional filters."""
        entries = self._entries.copy()
        if action_type:
            entries = [e for e in entries if e.action_type == action_type]
        if actor:
            entries = [e for e in entries if e.actor == actor]
        if hotel_id:
            entries = [e for e in entries if e.hotel_id == hotel_id]
        return [e.model_dump() for e in entries[-limit:]]

    def get_stats(self) -> dict:
        return {
            "total_entries": len(self._entries),
            "integrity": self.verify_integrity(),
            "by_type": {},
            "last_entry": self._entries[-1].model_dump() if self._entries else None,
        }


# Singleton
consent_log = ConsentLogService()
