"""
Supabase (PostgreSQL) database layer - replaces SQLite
"""

import os
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from supabase import create_client, Client

@dataclass
class Email:
    message_id: str
    sender: str
    subject: str
    snippet: str
    category: str = ""
    confidence: float = 0.0
    reasoning: str = ""
    processed_at: str = ""

class SupabaseDB:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY required in environment")
        self.client: Client = create_client(url, key)
        self._init_table()
    
    def _init_table(self):
        """Create table if not exists (run once)"""
        # Table created via Supabase dashboard or migration
        pass
    
    def is_processed(self, message_id: str) -> bool:
        res = self.client.table("emails").select("message_id").eq("message_id", message_id).execute()
        return len(res.data) > 0
    
    def save_email(self, email: Email):
        data = {
            "message_id": email.message_id,
            "sender": email.sender,
            "subject": email.subject,
            "snippet": email.snippet,
            "category": email.category,
            "confidence": email.confidence,
            "reasoning": email.reasoning,
            "processed_at": email.processed_at or datetime.now().isoformat()
        }
        self.client.table("emails").upsert(data, on_conflict="message_id").execute()
    
    def get_emails_by_category(self, category: str, limit: int = 50) -> List[Email]:
        res = self.client.table("emails").select("*").eq("category", category).order("processed_at", desc=True).limit(limit).execute()
        return [self._row_to_email(r) for r in res.data]
    
    def get_all_emails(self, limit: int = 100) -> List[Email]:
        res = self.client.table("emails").select("*").order("processed_at", desc=True).limit(limit).execute()
        return [self._row_to_email(r) for r in res.data]
    
    def get_stats(self) -> Dict[str, int]:
        res = self.client.table("emails").select("category").execute()
        stats = {}
        for row in res.data:
            cat = row.get("category") or "Uncategorized"
            stats[cat] = stats.get(cat, 0) + 1
        return stats
    
    def get_unprocessed_count(self) -> int:
        res = self.client.table("emails").select("message_id", count="exact").or_("category.is.null,category.eq.").execute()
        return res.count or 0
    
    def _row_to_email(self, row: dict) -> Email:
        return Email(
            message_id=row["message_id"],
            sender=row["sender"],
            subject=row["subject"],
            snippet=row["snippet"],
            category=row.get("category", ""),
            confidence=row.get("confidence", 0.0),
            reasoning=row.get("reasoning", ""),
            processed_at=row.get("processed_at", "")
        )
    
    def close(self):
        pass  # Supabase client doesn't need explicit close