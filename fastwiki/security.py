from __future__ import annotations
import base64, hashlib, hmac, json, os, time

_seen: dict[str, int] = {}

def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

def verify_suite_ticket(ticket: str) -> dict | None:
    secret = os.getenv("FASTOFFICE_SSO_SECRET", "")
    if not secret or "." not in ticket:
        return None
    raw, signature = ticket.rsplit(".", 1)
    expected = hmac.new(secret.encode(), raw.encode(), hashlib.sha256).hexdigest()
    try:
        if not hmac.compare_digest(expected, signature):
            return None
        payload = json.loads(_b64decode(raw))
    except (ValueError, TypeError, json.JSONDecodeError):
        return None
    now = int(time.time())
    ticket_id = str(payload.get("jti", ""))
    if payload.get("aud") != "wiki" or int(payload.get("exp", 0)) < now or not ticket_id or ticket_id in _seen:
        return None
    _seen[ticket_id] = int(payload["exp"])
    for key, expiry in list(_seen.items()):
        if expiry < now:
            _seen.pop(key, None)
    required = {"sub", "email", "org_id", "role"}
    return payload if required <= payload.keys() else None

def api_authorized(authorization: str | None) -> bool:
    token = os.getenv("FASTSME_API_TOKEN", "")
    return bool(token and authorization == f"Bearer {token}")

def google_email_allowed(info: dict) -> bool:
    email = str(info.get("email") or "").strip().lower()
    if not email or not info.get("email_verified", False) or "@" not in email:
        return False
    domains = {
        domain.strip().lower()
        for domain in os.getenv("GOOGLE_ALLOWED_DOMAINS", "mymedicalgateway.com").split(",")
        if domain.strip()
    }
    return email.rsplit("@", 1)[1] in domains

def google_identity(info: dict) -> dict:
    email = str(info["email"]).strip().lower()
    subject = str(info.get("sub") or email)
    return {
        "sub": f"google:{subject}",
        "email": email,
        "name": str(info.get("name") or email.split("@", 1)[0]),
        "org_id": os.getenv("FASTWIKI_ORG_ID", "mymedicalgateway.com"),
        "org_name": os.getenv("FASTWIKI_ORG_NAME", "My Medical Gateway"),
        "role": "member",
    }
