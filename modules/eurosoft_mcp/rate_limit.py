"""
Simple in-memory rate limiter for EUROSOFT MCP server.

Token bucket per (api_key, action_kind) — read vs insert have separate
limits. Single-process, stateful (will reset on service restart, OK for MVP).
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from .config import settings


class RateLimiter:
    """Sliding-window rate limiter (last-N-seconds)."""

    def __init__(self):
        self._events: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check_and_record(self, key: str, action_kind: str) -> tuple[bool, int]:
        """
        Check if action is allowed for key. If yes, record + return (True, count).
        If no, return (False, count).

        action_kind: "read" or "insert"
        """
        if action_kind == "read":
            limit = settings.rate_limit_read_per_min
        elif action_kind == "insert":
            limit = settings.rate_limit_insert_per_min
        else:
            return True, 0  # unknown action = no limit

        now = time.monotonic()
        cutoff = now - 60  # 60 seconds window

        bucket_key = (key, action_kind)
        with self._lock:
            events = self._events[bucket_key]
            # Drop events older than 60s
            while events and events[0] < cutoff:
                events.popleft()
            count = len(events)
            if count >= limit:
                return False, count
            events.append(now)
            return True, count + 1


limiter = RateLimiter()
