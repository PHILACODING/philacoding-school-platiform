import pytest
from fastapi import HTTPException

from app.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_and_token_round_trip() -> None:
    password_hash = hash_password("ChangeMe123!")

    assert verify_password("ChangeMe123!", password_hash)
    assert not verify_password("wrong-password", password_hash)

    token = create_access_token(user_id=7, school_id=3, role="teacher")
    claims = decode_access_token(token)

    assert claims["sub"] == 7
    assert claims["school_id"] == 3
    assert claims["role"] == "teacher"


def test_malformed_token_is_rejected_with_unauthorized_error() -> None:
    with pytest.raises(HTTPException) as error:
        decode_access_token("not-a-valid-token.!!!")

    assert error.value.status_code == 401
