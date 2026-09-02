import os
import hashlib
import uuid

def hash_password(password: str) -> str:
    """Hashes a password using PBKDF2 with SHA-256 and a random salt."""
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ":" + pwd_hash.hex()

def verify_password(password: str, stored_hash: str) -> bool:
    """Verifies a plain password against the stored salt:hash string."""
    try:
        salt_hex, hash_hex = stored_hash.split(":")
        salt = bytes.fromhex(salt_hex)
        candidate_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return candidate_hash.hex() == hash_hex
    except Exception as e:
        print("Password verify error:", e)
        return False

def generate_session_token(user_id: str) -> str:
    """Generates a secure session token."""
    return f"token_{user_id}_{uuid.uuid4().hex}"
