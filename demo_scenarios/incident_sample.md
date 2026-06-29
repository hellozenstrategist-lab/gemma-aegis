# Demo scenario: enterprise incident triage

Paste this into the UI if you do not have a screenshot ready:

```text
Production auth incident, 09:42 PT:
- Login error rate rose from 0.2% to 18% after deploy api-gateway:2026.06.28-rc2.
- Support tickets mention SSO redirect loops for enterprise customers.
- WAF logs show normal volume, no obvious credential stuffing spike.
- Grafana screenshot shows p95 auth latency 210ms -> 3.8s and OAuth callback 500s.
- Rollback is possible but would also disable the new SAML tenant routing fix.
Triage severity, blast radius, immediate action, and evidence to collect next.
```

60-second video beat:
1. Paste incident.
2. Run Cerebras/Gemma.
3. Show wall-ms/tokens/sec.
4. Enable baseline and show side-by-side latency delta.
5. End on enterprise value: faster first response, less downtime, clear next actions.
