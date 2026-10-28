# NetScope examples

Addresses and timings below are illustrative; real output depends on the target and network.

## DNS lookup

```bash
netscope dns example.com
```

```text
Target: example.com
IP address: 93.184.216.34
Response time: 2.41 ms
```

## Ping

```bash
netscope ping example.com
```

```text
Target: example.com
Reachable: Yes
Average latency: 18.25 ms
Packet loss: 0.0%
```

## Traceroute

```bash
netscope trace example.com --max-hops 20 --timeout 1.5
```

```text
Traceroute to example.com
 1  192.168.1.1  1.10 ms 1.04 ms 1.08 ms
 2  203.0.113.1  8.32 ms 8.15 ms 8.41 ms
```

A hop that does not answer is shown as `*`.

## TCP port scan

Scan individual ports and ranges in one command:

```bash
netscope scan example.com --ports 22,80,443,8000-8002
```

```text
22/tcp: CLOSED
80/tcp: OPEN (http)
443/tcp: OPEN (https)
8000/tcp: FILTERED - Connection timed out
8001/tcp: CLOSED
8002/tcp: CLOSED
```

Repeated ports are scanned once. Ranges must be ascending, and every port must be between 1 and 65535.

## Combined diagnostic

```bash
netscope diagnose example.com --ports 80,443
```

The report contains a timestamped target header followed by DNS, ping, traceroute, and TCP port sections. Timeout controls are available through `--port-timeout`, `--trace-timeout`, and `--max-hops`.

## JSON output

Add `--json` to any command:

```bash
netscope dns example.com --json
```

```json
{
  "target": {
    "value": "example.com",
    "type": "hostname"
  },
  "generated_at": "2026-10-28T12:00:00+00:00",
  "dns": {
    "success": true,
    "ip_address": "93.184.216.34",
    "response_time_ms": 2.41,
    "error": null
  },
  "ping": null,
  "traceroute": null,
  "ports": []
}
```

## Invalid input

Diagnostics accept a hostname or IP address, not a URL:

```bash
netscope ping https://example.com
```

```text
netscope: error: Target must be a hostname or IP address, not a URL
```
