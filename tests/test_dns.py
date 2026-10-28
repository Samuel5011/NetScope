import socket

from netscope.diagnostics.dns import resolve_dns
from netscope.models.target import Target


def test_dns_lookup_success(monkeypatch) -> None:

    target = Target(
        value="google.com",
        target_type="hostname",
    )

    def fake_getaddrinfo(hostname, port, family, type):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("142.250.190.78", 0))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    result = resolve_dns(target)

    assert result.success is True
    assert result.ip_address == "142.250.190.78"
    assert result.target == target
    assert result.error is None
    assert result.response_time_ms >= 0


def test_dns_lookup_supports_ipv6(monkeypatch) -> None:
    target = Target(value="example.com", target_type="hostname")

    def fake_getaddrinfo(hostname, port, family, type):
        return [
            (
                socket.AF_INET6,
                socket.SOCK_STREAM,
                6,
                "",
                ("2001:db8::1", 0, 0, 0),
            )
        ]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)

    result = resolve_dns(target)

    assert result.success is True
    assert result.ip_address == "2001:db8::1"


def test_dns_lookup_failure(monkeypatch) -> None:
    target = Target(value="missing.example", target_type="hostname")

    def fail_lookup(*args, **kwargs):
        raise socket.gaierror("Name or service not known")

    monkeypatch.setattr(socket, "getaddrinfo", fail_lookup)

    result = resolve_dns(target)

    assert result.success is False
    assert result.ip_address is None
    assert result.error == "Name or service not known"
