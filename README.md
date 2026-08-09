# NetScope

NetScope is a Python command-line network diagnostic toolkit for basic host troubleshooting and connectivity checks.

## Features

- Target validation for hostnames, IPv4 and IPv6 addresses
- DNS resolution with response timing
- ICMP reachability testing
- Packet-loss and latency reporting
- TCP port scanning
- Basic service identification for known ports
- Clear command-line error handling
- Automated tests and static analysis

## Installation

```bash
git clone <REPOSITORY_URL>
cd NetScope

python3 -m venv .venv
source .venv/bin/activate

pip install -e .
``` 

## Usage

### DNS lookup

```bash
netscope dns google.com
```

#### Example

```text
Target: google.com
IP address: 142.250.129.139
Response time: 85.85 ms
```

### Ping

```bash
netscope ping google.com
```

#### Example

```
Target: google.com
Reachable: Yes
Average latency: 37.11 ms
Packet loss: 0.0%
```

### TCP port scan

```bash
netscope scan google.com --ports 80,443
```

#### Example

```
80/tcp: OPEN (http)
443/tcp: OPEN (https)
```
#### Default ports

```bash
netscope scan google.com
```

## Architecture

NetScope separates command-line handling, diagnostics and result models.

```text
                CLI
                 │
                 ▼
         Target Validation
                 │
       ┌─────────┼─────────┐
       ▼         ▼         ▼
      DNS       Ping    TCP Scanner
       │         │         │
       └─────────┼─────────┘
                 ▼
            Result Models
```

## Testing and Code Quality

NetScope uses:

- pytest for automated testing
- mypy for static type checking
- Ruff for linting
- Black for code formatting

Current test suite: **14 tests passing**

Run the quality checks with:

```bash
pytest
mypy src
ruff check .
black --check .
```
