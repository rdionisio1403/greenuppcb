from app.security import hash_password, verify_password


LEGACY_PASSWORD = "Legacy-Bcrypt-Migration-2026!"
LEGACY_BCRYPT_HASH = '$2b$12$Oon4WFP22Sq8MOieZGkWM.yOO/48pFM5xpeKymsTkxn.EJigDvs5e'


def test_existing_bcrypt_hash_remains_verifiable():
    assert verify_password(LEGACY_PASSWORD, LEGACY_BCRYPT_HASH)


def test_existing_bcrypt_hash_rejects_wrong_password():
    assert not verify_password(
        "Definitely-Wrong-Password!", LEGACY_BCRYPT_HASH
    )


def test_new_password_hash_uses_argon2id():
    password = "New-Argon2-Migration-Test-2026!"
    encoded = hash_password(password)

    assert encoded.startswith("$argon2id$")
    assert verify_password(password, encoded)
    assert not verify_password("Wrong-Argon2-Password!", encoded)
