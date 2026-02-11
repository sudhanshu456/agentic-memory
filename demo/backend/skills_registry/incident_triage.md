# Incident Triage & Root Cause Analysis Runbook

## Severity Classification
- **P1 / Critical**: Revenue-impacting, full outage, data loss risk. Response: <5 min.
- **P2 / Major**: Degraded service, partial outage, SLO breach. Response: <15 min.
- **P3 / Minor**: Non-critical feature broken, workaround exists. Response: <1 hour.
- **P4 / Low**: Cosmetic, logging noise, no user impact. Response: next business day.

## Initial Diagnostics Checklist
1. **What changed?** — Check recent deployments (`kubectl rollout history`), config changes, infra diffs.
2. **What's the blast radius?** — Which services, regions, user segments are affected?
3. **What do the metrics say?** — Error rates, latency p99, CPU/memory, queue depth.
4. **What do the logs say?** — Grep for error spikes: `kubectl logs --since=10m -l app=<service> | grep -i error`
5. **Is it a dependency?** — Check upstream/downstream service health, third-party status pages.

## Escalation Flow
1. Acknowledge the page within SLA.
2. Open an incident channel (e.g., #inc-YYYY-MM-DD-description).
3. Assign Incident Commander (IC) and Communications Lead.
4. Post initial impact assessment within 10 minutes.
5. Escalate to service owner if not resolved within 30 minutes.

## Root Cause Analysis (RCA) Template
After resolution, document:
- **Timeline**: When did it start, when detected, when mitigated, when resolved?
- **Root Cause**: The actual underlying cause (not symptoms).
- **Contributing Factors**: What made detection or resolution harder?
- **Action Items**: Preventive measures with owners and deadlines.
- **Lessons Learned**: What went well, what didn't?

## Common Kubernetes Diagnostic Commands
```bash
# Pod status and recent events
kubectl get pods -n <ns> -l app=<service> -o wide
kubectl describe pod <pod> -n <ns>

# Recent logs
kubectl logs -n <ns> -l app=<service> --tail=100 --since=5m

# Resource pressure
kubectl top pods -n <ns> --sort-by=memory
kubectl top nodes

# Check recent rollouts
kubectl rollout status deployment/<service> -n <ns>
kubectl rollout history deployment/<service> -n <ns>
```
