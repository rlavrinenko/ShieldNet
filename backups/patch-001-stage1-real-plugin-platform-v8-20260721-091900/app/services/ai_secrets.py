import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class AISecretService:
    @staticmethod
    def _fernet() -> Fernet:
        material = settings.ai_credentials_master_key or settings.secret_key
        digest = hashlib.sha256(material.encode("utf-8")).digest()
        return Fernet(base64.urlsafe_b64encode(digest))

    @classmethod
    def encrypt(cls, value: str) -> str:
        return cls._fernet().encrypt(value.encode("utf-8")).decode("ascii")

    @classmethod
    def decrypt(cls, value: str) -> str:
        try:
            return cls._fernet().decrypt(value.encode("ascii")).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Unable to decrypt AI provider credential") from exc

    @staticmethod
    def hint(value: str) -> str:
        if len(value) <= 8:
            return "••••"
        return f"{value[:4]}••••{value[-4:]}"
