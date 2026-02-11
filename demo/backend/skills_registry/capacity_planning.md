# Capacity Planning & Autoscaling Runbook

## Resource Right-Sizing
1. **Audit current usage**: Compare requests vs actual usage over 7 days.
   ```bash
   kubectl top pods -n <ns> --sort-by=cpu
   kubectl top pods -n <ns> --sort-by=memory
   ```
2. **Identify waste**: Pods requesting 2 CPU but using 0.1 CPU are over-provisioned.
3. **Set requests = p95 usage**, limits = 2x requests (prevents OOM without waste).

## Horizontal Pod Autoscaler (HPA)
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: <service>-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: <service>
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
```

## Vertical Pod Autoscaler (VPA)
Use in "recommend" mode first to get sizing suggestions:
```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: <service>-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: <service>
  updatePolicy:
    updateMode: "Off"  # "Off" = recommend only, "Auto" = apply changes
```

## Traffic Spike Preparation
1. Pre-scale 30 minutes before expected spike.
2. Warm up connection pools, caches, and DNS.
3. Set HPA `minReplicas` to expected baseline.
4. Enable rate limiting as a safety net.
5. Monitor during event, scale down gradually after.

## Capacity Planning Formula
```
Required replicas = (peak_rps × p99_latency_seconds) / concurrency_per_pod
Buffer = Required replicas × 1.3  (30% headroom)
```
