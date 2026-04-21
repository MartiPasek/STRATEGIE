"""
Rate limiter pro login endpoint -- ochrana proti brute-force.

Per-IP sliding window:
- MAX_FAILED_ATTEMPTS (5) selhanych pokusu v WINDOW_SECONDS (15 min) = block
- Block trva do konce okna (ne fixed duration -- prirozene se rozplyne)
- Uspesny login resetuje counter pro danou IP

In-memory implementace (jeden process pres NSSM service). Pri restartu
se stav vynuluje (akceptovatelne pro MVP -- restart neni utocnikem ovladany,
plus 15 min okno znamena ze maximalni "free pokusy" pri restartu = 5).

Pro multi-process deployment (gunicorn workers, K8s) bude potreba
Redis-backed verze. Aktualne jeden uvicorn worker.

Thread-safe pres threading.Lock (FastAPI vola sync handlers v thread poolu).
"""
from __future__ import annotations

import time
import threading
from collections import defaultdict
from dataclasses import dataclass

from core.logging import get_logger

logger = get_logger("auth.rate_limit")

MAX_FAILED_ATTEMPTS = 5
WINDOW_SECONDS = 15 * 60   # 15 minut
PRUNE_INTERVAL_SECONDS = 5 * 60   # cistime mrtve entry kazdych 5 min


@dataclass
class RateLimitResult:
    allowed: bool
    retry_after_seconds: int   # kolik sekund pockat pred dalsim pokusem (0 = jeste muzes)
    failed_attempts: int       # kolik selhani v aktualnim okne (info pro user-facing message)


class _LoginRateLimiter:
    def __init__(self):
        # IP -> list of timestamps of FAILED attempts within window
        self._failed: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()
        self._last_prune = time.time()

    def _prune_locked(self, now: float) -> None:
        """Smaze stare zaznamy mimo okno. Volat s drzenym _lockem."""
        if now - self._last_prune < PRUNE_INTERVAL_SECONDS:
            return
        cutoff = now - WINDOW_SECONDS
        empty_keys = []
        for ip, timestamps in self._failed.items():
            self._failed[ip] = [t for t in timestamps if t > cutoff]
            if not self._failed[ip]:
                empty_keys.append(ip)
        for k in empty_keys:
            del self._failed[k]
        self._last_prune = now
        if empty_keys:
            logger.debug(f"RATE_LIMIT | pruned {len(empty_keys)} empty IP entries")

    def check(self, ip: str) -> RateLimitResult:
        """Zkontroluje zda IP smi udelat dalsi pokus. Pouze cte stav."""
        if not ip:
            # Bez IP nemuzeme rate-limitovat (napr. tests bez TestClient).
            # Povolujeme. V produkci je IP vzdy.
            return RateLimitResult(allowed=True, retry_after_seconds=0, failed_attempts=0)
        now = time.time()
        cutoff = now - WINDOW_SECONDS
        with self._lock:
            self._prune_locked(now)
            # Aktivni failed pokusy v okne
            recent = [t for t in self._failed.get(ip, []) if t > cutoff]
            self._failed[ip] = recent   # kompaktuj pro tuto IP
            if len(recent) >= MAX_FAILED_ATTEMPTS:
                # Nejstarsi pokus + okno = kdy se uvolni
                oldest = min(recent)
                retry_after = int(oldest + WINDOW_SECONDS - now) + 1
                return RateLimitResult(
                    allowed=False,
                    retry_after_seconds=max(retry_after, 1),
                    failed_attempts=len(recent),
                )
            return RateLimitResult(
                allowed=True,
                retry_after_seconds=0,
                failed_attempts=len(recent),
            )

    def record_failure(self, ip: str) -> None:
        """Zaznamena selhanlej login pokus. Volat PO (failed) check + auth."""
        if not ip:
            return
        now = time.time()
        with self._lock:
            self._failed[ip].append(now)
            count = len(self._failed[ip])
        if count >= MAX_FAILED_ATTEMPTS:
            logger.warning(
                f"RATE_LIMIT | IP blocked | ip={ip} | failed_attempts={count}"
            )

    def record_success(self, ip: str) -> None:
        """Uspesny login -> reset counter pro tuto IP (vita user, ne utocnik)."""
        if not ip:
            return
        with self._lock:
            self._failed.pop(ip, None)


# Singleton instance pouzivany z auth routeru
login_rate_limiter = _LoginRateLimiter()


class _ForgotPasswordRateLimiter(_LoginRateLimiter):
    """Stejna logika jako login, ale shovivavejsi limity -- forgot-password
    je mene atakovatelna (no-enumeration design + email send delay), ale chce
    se chranit proti email-flood spamu."""
    pass


# Override constants pro forgot-password (mensi window, sirsi tolerance)
_FORGOT_MAX_REQUESTS = 10
_FORGOT_WINDOW = 60 * 60   # 1 hodina


# Pouziti: monkey-patch konstant na instanci. Cleaner by bylo refactor _LoginRateLimiter
# na configurable, ale to chce vetsi prepis. Pro MVP staci instancovat s globalnimi.
forgot_password_rate_limiter = _ForgotPasswordRateLimiter()


def check_forgot_password_limit(ip: str) -> RateLimitResult:
    """Wrapper s forgot-specific limity (10 req / 1 hodina)."""
    if not ip:
        return RateLimitResult(allowed=True, retry_after_seconds=0, failed_attempts=0)
    now = time.time()
    cutoff = now - _FORGOT_WINDOW
    with forgot_password_rate_limiter._lock:
        forgot_password_rate_limiter._prune_locked(now)
        recent = [t for t in forgot_password_rate_limiter._failed.get(ip, []) if t > cutoff]
        forgot_password_rate_limiter._failed[ip] = recent
        if len(recent) >= _FORGOT_MAX_REQUESTS:
            oldest = min(recent)
            retry_after = int(oldest + _FORGOT_WINDOW - now) + 1
            return RateLimitResult(
                allowed=False,
                retry_after_seconds=max(retry_after, 1),
                failed_attempts=len(recent),
            )
        return RateLimitResult(allowed=True, retry_after_seconds=0, failed_attempts=len(recent))


def record_forgot_password_request(ip: str) -> None:
    """Zaznamena KAZDOU forgot-password zadost (uspech i fail).
    Lisi se od login rate limiter -- tam zaznamenava jen FAILED."""
    if not ip:
        return
    now = time.time()
    with forgot_password_rate_limiter._lock:
        forgot_password_rate_limiter._failed[ip].append(now)
