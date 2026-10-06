"""Security helpers and validation utilities."""

import secrets
import hashlib


def generate_resumption_token(length: int = 32) -> str:
    """Generates a cryptographically secure URL-safe token for task resumption."""
    return secrets.token_urlsafe(length)


def hash_state(state_data: str) -> str:
    """Computes a SHA-256 integrity hash for serialized state checkpoints."""
    return hashlib.sha256(state_data.encode("utf-8")).hexdigest()
