import re
import secrets
from datetime import datetime, timezone

def sanitize_path_component(component: str) -> str:
    """
    Sanitizes path components to prevent directory traversal (../) and illegal characters.
    """
    if not component:
        return "default"
    
    cleaned = component.replace("..", "")
    cleaned = re.sub(r"[/\\]", "", cleaned)
    cleaned = re.sub(r"[\x00-\x1F\x7F]", "", cleaned)
    cleaned = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", cleaned)
    
    return cleaned.lower().strip() or "default"

def generate_secure_filename(original_filename: str, fallback_ext: str = "csv") -> str:
    """
    Generates a collision-resistant, secure filename using timestamps and random entropy.
    """
    raw_ext = original_filename.split(".")[-1].lower() if "." in original_filename else fallback_ext
    safe_ext = raw_ext if safe_ext_check(raw_ext) else fallback_ext
    
    base_name = original_filename.rsplit(".", 1)[0] if "." in original_filename else original_filename
    clean_base = sanitize_path_component(base_name)[:50] or "dataset"
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    random_entropy = secrets.token_hex(4)
    
    return f"{timestamp}_{random_entropy}_{clean_base}.{safe_ext}"

def safe_ext_check(ext: str) -> bool:
    return ext in {"csv", "xls", "xlsx", "json", "tsv", "txt", "parquet"}

# Prompt injection patterns (system prompt override / jailbreak attempts)
PROMPT_INJECTION_PATTERNS = [
    re.compile(r'(?i)\b(ignore|disregard|forget|override|bypass)\s+(all\s+)?(previous|prior|above|system)\s+(instructions|prompts|rules|commands)\b'),
    re.compile(r'(?i)\b(you\s+are\s+now|act\s+as|pretend\s+to\s+be)\s+(DAN|jailbroken|unfiltered|root|admin)\b'),
    re.compile(r'(?i)<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>'),
    re.compile(r'(?i)!\[.*?\]\(https?:\/\/[^\s\)]+\)'),  # Markdown image exfiltration
    re.compile(r'(?i)\b(reveal|output|print|show)\s+(system\s+prompt|instructions|secret\s+key|api_key)\b')
]

def sanitize_prompt_input(query: str) -> str:
    """
    Sanitizes user queries to neutralize prompt injection, jailbreak attempts, and script tags.
    """
    if not query:
        return ""
    
    cleaned = query.strip()
    for pattern in PROMPT_INJECTION_PATTERNS:
        cleaned = pattern.sub("[FILTERED_INPUT]", cleaned)
        
    return cleaned

def sanitize_csv_cell(val: object) -> object:
    """
    Sanitizes tabular cell values to prevent CSV / Spreadsheet Formula Injection (OWASP DDE Attacks).
    Escapes leading '=', '+', '-', '@', '\t', '\r' with a leading single quote.
    """
    if isinstance(val, str):
        if val.startswith(("=", "+", "-", "@", "\t", "\r")):
            return "'" + val
    return val
