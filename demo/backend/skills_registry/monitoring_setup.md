# Monitoring, Alerting & SLO Configuration Runbook

## SLI / SLO Framework
- **SLI (Service Level Indicator)**: A measurable metric (e.g., request latency p99).
- **SLO (Service Level Objective)**: Target for the SLI (e.g., p99 latency < 200ms for 99.9% of requests).
- **Error Budget**: 100% - SLO = budget for failures (e.g., 0.1% = ~43 min/month of downtime).

### Common SLIs
| Service Type | SLI | Typical SLO |
|---|---|---|
| API | Availability (2xx / total) | 99.9% |
| API | Latency p99 | < 300ms |
| Queue Worker | Processing success rate | 99.95% |
| Batch Job | Completion within window | 99% |

## Alerting Rules (Prometheus example)
```yaml
groups:
- name: slo-alerts
  rules:
  - alert: HighErrorRate
    expr: |
      (sum(rate(http_requests_total{status=~"5.."}[5m]))
       / sum(rate(http_requests_total[5m]))) > 0.001
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Error rate exceeds 0.1% SLO threshold"

  - alert: HighLatency
    expr: |
      histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
      > 0.3
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "p99 latency exceeds 300ms SLO"
```

## Dashboard Essentials (Grafana / Datadog)
Every service dashboard should have:
1. **RED metrics**: Rate, Errors, Duration (latency)
2. **USE metrics**: Utilization, Saturation, Errors (for infra)
3. **SLO burn rate**: How fast are we consuming error budget?
4. **Deployment markers**: Overlay deploy events on graphs
5. **Dependency health**: Upstream/downstream status

## On-Call Escalation Policy
1. **L1** (0-5 min): Primary on-call gets paged.
2. **L2** (5-15 min): If unacknowledged, escalate to secondary.
3. **L3** (15-30 min): Escalate to team lead / engineering manager.
4. **L4** (30+ min): Escalate to VP Engineering for P1 incidents.

## Quick Setup Commands
```bash
# Port-forward Prometheus
kubectl port-forward svc/prometheus 9090:9090 -n monitoring

# Port-forward Grafana
kubectl port-forward svc/grafana 3000:3000 -n monitoring

# Check Alertmanager status
kubectl port-forward svc/alertmanager 9093:9093 -n monitoring
```
