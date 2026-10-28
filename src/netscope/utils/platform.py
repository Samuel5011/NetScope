import platform
from typing import Literal

from netscope.exceptions import UnsupportedPlatformError

PlatformName = Literal["darwin", "linux", "windows"]


def get_platform_name() -> PlatformName:
    """Return the normalized name of a supported operating system."""
    name = platform.system().lower()
    if name == "darwin":
        return "darwin"
    if name == "linux":
        return "linux"
    if name == "windows":
        return "windows"

    display_name = platform.system() or "unknown"
    raise UnsupportedPlatformError(f"Unsupported platform: {display_name}")
