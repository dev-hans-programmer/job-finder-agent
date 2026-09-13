import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(
    user_id: uuid.UUID,
    email: str,
    roles: list[str],
    secret: str,
    minutes: int,
    issuer: str,
    session_id: uuid.UUID | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user_id),
            "email": email,
            "roles": roles,
            "type": "access",
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": now + timedelta(minutes=minutes),
            "iss": issuer,
            **({"sid": str(session_id)} if session_id else {}),
        },
        secret,
        algorithm="HS256",
    )


def decode_access_token(token: str, secret: str, issuer: str) -> dict:
    claims = jwt.decode(token, secret, algorithms=["HS256"], issuer=issuer)
    if claims.get("type") != "access" or not claims.get("sub"):
        raise jwt.InvalidTokenError("invalid access token")
    return claims
