# NetScope

NetScope is a Python command-line toolkit for network troubleshooting and connectivity checks.

## Features

- Hostname, IPv4, and IPv6 target validation
- DNS resolution with response timing
- Ping reachability, latency, and packet-loss reporting
- Traceroute with parsed hop addresses and response times
- TCP scanning for individual ports, lists, and ranges
- Open, closed, filtered, and error scan states
- Combined diagnostic reports in text or JSON
- Automated tests, formatting, linting, and strict type checking

## Platform support

The project has been tested on:

- macOS
- Ubuntu Linux

NetScope also contains Windows-specific `ping` and `tracert` handling covered by automated tests, but Windows has not been verified with live diagnostics.

Ping and traceroute use the operating system commands. Ensure `ping` and `traceroute` are installed and available on `PATH`; Windows provides `ping` and `tracert` under their standard names.

## Installation

NetScope requires Python 3.11 or newer.

```bash
git clone https://github.com/Samuel5011/NetScope.git
cd NetScope

python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

On Windows, activate the environment with `.venv\Scripts\activate`.

For development tools:

```bash
pip install -e ".[dev]"
```

## Usage

Resolve a target:

```bash
netscope dns example.com
```

Check reachability:

```bash
netscope ping example.com
```

Trace the route with optional hop and response limits:

```bash
netscope trace example.com --max-hops 20 --timeout 1.5
```

Scan a list containing individual ports and inclusive ranges:

```bash
netscope scan example.com --ports 22,80,443,8000-8010
```

Run the complete diagnostic set:

```bash
netscope diagnose example.com --ports 22,80,443
```

Every command supports JSON output:

```bash
netscope diagnose example.com --json
netscope scan example.com --ports 80,443 --json
```

Use command-specific help to see all timeout and range options:

```bash
netscope --help
netscope diagnose --help
```

More output samples are in [docs/examples.md](docs/examples.md), and the internal design is described in [docs/architecture.md](docs/architecture.md).

## Development

Run the required quality checks before committing:

```bash
black .
ruff check .
mypy src
pytest
```

The current suite contains 63 tests covering diagnostics, parsing, report formatting, JSON serialization, platform command handling, and CLI integration.
