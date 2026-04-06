"""
Step 57: Notion API Integration for CRM / Operational Logs
Uses Notion API to log incidents, guest records, and operational events.
Supports both real Notion API and mock fallback.
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger("ahos.integrations.notion")


# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────
class NotionLogEntry(BaseModel):
    """An entry to log into Notion CRM database."""
    title: str = Field(..., description="Entry title")
    category: str = Field(default="general", description="Category: incident, guest, booking, maintenance, finance")
    status: str = Field(default="open", description="Status: open, in_progress, resolved, closed")
    priority: str = Field(default="medium", description="Priority: low, medium, high, critical")
    hotel_id: str = Field(default="HQ", description="Hotel identifier")
    description: str = Field(default="", description="Detailed description")
    assigned_agent: str = Field(default="system", description="Agent responsible")
    tags: list[str] = Field(default_factory=list, description="Tags for filtering")
    metadata: dict = Field(default_factory=dict, description="Additional structured data")


class NotionQueryFilter(BaseModel):
    """Filter for querying Notion database entries."""
    hotel_id: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)


class NotionResult(BaseModel):
    """Result of a Notion operation."""
    success: bool
    page_id: Optional[str] = None
    timestamp: str
    provider: str  # "notion_api" or "mock"
    data: dict = Field(default_factory=dict)


# ─────────────────────────────────────────────
# Notion Service
# ─────────────────────────────────────────────
class NotionService:
    """
    Notion integration for AHOS CRM and operational logging.
    Falls back to in-memory mock if Notion credentials are not set.
    """

    NOTION_API_VERSION = "2022-06-28"
    NOTION_BASE_URL = "https://api.notion.com/v1"

    # Category → Emoji mapping for Notion pages
    CATEGORY_ICONS = {
        "incident": "🚨",
        "guest": "👤",
        "booking": "📅",
        "maintenance": "🔧",
        "finance": "💰",
        "general": "📋",
    }

    # Status → Color mapping for Notion select properties
    STATUS_COLORS = {
        "open": "red",
        "in_progress": "yellow",
        "resolved": "green",
        "closed": "gray",
    }

    def __init__(self):
        self.api_key = os.getenv("NOTION_API_KEY")
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        self._mock_store: list[dict] = []
        self._mock_counter = 0

    @property
    def is_configured(self) -> bool:
        return all([self.api_key, self.database_id])

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": self.NOTION_API_VERSION,
            "Content-Type": "application/json",
        }

    async def create_log(self, entry: NotionLogEntry) -> NotionResult:
        """Create a new log entry in Notion."""
        if self.is_configured:
            return await self._create_via_api(entry)
        return await self._create_mock(entry)

    async def query_logs(self, filters: NotionQueryFilter) -> NotionResult:
        """Query log entries from Notion."""
        if self.is_configured:
            return await self._query_via_api(filters)
        return await self._query_mock(filters)

    async def _create_via_api(self, entry: NotionLogEntry) -> NotionResult:
        """Create entry via real Notion API."""
        try:
            icon = self.CATEGORY_ICONS.get(entry.category, "📋")
            status_color = self.STATUS_COLORS.get(entry.status, "default")

            payload = {
                "parent": {"database_id": self.database_id},
                "icon": {"emoji": icon},
                "properties": {
                    "Title": {"title": [{"text": {"content": entry.title}}]},
                    "Category": {"select": {"name": entry.category}},
                    "Status": {"select": {"name": entry.status, "color": status_color}},
                    "Priority": {"select": {"name": entry.priority}},
                    "Hotel": {"rich_text": [{"text": {"content": entry.hotel_id}}]},
                    "Agent": {"rich_text": [{"text": {"content": entry.assigned_agent}}]},
                    "Tags": {"multi_select": [{"name": tag} for tag in entry.tags]},
                    "Created": {"date": {"start": datetime.now(timezone.utc).isoformat()}},
                },
                "children": [
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"text": {"content": "Description"}}]
                        },
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"text": {"content": entry.description or "No description provided."}}]
                        },
                    },
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"text": {"content": "Metadata"}}]
                        },
                    },
                    {
                        "object": "block",
                        "type": "code",
                        "code": {
                            "rich_text": [{"text": {"content": json.dumps(entry.metadata, indent=2)}}],
                            "language": "json",
                        },
                    },
                ],
            }

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.NOTION_BASE_URL}/pages",
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()

            result = NotionResult(
                success=True,
                page_id=data.get("id"),
                timestamp=datetime.now(timezone.utc).isoformat(),
                provider="notion_api",
                data={"url": data.get("url")},
            )
            logger.info(f"Notion page created: {result.page_id}")
            return result

        except Exception as e:
            logger.error(f"Notion API create failed: {e}")
            return NotionResult(
                success=False,
                timestamp=datetime.now(timezone.utc).isoformat(),
                provider="notion_api",
                data={"error": str(e)},
            )

    async def _create_mock(self, entry: NotionLogEntry) -> NotionResult:
        """Mock Notion page creation for development."""
        self._mock_counter += 1
        page_id = f"mock-notion-{self._mock_counter:04d}"
        icon = self.CATEGORY_ICONS.get(entry.category, "📋")

        record = {
            "id": page_id,
            "title": entry.title,
            "category": entry.category,
            "status": entry.status,
            "priority": entry.priority,
            "hotel_id": entry.hotel_id,
            "description": entry.description,
            "assigned_agent": entry.assigned_agent,
            "tags": entry.tags,
            "metadata": entry.metadata,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._mock_store.append(record)

        logger.info(
            f"\n{'─'*50}\n"
            f"{icon} NOTION LOG CREATED (Mock)\n"
            f"{'─'*50}\n"
            f"  ID:       {page_id}\n"
            f"  Title:    {entry.title}\n"
            f"  Category: {entry.category}\n"
            f"  Status:   {entry.status}\n"
            f"  Hotel:    {entry.hotel_id}\n"
            f"  Agent:    {entry.assigned_agent}\n"
            f"{'─'*50}"
        )

        return NotionResult(
            success=True,
            page_id=page_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            provider="mock",
            data=record,
        )

    async def _query_via_api(self, filters: NotionQueryFilter) -> NotionResult:
        """Query Notion database via API."""
        try:
            filter_conditions = []
            if filters.hotel_id:
                filter_conditions.append({
                    "property": "Hotel",
                    "rich_text": {"contains": filters.hotel_id},
                })
            if filters.category:
                filter_conditions.append({
                    "property": "Category",
                    "select": {"equals": filters.category},
                })
            if filters.status:
                filter_conditions.append({
                    "property": "Status",
                    "select": {"equals": filters.status},
                })

            payload = {"page_size": filters.limit}
            if filter_conditions:
                payload["filter"] = {"and": filter_conditions} if len(filter_conditions) > 1 else filter_conditions[0]

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.NOTION_BASE_URL}/databases/{self.database_id}/query",
                    headers=self._headers(),
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()

            return NotionResult(
                success=True,
                timestamp=datetime.now(timezone.utc).isoformat(),
                provider="notion_api",
                data={"results": data.get("results", []), "has_more": data.get("has_more", False)},
            )

        except Exception as e:
            logger.error(f"Notion API query failed: {e}")
            return NotionResult(
                success=False,
                timestamp=datetime.now(timezone.utc).isoformat(),
                provider="notion_api",
                data={"error": str(e)},
            )

    async def _query_mock(self, filters: NotionQueryFilter) -> NotionResult:
        """Query mock in-memory store."""
        results = self._mock_store.copy()

        if filters.hotel_id:
            results = [r for r in results if r["hotel_id"] == filters.hotel_id]
        if filters.category:
            results = [r for r in results if r["category"] == filters.category]
        if filters.status:
            results = [r for r in results if r["status"] == filters.status]
        if filters.priority:
            results = [r for r in results if r["priority"] == filters.priority]

        results = results[: filters.limit]

        return NotionResult(
            success=True,
            timestamp=datetime.now(timezone.utc).isoformat(),
            provider="mock",
            data={"results": results, "total": len(results)},
        )

    def get_all_logs(self) -> list[dict]:
        """Get all mock logs (for development dashboard)."""
        return self._mock_store.copy()


# ─────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────
notion_service = NotionService()
