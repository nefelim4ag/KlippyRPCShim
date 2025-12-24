"""
Klippy RPC Shim - Client for Klipper's Unix socket API RPC interface.
"""

__version__ = "0.0.1"

from .shim import KlippyRPCShim

__all__ = ["KlippyRPCShim"]
