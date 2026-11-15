"""Authenticated messages for Mike's loopback control channel."""

import hashlib
import hmac
import secrets


class ControlMessageCodec:
    """Sign and verify the sensitive commands sent over Mike's UDP socket."""

    _HEADER = b"MIKE/1"
    _ALLOWED_COMMANDS = frozenset({b"KILL_MIC", b"WAKE_MIC"})

    def __init__(self, secret: bytes):
        if not isinstance(secret, bytes) or len(secret) < 32:
            raise ValueError("Control secret must contain at least 32 bytes")
        self._secret = secret
        self._seen_nonces = set()

    def encode(self, command: bytes) -> bytes:
        if not isinstance(command, bytes) or command not in self._ALLOWED_COMMANDS:
            raise ValueError("Unsupported control command")

        nonce = secrets.token_bytes(16)
        content = b" ".join((self._HEADER, command, nonce.hex().encode("ascii")))
        signature = hmac.new(self._secret, content, hashlib.sha256).hexdigest()
        return content + b" " + signature.encode("ascii")

    def decode(self, message: bytes):
        if not isinstance(message, bytes):
            return None

        parts = message.split(b" ")
        if len(parts) != 4 or parts[0] != self._HEADER:
            return None

        _, command, nonce_text, signature = parts
        if command not in self._ALLOWED_COMMANDS:
            return None
        if len(nonce_text) != 32 or len(signature) != 64:
            return None
        if any(char not in b"0123456789abcdef" for char in nonce_text):
            return None

        nonce = bytes.fromhex(nonce_text.decode("ascii"))
        content = b" ".join((self._HEADER, command, nonce_text))
        expected = hmac.new(self._secret, content, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected.encode("ascii")):
            return None
        if nonce in self._seen_nonces:
            return None

        self._seen_nonces.add(nonce)
        return command
