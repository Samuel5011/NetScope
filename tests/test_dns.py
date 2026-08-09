import socket

from netscope.diagnostics.dns import resolve_dns
from netscope.models.target import Target


def test_dns_lookup_success(monkeypatch) -> None:

    target = Target(
        value="google.com",
        target_type="hostname",
    )

    def fake_gethostbyname(hostname: str) -> str:
        return "142.250.190.78"

    monkeypatch.setattr(socket, "gethostbyname", fake_gethostbyname)
    result = resolve_dns(target)

    assert result.success is True
    assert result.ip_address == "142.250.190.78"
    assert result.target == target
    assert result.error is None
    assert result.response_time_ms >= 0
