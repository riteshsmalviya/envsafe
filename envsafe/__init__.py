from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence, TypeVar
from urllib.parse import urlparse


T = TypeVar("T")


class EnvError(ValueError):
    """Raised when an environment variable is missing or invalid."""


class Env:
    """Helper for reading and validating environment variables.

    Parameters
    ----------
    source:
        Mapping to read variables from. Defaults to ``os.environ``.
        Useful for testing.
    """

    def __init__(self, source: Optional[Mapping[str, str]] = None) -> None:
        self._source: Mapping[str, str] = source or os.environ

    # ------------------------------------------------------------------ #
    # Core helper
    # ------------------------------------------------------------------ #

    def _get_raw(
        self,
        key: str,
        *,
        default: Any = None,
        required: bool = False,
    ) -> Any:
        if key in self._source:
            return self._source[key]

        if required:
            raise EnvError(f"Missing required environment variable: {key}")

        return default

    # ------------------------------------------------------------------ #
    # Basic types
    # ------------------------------------------------------------------ #

    def str(
        self,
        key: str,
        *,
        default: Optional[str] = None,
        required: bool = False,
        allow_empty: bool = False,
    ) -> Optional[str]:
        raw = self._get_raw(key, default=default, required=required)

        if raw is None:
            return None

        value = str(raw)
        if not allow_empty and value == "":
            raise EnvError(f"{key} must not be empty")

        return value

    def int(
        self,
        key: str,
        *,
        default: Optional[int] = None,
        required: bool = False,
        min: Optional[int] = None,
        max: Optional[int] = None,
    ) -> Optional[int]:
        raw = self._get_raw(key, default=default, required=required)

        if raw is None:
            return None

        try:
            value = int(raw)
        except (TypeError, ValueError):
            raise EnvError(f"{key} must be an integer, got {raw!r}")

        if min is not None and value < min:
            raise EnvError(f"{key} must be >= {min}, got {value}")
        if max is not None and value > max:
            raise EnvError(f"{key} must be <= {max}, got {value}")

        return value

    def float(
        self,
        key: str,
        *,
        default: Optional[float] = None,
        required: bool = False,
        min: Optional[float] = None,
        max: Optional[float] = None,
    ) -> Optional[float]:
        raw = self._get_raw(key, default=default, required=required)

        if raw is None:
            return None

        try:
            value = float(raw)
        except (TypeError, ValueError):
            raise EnvError(f"{key} must be a float, got {raw!r}")

        if min is not None and value < min:
            raise EnvError(f"{key} must be >= {min}, got {value}")
        if max is not None and value > max:
            raise EnvError(f"{key} must be <= {max}, got {value}")

        return value

    def bool(
        self,
        key: str,
        *,
        default: Optional[bool] = None,
        required: bool = False,
    ) -> Optional[bool]:
        raw = self._get_raw(key, default=default, required=required)

        if raw is None:
            return None

        if isinstance(raw, bool):
            return raw

        value_str = str(raw).strip().lower()

        truthy = {"1", "true", "t", "yes", "y", "on"}
        falsy = {"0", "false", "f", "no", "n", "off"}

        if value_str in truthy:
            return True
        if value_str in falsy:
            return False

        allowed = sorted(truthy | falsy)
        raise EnvError(
            f"{key} must be a boolean (one of {allowed}), got {raw!r}"
        )

    # ------------------------------------------------------------------ #
    # Higher-level helpers
    # ------------------------------------------------------------------ #

    def url(
        self,
        key: str,
        *,
        default: Optional[str] = None,
        required: bool = False,
        schemes: Optional[Sequence[str]] = None,
    ) -> Optional[str]:
        raw = self._get_raw(key, default=default, required=required)

        if raw is None:
            return None

        value = str(raw)
        parsed = urlparse(value)

        if not (parsed.scheme and parsed.netloc):
            raise EnvError(f"{key} must be a valid URL, got {value!r}")

        if schemes is not None and parsed.scheme not in schemes:
            allowed = ", ".join(schemes)
            raise EnvError(
                f"{key} must use one of schemes [{allowed}], got {parsed.scheme!r}"
            )

        return value

    def choice(
        self,
        key: str,
        *,
        choices: Iterable[str],
        default: Optional[str] = None,
        required: bool = False,
        case_sensitive: bool = False,
    ) -> Optional[str]:
        raw = self._get_raw(key, default=default, required=required)

        if raw is None:
            return None

        value = str(raw)
        options = list(choices)

        if not options:
            raise EnvError(f"{key}: choices must not be empty")

        if not case_sensitive:
            value_cmp = value.lower()
            options_cmp = [c.lower() for c in options]
        else:
            value_cmp = value
            options_cmp = options

        if value_cmp not in options_cmp:
            raise EnvError(f"{key} must be one of {options}, got {value!r}")

        if not case_sensitive:
            index = options_cmp.index(value_cmp)
            return options[index]

        return value

    def list(
        self,
        key: str,
        *,
        default: Optional[Sequence[str]] = None,
        required: bool = False,
        separator: str = ",",
        strip: bool = True,
        allow_empty_items: bool = False,
    ) -> Optional[list[str]]:
        raw = self._get_raw(key, default=None, required=required)

        if raw is None:
            if default is None:
                return None
            return list(default)

        value = str(raw)
        if value == "":
            return [] if default is None else list(default)

        parts = value.split(separator)
        result: list[str] = []

        for part in parts:
            item = part.strip() if strip else part
            if not allow_empty_items and item == "":
                continue
            result.append(item)

        return result

    # ------------------------------------------------------------------ #
    # Advanced types
    # ------------------------------------------------------------------ #

    def json(
        self,
        key: str,
        *,
        default: Any = None,
        required: bool = False,
    ) -> Any:
        """Parse a JSON string from environment variable.
        
        Example:
            CONFIG='{"debug": true, "port": 8080}'
            env.json("CONFIG")  # -> {"debug": True, "port": 8080}
        """
        raw = self._get_raw(key, default=None, required=required)

        if raw is None:
            return default

        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise EnvError(f"{key} must be valid JSON: {e}")

    def path(
        self,
        key: str,
        *,
        default: Optional[str] = None,
        required: bool = False,
        must_exist: bool = False,
        must_be_file: bool = False,
        must_be_dir: bool = False,
        resolve: bool = False,
    ) -> Optional[Path]:
        """Parse a file system path from environment variable.
        
        Example:
            LOG_DIR="/var/log/myapp"
            env.path("LOG_DIR", must_be_dir=True)  # -> Path("/var/log/myapp")
        """
        raw = self._get_raw(key, default=default, required=required)

        if raw is None:
            return None

        path = Path(raw)
        
        if resolve:
            path = path.resolve()

        if must_exist and not path.exists():
            raise EnvError(f"{key}: path does not exist: {path}")

        if must_be_file and not path.is_file():
            raise EnvError(f"{key}: not a file: {path}")

        if must_be_dir and not path.is_dir():
            raise EnvError(f"{key}: not a directory: {path}")

        return path

    def email(
        self,
        key: str,
        *,
        default: Optional[str] = None,
        required: bool = False,
    ) -> Optional[str]:
        """Parse and validate an email address.
        
        Example:
            ADMIN_EMAIL="admin@example.com"
            env.email("ADMIN_EMAIL")  # -> "admin@example.com"
        """
        raw = self._get_raw(key, default=default, required=required)

        if raw is None:
            return None

        value = str(raw).strip()
        
        # Simple email regex pattern
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        
        if not re.match(pattern, value):
            raise EnvError(f"{key} must be a valid email address, got {value!r}")

        return value

    def port(
        self,
        key: str,
        *,
        default: Optional[int] = None,
        required: bool = False,
    ) -> Optional[int]:
        """Parse a port number (1-65535).
        
        Example:
            PORT="8080"
            env.port("PORT")  # -> 8080
        """
        return self.int(key, default=default, required=required, min=1, max=65535)

    def regex(
        self,
        key: str,
        *,
        pattern: str,
        default: Optional[str] = None,
        required: bool = False,
        flags: int = 0,
    ) -> Optional[str]:
        """Validate string matches a regex pattern.
        
        Example:
            API_KEY="sk-abc123"
            env.regex("API_KEY", pattern=r"^sk-[a-z0-9]+$")
        """
        raw = self._get_raw(key, default=default, required=required)

        if raw is None:
            return None

        value = str(raw)
        
        if not re.match(pattern, value, flags):
            raise EnvError(f"{key} must match pattern {pattern!r}, got {value!r}")

        return value

    def bytes(
        self,
        key: str,
        *,
        default: Optional[int] = None,
        required: bool = False,
    ) -> Optional[int]:
        """Parse byte size strings like '10MB', '1GB', '500KB'.
        
        Example:
            MAX_UPLOAD="10MB"
            env.bytes("MAX_UPLOAD")  # -> 10485760 (bytes)
        """
        raw = self._get_raw(key, default=default, required=required)

        if raw is None:
            return None

        if isinstance(raw, int):
            return raw

        value = str(raw).strip().upper()
        
        units = {
            "B": 1,
            "KB": 1024,
            "MB": 1024 ** 2,
            "GB": 1024 ** 3,
            "TB": 1024 ** 4,
            "K": 1024,
            "M": 1024 ** 2,
            "G": 1024 ** 3,
            "T": 1024 ** 4,
        }
        
        # Try to parse number with unit
        pattern = r"^(\d+(?:\.\d+)?)\s*(B|KB|MB|GB|TB|K|M|G|T)?$"
        match = re.match(pattern, value)
        
        if not match:
            raise EnvError(
                f"{key} must be a byte size (e.g., '10MB', '1GB'), got {raw!r}"
            )

        number = float(match.group(1))
        unit = match.group(2) or "B"
        
        return int(number * units[unit])

    def duration(
        self,
        key: str,
        *,
        default: Optional[float] = None,
        required: bool = False,
    ) -> Optional[float]:
        """Parse duration strings like '30s', '5m', '2h' into seconds.
        
        Example:
            TIMEOUT="30s"
            env.duration("TIMEOUT")  # -> 30.0 (seconds)
        """
        raw = self._get_raw(key, default=default, required=required)

        if raw is None:
            return None

        if isinstance(raw, (int, float)):
            return float(raw)

        value = str(raw).strip().lower()
        
        units = {
            "ms": 0.001,
            "s": 1,
            "m": 60,
            "h": 3600,
            "d": 86400,
        }
        
        pattern = r"^(\d+(?:\.\d+)?)\s*(ms|s|m|h|d)?$"
        match = re.match(pattern, value)
        
        if not match:
            raise EnvError(
                f"{key} must be a duration (e.g., '30s', '5m', '2h'), got {raw!r}"
            )

        number = float(match.group(1))
        unit = match.group(2) or "s"
        
        return number * units[unit]

    def custom(
        self,
        key: str,
        parser: Callable[[str], T],
        *,
        default: Optional[T] = None,
        required: bool = False,
    ) -> Optional[T]:
        """Parse using a custom function.
        
        Example:
            def parse_date(s):
                return datetime.strptime(s, "%Y-%m-%d")
            
            env.custom("START_DATE", parse_date)
        """
        raw = self._get_raw(key, default=None, required=required)

        if raw is None:
            return default

        try:
            return parser(str(raw))
        except Exception as e:
            raise EnvError(f"{key}: custom parser failed: {e}")


