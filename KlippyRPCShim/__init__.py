"""
Klippy RPC Shim - Client for Klipper's Unix socket API RPC interface.
"""

__version__ = "0.0.2"

from .shim import KlippyRPCShim as KlippyRPCShim
from .exceptions import SocketClosed

__all__ = [
    "KlippyRPCShim",
    "SocketClosed"
]
