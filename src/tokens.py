"""
Token management — clean, modern API tokens for Panda AI.

Format: pnd_<32 random hex chars>  (36 chars total)
Examples: pnd_7Kx9mQ2vL8rT4nY6cW1zP5aH3bN8

Features:
- Short prefix for easy identification in logs
- Built-in expiry, scope, and name metadata
- Server-side validation (environment is internal, not in key)
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import time
from dataclasses import dataclass, field, asdict
from typing import Optional

from src.config import Config

# ── Token format ───────────────────────────────────────────────

TOKEN_PREFIX = "pnd_"
TOKEN_RANDOM_BYTES = 16  # 16 bytes → 32 hex chars → 36 total with prefix


def generate_token() -> str:
    """Generate a new pnd_ prefixed token."""
    return TOKEN_PREFIX + secrets.token_hex(TOKEN_RANDOM_BYTES)


def is_valid_format(token: str) -> bool:
    """Check if a token matches the pnd_ format."""
    if not token.startswith(TOKEN_PREFIX):
        return False
    body = token[len(TOKEN_PREFIX):]
    return len(body) == TOKEN_RANDOM_BYTES * 2 and all(c in "0123456789abcdef" for c in body)


def hash_token(token: str) -> str:
    """Hash a token for secure storage (SHA-256)."""
    return hashlib.sha256(token.encode()).hexdigest()


# ── Token metadata ─────────────────────────────────────────────

@dataclass
class TokenMeta:
    """Metadata attached to an API token."""
    name: str = "default"              # Human-readable label
    scope: list[str] = field(default_factory=lambda: ["*"])  # Allowed endpoints
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None  # None = never expires
    max_requests: Optional[int] = None  # None = unlimited
    request_count: int = 0

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def is_limit_reached(self) -> bool:
        if self.max_requests is None:
            return False
        return self.request_count >= self.max_requests

    def consume(self) -> bool:
        """Increment counter. Returns False if token should be rejected."""
        if self.is_expired():
            return False
        if self.is_limit_reached():
            return False
        self.request_count += 1
        return True

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "scope": self.scope,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "max_requests": self.max_requests,
            "request_count": self.request_count,
        }


# ── Token store (persisted to disk) ────────────────────────────

_PERSIST_PATH = Config.PROJECT_ROOT / ".panda_tokens.json"


class TokenStore:
    """
    Token store persisted to .panda_tokens.json (chmod 600).

    Tokens survive gateway restarts — essential on a VPS where the
    dashboard holds a session cookie tied to a generated token.
    Only SHA-256 hashes are stored, never the raw tokens.
    """

    def __init__(self) -> None:
        self._tokens: dict[str, TokenMeta] = {}
        self._load()

    def _load(self) -> None:
        """Load persisted tokens. A corrupt file starts fresh (never crash)."""
        try:
            if _PERSIST_PATH.exists():
                data = json.loads(_PERSIST_PATH.read_text(encoding="utf-8"))
                for hashed, meta_dict in data.items():
                    try:
                        self._tokens[hashed] = TokenMeta(**meta_dict)
                    except Exception:
                        continue
        except Exception:
            self._tokens = {}

    def _save(self) -> None:
        """Atomically persist hashes+metadata with restrictive permissions."""
        try:
            payload = {h: m.to_dict() for h, m in self._tokens.items()}
            tmp = _PERSIST_PATH.with_suffix(".tmp")
            tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            os.chmod(tmp, 0o600)
            os.replace(tmp, _PERSIST_PATH)
        except Exception:
            pass  # persistence is best-effort; auth still works in-memory

    def register(self, token: str, meta: TokenMeta | None = None) -> TokenMeta:
        """Register a new token. Returns its metadata."""
        hashed = hash_token(token)
        if meta is None:
            meta = TokenMeta()
        self._tokens[hashed] = meta
        self._save()
        return meta

    def validate(self, token: str) -> TokenMeta | None:
        """Validate a token. Returns metadata if valid, None otherwise."""
        hashed = hash_token(token)
        meta = self._tokens.get(hashed)
        if meta is None:
            return None
        if not meta.consume():
            return None
        return meta

    def revoke(self, token: str) -> bool:
        """Remove a token. Returns True if it existed."""
        hashed = hash_token(token)
        removed = self._tokens.pop(hashed, None) is not None
        if removed:
            self._save()
        return removed

    def list_tokens(self) -> list[dict]:
        """List all tokens (hashed keys + metadata)."""
        result = []
        for hashed, meta in self._tokens.items():
            result.append({
                "hash": hashed[:12] + "...",
                **meta.to_dict(),
            })
        return result

    def clear(self) -> None:
        """Remove all tokens."""
        self._tokens.clear()


# Global store instance
token_store = TokenStore()
