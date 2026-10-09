from app.security import generate_reset_token, hash_reset_token


def test_reset_tokens_are_unique_and_hashes_do_not_match_raw_tokens():
    first_token = generate_reset_token()
    second_token = generate_reset_token()

    assert first_token != second_token
    assert len(first_token) >= 32

    first_hash = hash_reset_token(first_token)

    assert first_hash != first_token
    assert first_hash == hash_reset_token(first_token)
    assert first_hash != hash_reset_token(second_token)
