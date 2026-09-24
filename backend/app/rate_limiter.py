from collections import defaultdict
from time import monotonic
from threading import Lock


MAX_ATTEMPTS = 5
WINDOW_SECONDS = 300


_attempts = defaultdict(list)
_lock = Lock()


def is_rate_limited(key: str) -> bool:
    now = monotonic()

    with _lock:
        recent_attempts = [
            timestamp
            for timestamp in _attempts[key]
            if now - timestamp < WINDOW_SECONDS
        ]

        _attempts[key] = recent_attempts

        return len(recent_attempts) >= MAX_ATTEMPTS


def record_failed_attempt(key: str) -> None:
    with _lock:
        _attempts[key].append(monotonic())


def reset_attempts(key: str) -> None:
    with _lock:
        _attempts.pop(key, None)


def get_attempt_count(key: str) -> int:
    now = monotonic()

    with _lock:
        recent_attempts = [
            timestamp
            for timestamp in _attempts[key]
            if now - timestamp < WINDOW_SECONDS
        ]

        _attempts[key] = recent_attempts

        return len(recent_attempts)
