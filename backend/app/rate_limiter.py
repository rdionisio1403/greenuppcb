from threading import Lock
from time import monotonic


MAX_ATTEMPTS = 5
WINDOW_SECONDS = 300
MAX_TRACKED_KEYS = 10000

_attempts: dict[str, list[float]] = {}
_lock = Lock()


def _recent_attempts(key: str, now: float) -> list[float]:
    recent = [
        timestamp
        for timestamp in _attempts.get(key, [])
        if now - timestamp < WINDOW_SECONDS
    ]
    if recent:
        _attempts[key] = recent
    else:
        _attempts.pop(key, None)
    return recent


def _make_room_for_new_key(now: float) -> bool:
    if len(_attempts) < MAX_TRACKED_KEYS:
        return True

    # Remove expired entries only. Never evict an active rate-limit key.
    for existing_key in list(_attempts):
        _recent_attempts(existing_key, now)

    return len(_attempts) < MAX_TRACKED_KEYS


def is_rate_limited(key: str) -> bool:
    now = monotonic()
    with _lock:
        recent = _recent_attempts(key, now)
        if len(recent) >= MAX_ATTEMPTS:
            return True

        # When capacity is full, reject new keys rather than allowing
        # untracked login attempts. Expired keys may be reclaimed first.
        if key not in _attempts and not _make_room_for_new_key(now):
            return True

        return False


def check_and_record_attempt(key: str) -> bool:
    """Atomically check and record an attempt; fail closed at capacity."""
    now = monotonic()

    with _lock:
        recent = _recent_attempts(key, now)

        if len(recent) >= MAX_ATTEMPTS:
            return True

        if key not in _attempts and not _make_room_for_new_key(now):
            return True

        _attempts[key] = recent + [now]
        return False


def record_failed_attempt(key: str) -> None:
    now = monotonic()

    with _lock:
        recent = _recent_attempts(key, now)

        if key not in _attempts and not _make_room_for_new_key(now):
            return

        _attempts[key] = recent + [now]


def reset_attempts(key: str) -> None:
    with _lock:
        _attempts.pop(key, None)


def get_attempt_count(key: str) -> int:
    now = monotonic()
    with _lock:
        return len(_recent_attempts(key, now))
