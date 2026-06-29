# Gemma Aegis — Always-on Blue-Team Defender Swarm

```text
Gemma Aegis
Always-on blue-team defender swarm for enterprise data, powered by Gemma 4 31B on Cerebras.

Core pitch:
Static virus detectors are too slow/dumb. Gemma Aegis watches identity, DLP, endpoint, SaaS, and storage telemetry, then coordinates defender agents to stop data exfiltration before breach.

Defender agents:
- Data Sentinel — finds sensitive data at risk across DLP, SaaS, storage, and database telemetry.
- Identity Guardian — catches OAuth abuse, impossible travel, account takeover, and risky service-account use.
- Endpoint Hunter — links EDR alerts, workstation behavior, PowerShell, Office parent processes, and lateral movement.
- Response Orchestrator — coordinates containment, evidence capture, owner routing, and executive breach-prevention brief.

Enterprise telemetry, sanitized demo feed:
- 09:13 UTC: finance admin impossible travel: finance-admin@corp signs in from US and NL within 11 minutes.
- 09:15 UTC: malicious OAuth grant: app "Quarterly Metrics Exporter" receives Files.Read.All and Mail.Read scopes.
- 09:18 UTC: S3 export spike: finance-close-prod exports 2GB to previously unseen ASN 64590.
- 09:19 UTC: DLP payroll/bank-account staging: 1,248 records staged in /tmp/export-cache.
- 09:21 UTC: PowerShell download cradle: EDR flags FIN-WKS-044, parent process WINWORD.EXE.
- 09:24 UTC: lateral RDP with service account: FIN-WKS-044 reaches analytics jump host using svc-reporting.

Ask Gemma Aegis to return:
- Which enterprise data is at risk.
- Which identity / endpoint / storage signals connect into one exfiltration chain.
- What to contain immediately without destroying evidence.
- What evidence proves the chain.
- What executive brief explains avoided breach impact.
```


