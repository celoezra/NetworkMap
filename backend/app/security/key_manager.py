import os
import sys
import logging
from pathlib import Path

logger = logging.getLogger("networkmap.security")

# Key storage path fallback for persistent key simulation if OS keyrings are unavailable
SECRET_KEY_FILE = Path("data/.db_key")

def get_or_create_database_key() -> str:
    """
    Retrieves or generates a strong encryption key for SQLCipher.
    In Windows/Linux environments, this can abstract to OS Keychain / DPAPI / SecretService.
    To prevent hardcoding in code, the key is securely managed per instance.
    """
    # 1. Environment variable override if provided
    env_key = os.getenv("NETWORKMAP_DB_KEY")
    if env_key:
        return env_key

    # 2. Keyfile strategy with restricted permissions
    if SECRET_KEY_FILE.exists():
        try:
            with open(SECRET_KEY_FILE, "r", encoding="utf-8") as f:
                key = f.read().strip()
                if key:
                    return key
        except Exception as e:
            logger.error(f"Error reading DB key file: {e}")

    # Generate new random 64-character hex key
    new_key = os.urandom(32).hex()
    try:
        SECRET_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SECRET_KEY_FILE, "w", encoding="utf-8") as f:
            f.write(new_key)
        # Restrict permissions on Unix-like systems if possible
        if sys.platform != "win32":
            os.chmod(SECRET_KEY_FILE, 0o600)
        logger.info("Generated new encrypted database master key.")
    except Exception as e:
        logger.error(f"Failed to persist DB encryption key: {e}")

    return new_key
