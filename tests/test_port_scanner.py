import socket

from netscope.diagnostics.port_scanner import scan_port
from netscope.models.target import Target


def test_open_port(monkeypatch) -> None:
    target = Target(
        value="example.com",
        target_type="hostname",
    )

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return None

    def fake_create_connection(address, timeout):
        return FakeConnection()

    monkeypatch.setattr(
        socket,
        "create_connection",
        fake_create_connection,
    )

    result = scan_port(target, 443)

    assert result.target == target
    assert result.port == 443
    assert result.open is True
    assert result.service == "https"
    assert result.error is None


def test_closed_port(monkeypatch) -> None:
    target = Target(
        value="example.com",
        target_type="hostname",
    )

    def fake_create_connection(address, timeout):
        raise ConnectionRefusedError("Connection refused")

    monkeypatch.setattr(
        socket,
        "create_connection",
        fake_create_connection,
    )

    result = scan_port(target, 9999)

    assert result.target == target
    assert result.port == 9999
    assert result.open is False
    assert result.service is None
    assert result.error is not None
