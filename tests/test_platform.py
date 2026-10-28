import platform

import pytest

from netscope.exceptions import UnsupportedPlatformError
from netscope.utils.platform import get_platform_name


@pytest.mark.parametrize(
    ("system_name", "expected"),
    [("Darwin", "darwin"), ("Linux", "linux"), ("Windows", "windows")],
)
def test_get_platform_name(monkeypatch, system_name: str, expected: str) -> None:
    monkeypatch.setattr(platform, "system", lambda: system_name)

    assert get_platform_name() == expected


def test_get_platform_name_rejects_unknown_system(monkeypatch) -> None:
    monkeypatch.setattr(platform, "system", lambda: "Plan 9")

    with pytest.raises(UnsupportedPlatformError, match="Unsupported platform: Plan 9"):
        get_platform_name()
