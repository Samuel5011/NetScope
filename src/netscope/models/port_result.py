from dataclasses import dataclass
from typing import Literal

from netscope.models.target import Target


@dataclass
class PortResult:
    target: Target
    port: int
    open: bool
    state: Literal["open", "closed", "filtered", "error"]
    service: str | None = None
    error: str | None = None
