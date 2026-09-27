# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 0.4.x | ✅ |
| < 0.4 | ❌ |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it by emailing
saraasaalari@yahoo.com.

Please include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You can expect an initial response within 48 hours.

## What to expect

- We will acknowledge receipt of your report within 48 hours.
- We will provide an estimated timeline for a fix.
- We will notify you when the vulnerability is fixed.
- We will credit you in the release notes (unless you prefer to remain anonymous).

## Scope

datasift-py is a zero-dependency library. Security concerns include:

- Arbitrary code execution via malicious input files
- Denial of service via crafted input
- Path traversal in file operations

Please note that datasift-py does **not** execute any code from input files.
Data formats are parsed with Python's standard library. Schema files supplied as Python modules are intentionally imported and executed by Python; only load schema files you trust.