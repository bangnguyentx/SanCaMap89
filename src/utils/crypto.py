import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

def derive_key(password: str, salt: bytes = None) -> bytes:
    """Derive a key from password using PBKDF2."""
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key

def encrypt_seed(seed: str, encryption_key: str) -> str:
    """Encrypt a server seed."""
    key = derive_key(encryption_key)
    fernet = Fernet(key)
    encrypted = fernet.encrypt(seed.encode())
    return base64.urlsafe_b64encode(encrypted).decode()

def decrypt_seed(encrypted_seed: str, encryption_key: str) -> str:
    """Decrypt a server seed."""
    key = derive_key(encryption_key)
    fernet = Fernet(key)
    encrypted_bytes = base64.urlsafe_b64decode(encrypted_seed.encode())
    decrypted = fernet.decrypt(encrypted_bytes)
    return decrypted.decode()
