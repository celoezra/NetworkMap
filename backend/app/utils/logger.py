import logging
import os
import re
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "networkmap.log"

class SensitiveFilter(logging.Filter):
    """Filters out any potential database keys, tokens, or raw secrets from logs."""
    def filter(self, record):
        msg = str(record.msg)
        # Redact PRAGMA key lines
        if "PRAGMA key" in msg or "DATABASE_KEY" in msg:
            record.msg = re.sub(r"PRAGMA key\s*=\s*'[^']+'", "PRAGMA key = '***REDACTED***'", msg)
            record.msg = re.sub(r"NETWORKMAP_DB_KEY=[^\s]+", "NETWORKMAP_DB_KEY=***REDACTED***", record.msg)
        return True

def setup_logger():
    logger = logging.getLogger("networkmap")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s")
        
        # File Handler
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.addFilter(SensitiveFilter())
        logger.addHandler(file_handler)
        
        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.addFilter(SensitiveFilter())
        logger.addHandler(console_handler)
        
    return logger

logger = setup_logger()
