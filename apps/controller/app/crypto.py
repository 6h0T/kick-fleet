import base64
import hashlib
import json

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


def _fernet() -> Fernet:
    try:
        return Fernet(settings.fernet_key.encode())
    except ValueError:
        # Any passphrase works: derive a deterministic 32-byte Fernet key from it.
        # A generated key (Fernet.generate_key()) is used as-is.
        digest = hashlib.sha256(settings.fernet_key.encode()).digest()
        return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_json(payload: dict) -> bytes:
    return _fernet().encrypt(json.dumps(payload).encode())


def decrypt_json(blob: bytes) -> dict:
    try:
        return json.loads(_fernet().decrypt(blob).decode())
    except InvalidToken as exc:
        raise ValueError("credential blob cannot be decrypted with current FERNET_KEY") from exc