def load_dotenv(
    path: str | Path = ".env",
    *,
    override: bool = False,
    encoding: str = "utf-8",
) -> dict[str, str]:
    """Load environment variables from a .env file.
    
    Parameters
    ----------
    path:
        Path to the .env file. Defaults to ".env" in current directory.
    override:
        If True, override existing environment variables.
    encoding:
        File encoding. Defaults to "utf-8".
    
    Returns
    -------
    dict:
        Dictionary of loaded variables.
    
    Example:
        from envsafe import load_dotenv, env
        
        load_dotenv()  # Load from .env
        
        DEBUG = env.bool("DEBUG")
    """
    env_path = Path(path)
    loaded: dict[str, str] = {}
    
    if not env_path.exists():
        return loaded
    
    with open(env_path, encoding=encoding) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            
            # Handle export prefix
            if line.startswith("export "):
                line = line[7:].strip()
            
            # Find the = sign
            if "=" not in line:
                continue
            
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            
            # Remove quotes
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            
            # Handle escape sequences in double-quoted strings
            if value.startswith('"'):
                value = value.encode().decode("unicode_escape")
            
            loaded[key] = value
            
            # Set in os.environ
            if override or key not in os.environ:
                os.environ[key] = value
    
    return loaded


# Default instance, similar to 'os.environ'
env = Env()

__all__ = ["Env", "EnvError", "env", "load_dotenv"]
