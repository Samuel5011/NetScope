import socket

import pytest

from netscope.diagnostics.port_scanner import scan_port, scan_ports
from netscope.exceptions import InvalidPortError
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
    assert result.state == "open"
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
    assert result.state == "closed"
    assert result.service is None
    assert result.error is None


def test_scan_ports_preserves_order(monkeypatch) -> None:
    target = Target(value="example.com", target_type="hostname")

    def refuse_connection(address, timeout):
        raise ConnectionRefusedError("Connection refused")

    monkeypatch.setattr(socket, "create_connection", refuse_connection)

    results = scan_ports(target, [443, 80], timeout=0.25)

    assert [result.port for result in results] == [443, 80]
    assert all(result.open is False for result in results)
    assert all(result.state == "closed" for result in results)


@pytest.mark.parametrize("port", [0, 65536])
def test_scan_port_rejects_out_of_range_port(port: int) -> None:
    target = Target(value="example.com", target_type="hostname")

    with pytest.raises(InvalidPortError):
        scan_port(target, port)


def test_scan_port_rejects_non_positive_timeout() -> None:
    target = Target(value="example.com", target_type="hostname")

    with pytest.raises(ValueError, match="Timeout must be greater than 0"):
        scan_port(target, 443, timeout=0)


def test_timed_out_port_is_filtered(monkeypatch) -> None:
    target = Target(value="example.com", target_type="hostname")

    def time_out(address, timeout):
        raise TimeoutError

    monkeypatch.setattr(socket, "create_connection", time_out)

    result = scan_port(target, 443)

    assert result.open is False
    assert result.state == "filtered"
    assert result.error == "Connection timed out"


def test_name_resolution_failure_is_an_error(monkeypatch) -> None:
    target = Target(value="missing.example", target_type="hostname")

    def fail_lookup(address, timeout):
        raise socket.gaierror("Name or service not known")

    monkeypatch.setattr(socket, "create_connection", fail_lookup)

    result = scan_port(target, 443)

    assert result.open is False
    assert result.state == "error"
    assert result.error == "Name resolution failed: Name or service not known"
