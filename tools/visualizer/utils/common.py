"""
Common utilities for the visualizer package.

Provides shared functions and imports to reduce redundancy across modules.
"""

import hashlib
import json
import time
import uuid
from datetime import datetime
from pathlib import Path

from .types import Dict, Any, Optional


def generate_uuid() -> str:
    """Generate a unique identifier string."""
    return str(uuid.uuid4())


def hash_string(text: str) -> str:
    """Generate SHA-256 hash of a string."""
    return hashlib.sha256(text.encode()).hexdigest()


def get_timestamp() -> float:
    """Get current Unix timestamp."""
    return time.time()


def get_formatted_timestamp() -> str:
    """Get formatted timestamp string."""
    return datetime.now().isoformat()


def serialize_json(data: Any) -> str:
    """Safely serialize data to JSON string."""
    try:
        return json.dumps(data, default=str, indent=2)
    except (TypeError, ValueError) as e:
        return json.dumps({"error": f"Serialization failed: {str(e)}"})


def deserialize_json(json_str: str) -> Optional[Any]:
    """Safely deserialize JSON string to data."""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return None


def safe_path_join(*parts: str) -> Path:
    """Safely join path components."""
    return Path(*parts).resolve()


def ensure_directory(path: Path) -> Path:
    """Ensure directory exists, create if necessary."""
    path.mkdir(parents=True, exist_ok=True)
    return path


__all__ = [
    'generate_uuid', 'hash_string', 'get_timestamp', 'get_formatted_timestamp',
    'serialize_json', 'deserialize_json', 'safe_path_join', 'ensure_directory'
]