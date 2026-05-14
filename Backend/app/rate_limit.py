"""
Shared slowapi Limiter instance.

Defining it at module scope (rather than inside `create_app`) lets routers
import it and apply per-route decorators that the middleware in main.py
will then enforce.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

# Per-IP keying. `default_limits=[]` means no global limit; opt-in per route.
limiter = Limiter(key_func=get_remote_address, default_limits=[])
