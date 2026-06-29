# Security and OPSEC

## Secrets

Do not commit secrets. Keep API keys in `.env` or process environment only. `.env` is ignored by git.

Never put these in source, screenshots, issues, pull requests, comments, or browser localStorage:

- Cerebras API keys
- OpenAI-compatible provider keys
- SSH keys
- GitHub tokens
- customer logs or customer screenshots
- real credentials, session cookies, OAuth tokens, refresh tokens, or service-account keys

## Demo safety

Gemma Aegis is a defender-demo workflow using synthetic/sanitized telemetry. It must not be used to run real exploitation, credential theft, malware, destructive containment, or unauthorized access.

The app renders containment recommendations and evidence reports. It does not execute live containment actions against production services.

## Reporting issues

If you find a security issue, do not publish exploit details publicly. Open a private GitHub security advisory or contact the maintainer through an approved private channel.

