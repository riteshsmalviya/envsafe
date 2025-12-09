from __future__ import annotations

import os
from typing import Any, Iterable, Mapping, Optional, Sequence
from urllib.parse import urlparse


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


# Default instance, similar to 'os.environ'
env = Env()

__all__ = ["Env", "EnvError", "env"]
