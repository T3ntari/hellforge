"""
Custom encryption — double XOR with SHA-256 key.
Place in encryption/ directory. Auto-loaded at startup.
"""

import hashlib


def register_encryptor(register_fn):
    """Register this encryptor with the core system."""
    register_fn("custom_xor", encrypt, decrypt)


def _derive_key(key: str, salt: bytes = b"E-LANG-SALT") -> bytes:
    """Derive a stronger key using SHA-256."""
    return hashlib.sha256(key.encode() + salt).digest()


def encrypt(data: bytes, key: str = "default") -> bytes:
    """Encrypt: XOR with derived key twice."""
    k = _derive_key(key)
    # First pass
    result = bytearray(len(data))
    for i in range(len(data)):
        result[i] = data[i] ^ k[i % len(k)]
    # Second pass with shifted key
    k2 = k[::-1]
    for i in range(len(result)):
        result[i] ^= k2[i % len(k2)]
    return bytes(result)


def decrypt(data: bytes, key: str = "default") -> bytes:
    """Decrypt: same operation (XOR is symmetric)."""
    return encrypt(data, key)
