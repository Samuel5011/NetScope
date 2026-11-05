# NetScope architecture

NetScope keeps command-line handling, network operations, result data, and report formatting separate.

```text
CLI and validation
       │
       ├── DNS resolver ─────────┐
       ├── Ping runner ──────────┤
       ├── Traceroute runner ────┼── Result models ── Report service
       └── TCP port scanner ─────┤                         │
                                └── Diagnostic service ────┘
```

## CLI

`src/netscope/cli.py` defines the user-facing commands:

- `netscope dns`
- `netscope ping`
- `netscope trace`
- `netscope scan`
- `netscope diagnose`

The CLI validates targets, port specifications, hop limits, and timeouts before invoking a diagnostic. Existing commands retain concise terminal output and can emit structured reports with `--json`. The combined command uses the full text report by default.

## Diagnostics

Modules in `src/netscope/diagnostics` perform one network operation each:

- `dns.py` uses `socket.getaddrinfo()` and can return IPv4 or IPv6 addresses.
- `ping.py` runs the platform ping command and parses Unix and Windows summaries.
- `traceroute.py` runs `traceroute` or `tracert` and parses individual hops.
- `port_scanner.py` attempts TCP connections and classifies ports as open, closed, timeout, or error. A timeout remains distinct because it does not confirm firewall filtering.

External commands are passed as argument lists without a shell. `utils/subprocess_runner.py` normalizes timeouts, missing executables, permission problems, and other operating-system errors.

## Models

Dataclasses in `src/netscope/models` hold diagnostic data independently of terminal formatting:

- `Target`
- `DNSResult`
- `PingResult`
- `TraceHop` and `TraceResult`
- `PortResult`
- `DiagnosticReport`

This separation lets the same result feed human-readable output, JSON output, or a combined report.

## Services

`diagnostic_service.py` runs DNS, ping, traceroute, and TCP scanning for the combined command. Each operation is isolated so an unexpected failure becomes an error result without preventing the remaining checks from running.

`report_service.py` creates timestamped reports and formats them as terminal text or a stable JSON object. Diagnostics that were not requested appear as `null` in JSON; the port collection is always an array.

## Platform boundaries

Platform selection is isolated in `utils/platform.py`. IPv4 uses `ping` and `traceroute` on macOS and Linux. IPv6 uses `ping6` and `traceroute6` on macOS, while Linux uses the utilities' `-6` flag. Windows uses `ping` and `tracert` with the appropriate count, family, hop, and timeout flags. Unsupported systems return a clear diagnostic error instead of falling back to an incompatible command.

Traceroute has a 60-second overall limit. If that limit is reached, partial hop output is retained and the result is marked unsuccessful with a timeout error.
