import re
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict

SECRET_PATTERNS = [
    (re.compile(r'Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*', re.IGNORECASE), "Bearer [MASKED_JWT]"),
    (re.compile(r'nvapi-[A-Za-z0-9_\-]{16,}', re.IGNORECASE), "nvapi-[MASKED_KEY]"),
    (re.compile(r'eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]+', re.IGNORECASE), "[MASKED_JWT]"),
    (re.compile(r'(?i)(password|secret|service_role_key|api_key)["\']?\s*[:=]\s*["\']([^"\']+)["\']'), r'\1: "[MASKED]"')
]

def mask_secrets(text: str) -> str:
    """Scans and masks sensitive API keys, tokens, and credentials in log text."""
    if not text:
        return text
    masked = str(text)
    for pattern, replacement in SECRET_PATTERNS:
        masked = pattern.sub(replacement, masked)
    return masked

class JSONLogFormatter(logging.Formatter):
    """
    Formatter that outputs structured JSON logs with automated secret scrubbing.
    """
    def format(self, record: logging.LogRecord) -> str:
        msg = mask_secrets(record.getMessage())
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": msg,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Include extra attributes if passed
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "method"):
            log_data["method"] = record.method
            
        if record.exc_info:
            log_data["exception"] = mask_secrets(self.formatException(record.exc_info))
            
        return json.dumps(log_data)

def setup_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """
    Configures global logging for the application.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if log_format.lower() == "json":
        handler.setFormatter(JSONLogFormatter())
    else:
        text_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] %(message)s"
        )
        handler.setFormatter(text_formatter)

    root_logger.addHandler(handler)

def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance for a given module name.
    """
    return logging.getLogger(name)
