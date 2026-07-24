"""Conector Ruvic de seguridad DNS y filtrado web para Cisco Umbrella."""

from .client import UmbrellaClient
from .config import ENV_PREFIX, UmbrellaConfig
from .exceptions import (
    UmbrellaAuthError,
    UmbrellaConnectorError,
    UmbrellaDataError,
    UmbrellaNetworkError,
)
from .logging_utils import setup_logging

__all__ = [
    "ENV_PREFIX",
    "UmbrellaAuthError",
    "UmbrellaClient",
    "UmbrellaConfig",
    "UmbrellaConnectorError",
    "UmbrellaDataError",
    "UmbrellaNetworkError",
    "setup_logging",
]

__version__ = "1.0.0"
