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
    # 1. Organization level fallback key for database import compatibility across authorized branches
    org_key = os.getenv("ORGANIZATION_DB_KEY")
    if org_key:
        return org_key
        
    # 2. Environment variable override if provided
    env_key = os.getenv("NETWORKMAP_DB_KEY")
    if env_key:
        return env_key

    # 3. Secure Keystore Strategy (e.g., Windows DPAPI / Linux Secret Service)
    # This serves as a placeholder for production implementation.
    # In production, use `keyring` or `cryptography` to securely retrieve from OS.
    # try:
    #     import keyring
    #     os_key = keyring.get_password("networkmap", "db_master_key")
    #     if os_key:
    #         return os_key
    # except Exception as e:
    #     logger.warning(f"Could not retrieve key from OS Keyring: {e}")

    # 4. Local Keyfile strategy with restricted permissions (Development fallback)
    if SECRET_KEY_FILE.exists():
        try:
            with open(SECRET_KEY_FILE, "r", encoding="utf-8") as f:
                key = f.read().strip()
                if key:
                    return key
        except Exception as e:
            logger.error(f"Error reading DB key file: {e}")

    # Generate new random 64-character hex key if not found anywhere
    new_key = os.urandom(32).hex()
    try:
        # In production, save to secure keystore:
        # try:
        #     import keyring
        #     keyring.set_password("networkmap", "db_master_key", new_key)
        # except ...

        SECRET_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SECRET_KEY_FILE, "w", encoding="utf-8") as f:
            f.write(new_key)
        
        if sys.platform != "win32":
            os.chmod(SECRET_KEY_FILE, 0o600)
        logger.info("Generated new encrypted database master key.")
    except Exception as e:
        logger.error(f"Failed to persist DB encryption key: {e}")

    return new_key
