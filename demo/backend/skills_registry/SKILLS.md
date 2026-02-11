# OpsAgent Skills Index

This file acts as a lightweight table of contents. The agent reads ONLY this
index at startup. Full skill/runbook instructions are loaded on-demand when
a user query matches the skill's keywords — **progressive disclosure**.

## incident_triage — Incident Triage & Root Cause Analysis
Summary: Guide SREs through incident severity classification, initial diagnostics, and RCA workflows.
Keywords: incident, outage, alert, page, severity, p1, p2, triage, root cause, rca, postmortem, fire

## rollback — Deployment Rollback Procedures
Summary: Step-by-step rollback runbook for Kubernetes deployments, Helm releases, and feature flags.
Keywords: rollback, deploy, deployment, revert, helm, release, canary, rollout, undo, failed deploy

## capacity_planning — Capacity Planning & Autoscaling
Summary: Help estimate resource needs, configure HPA/VPA, and plan for traffic spikes.
Keywords: capacity, scale, autoscale, hpa, vpa, resources, cpu, memory, limits, requests, traffic, spike, load

## monitoring_setup — Monitoring, Alerting & SLO Configuration
Summary: Set up dashboards, alerting rules, SLIs/SLOs, and on-call escalation policies.
Keywords: monitor, alert, dashboard, slo, sli, sla, grafana, datadog, prometheus, pagerduty, on-call, observability
