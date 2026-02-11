# Deployment Rollback Runbook

## Pre-Rollback Checklist
1. Confirm the bad deployment is the root cause (not a dependency issue).
2. Identify the last known-good revision.
3. Notify the team in the incident channel.
4. Check if database migrations were applied (rollback may need DB revert too).

## Kubernetes Deployment Rollback
```bash
# View rollout history
kubectl rollout history deployment/<service> -n <ns>

# Rollback to previous revision
kubectl rollout undo deployment/<service> -n <ns>

# Rollback to a specific revision
kubectl rollout undo deployment/<service> -n <ns> --to-revision=<N>

# Verify rollback succeeded
kubectl rollout status deployment/<service> -n <ns>
kubectl get pods -n <ns> -l app=<service> -w
```

## Helm Release Rollback
```bash
# List release history
helm history <release> -n <ns>

# Rollback to previous
helm rollback <release> 0 -n <ns>

# Rollback to specific revision
helm rollback <release> <revision> -n <ns>

# Verify
helm status <release> -n <ns>
```

## Canary / Progressive Rollback
If using Argo Rollouts or Flagger:
```bash
# Abort an in-progress canary
kubectl argo rollouts abort <rollout> -n <ns>

# Manually promote a rollback
kubectl argo rollouts undo <rollout> -n <ns>
```

## Feature Flag Rollback
If the issue is behind a feature flag:
1. Disable the flag in your flag management system (LaunchDarkly, Unleash, etc.).
2. No deployment needed — instant rollback.
3. Verify metrics stabilize.

## Post-Rollback
1. Confirm metrics return to baseline.
2. Update the incident channel with rollback status.
3. Investigate root cause before re-deploying.
4. Fix forward only after thorough review.
