# Security policy

## Supported versions

| Version | Supported |
| --- | --- |
| 2.0.x (latest release) | ✓ |
| < 2.0 (`prettyTables`) | ✗ |

Fixes ship in a new 2.0.x release; please upgrade to the latest.

## Reporting a vulnerability

Please **do not** open a public issue for security problems. Use GitHub's
private reporting instead:
<https://github.com/Opus-Perpetuus/flexablelib/security/advisories/new>.

Include the affected version, a minimal reproduction and the impact you
expect. We aim to acknowledge reports within 5 business days and to publish a
fix and advisory as soon as one is ready.

## Scope notes

flexablelib renders data you give it. Two areas deserve care in your own
code:

- **Terminal escape sequences.** Cell text is printed as-is; if you render
  untrusted input to a terminal, strip control characters first.
- **HTML export.** `to_html` escapes cell text. Report any case where
  untrusted cell content can inject markup or script.
