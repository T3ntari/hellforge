"""
AES-256-GCM encryption for .ee files.
Uses PyCryptodome if available, falls back to SHA-256 + XOR with random salt.
"""

import hashlib
import os
import json

try:
    from Crypto.Cipher import AES
    from Crypto.Protocol.KDF import scrypt
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False


def register_encryptor(register_fn):
    register_fn("aes-gcm", encrypt, decrypt)


def _derive_key(password: str, salt: bytes = None) -> tuple:
    """Derive a 256-bit key using scrypt or PBKDF2."""
    if salt is None:
        salt = os.urandom(32)

    if HAS_CRYPTO:
        key = scrypt(password.encode(), salt, 32, N=2**17, r=8, p=1)
    else:
        # Fallback: multiple rounds of SHA-256
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600000, dklen=32)

    return key, salt


def encrypt(data: bytes, password: str = "e-lang-default") -> bytes:
    """Encrypt data using AES-256-GCM."""
    salt = os.urandom(32)

    if HAS_CRYPTO:
        key, _ = _derive_key(password, salt)
        cipher = AES.new(key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        nonce = cipher.nonce
        # Format: salt(32) + nonce(16) + tag(16) + ciphertext
        return salt + nonce + tag + ciphertext
    else:
        key, _ = _derive_key(password, salt)
        # XOR cipher with random stream derived from key
        import hashlib as h
        stream = b""
        counter = 0
        while len(stream) < len(data):
            stream += h.sha256(key + counter.to_bytes(4, "big")).digest()
            counter += 1
        stream = stream[:len(data)]
        encrypted = bytes(a ^ b for a, b in zip(data, stream))
        return salt + encrypted


def decrypt(data: bytes, password: str = "e-lang-default") -> bytes:
    """Decrypt data encrypted with encrypt()."""
    salt = data[:32]
    rest = data[32:]

    if HAS_CRYPTO and len(rest) > 32:
        try:
            key, _ = _derive_key(password, salt)
            nonce = rest[:16]
            tag = rest[16:32]
            ciphertext = rest[32:]
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            return cipher.decrypt_and_verify(ciphertext, tag)
        except Exception:
            pass  # Fall through to XOR fallback

    # XOR fallback
    key, _ = _derive_key(password, salt)
    stream = b""
    counter = 0
    target_len = len(rest)
    import hashlib as h
    while len(stream) < target_len:
        stream += h.sha256(key + counter.to_bytes(4, "big")).digest()
        counter += 1
    stream = stream[:target_len]
    return bytes(a ^ b for a, b in zip(rest, stream))
