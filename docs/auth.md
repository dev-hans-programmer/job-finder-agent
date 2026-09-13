The access token is a JWT. The refresh token is intentionally not a JWT.
Access token
The access token is created using JWT:
header.payload.signature
Example shape:
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOi...signature
It contains claims such as:
{
  "sub": "user-id",
  "email": "user@example.com",
  "roles": ["user"],
  "type": "access",
  "iss": "job-radar-agent",
  "exp": 1780000000,
  "jti": "token-id"
}
The API can validate it locally using the signing key without querying the database on every request.
Refresh token
The refresh token is an opaque random value generated using:
secrets.token_urlsafe(48)
It looks like:
w1wLxQ8...random-value...
It is not a JWT because it has no header, payload, or signature.
Only its hash is stored in PostgreSQL:
raw refresh token → SHA-256 hash → database
The raw refresh token is returned to the client once, but the database stores only:
token_hash
user_id
family_id
expires_at
revoked_at
How refresh works
1. Login
The server creates:
- Short-lived JWT access token
- Long-lived random refresh token
- Database record containing the refresh token hash
Client:
  access_token
  refresh_token

Database:
  hash(refresh_token)
2. Calling protected APIs
The client sends only the access token:
Authorization: Bearer <access-token>
The API validates the JWT.
3. Access token expires
The client sends the refresh token:
POST /api/v1/auth/refresh
{
  "refresh_token": "random-refresh-token"
}
The server:
1. Hashes the supplied token.
2. Finds the matching database record.
3. Checks expiration.
4. Checks whether it was revoked.
5. Revokes the old token family.
6. Creates a new access token.
7. Creates a new refresh token.
The old refresh token can no longer be used.
Why the refresh token is not a JWT
A random opaque token provides simpler and stronger revocation behavior.
If refresh tokens were JWTs:
- The token would contain readable claims.
- Revoking one JWT would require a blacklist or database lookup.
- Rotation and reuse detection would still require database state.
- A stolen JWT would remain valid until expiration unless actively tracked.
- Sensitive refresh claims could be exposed through the token payload.
With the current design:
- Refresh tokens contain no meaningful information.
- The database controls whether they are valid.
- Tokens can be revoked immediately.
- Token reuse can be detected.
- The raw token is never stored in the database.
- Refresh-token families can be revoked after suspected theft.
Why not use JWTs for both?
JWT refresh tokens are valid in some architectures, especially when:
- The system needs mostly stateless authentication.
- Immediate revocation is not required.
- Refresh tokens are very short-lived.
- A token blacklist or session store already exists.
However, for this application we already need database state for:
- Logout
- Refresh rotation
- Reuse detection
- Disabled users
- Session revocation
Therefore, using an opaque refresh token is more appropriate.
The design is:
Access token  = JWT, short-lived, mostly stateless
Refresh token = random opaque value, long-lived, database-controlled
