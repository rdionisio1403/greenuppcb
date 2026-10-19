import pytest

import app.rate_limiter as limiter


@pytest.fixture(autouse=True)
def clear_attempts():
    with limiter._lock:
        limiter._attempts.clear()

    yield

    with limiter._lock:
        limiter._attempts.clear()


def test_attempt_limit_expires_after_window(monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(limiter, "monotonic", lambda: clock[0])

    for _ in range(limiter.MAX_ATTEMPTS):
        assert limiter.check_and_record_attempt("account:first") is False

    assert limiter.check_and_record_attempt("account:first") is True
    assert limiter.get_attempt_count("account:first") == limiter.MAX_ATTEMPTS

    clock[0] += limiter.WINDOW_SECONDS + 1

    assert limiter.get_attempt_count("account:first") == 0
    assert limiter.check_and_record_attempt("account:first") is False


def test_capacity_does_not_evict_active_keys(monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(limiter, "monotonic", lambda: clock[0])
    monkeypatch.setattr(limiter, "MAX_TRACKED_KEYS", 2)

    for _ in range(limiter.MAX_ATTEMPTS):
        assert limiter.check_and_record_attempt("account:first") is False

    assert limiter.check_and_record_attempt("account:first") is True
    assert limiter.check_and_record_attempt("account:second") is False

    # Unknown keys must also fail closed at capacity, including login callers
    # that check the limit separately from recording the failed attempt.
    assert limiter.is_rate_limited("account:third")
    assert limiter.check_and_record_attempt("account:third") is True
    assert limiter.is_rate_limited("account:first")
    assert limiter.get_attempt_count("account:first") == limiter.MAX_ATTEMPTS


def test_expired_keys_are_reclaimed_when_capacity_is_full(monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(limiter, "monotonic", lambda: clock[0])
    monkeypatch.setattr(limiter, "MAX_TRACKED_KEYS", 2)

    assert limiter.check_and_record_attempt("account:first") is False
    assert limiter.check_and_record_attempt("account:second") is False

    clock[0] += limiter.WINDOW_SECONDS + 1

    assert limiter.check_and_record_attempt("account:third") is False
    assert limiter.get_attempt_count("account:first") == 0
    assert limiter.get_attempt_count("account:second") == 0
