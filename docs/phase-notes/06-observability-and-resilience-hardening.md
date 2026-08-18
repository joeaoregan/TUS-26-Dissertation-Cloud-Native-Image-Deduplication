# Phase 06: Observability and Resilience Hardening

## Objective

Add operational controls and telemetry to make the service diagnosable, fault-tolerant, and cloud-runtime friendly.

## Scope

This phase emphasises non-functional cloud-native qualities:

- Observability
- Resilience
- Operational health signalling

## Planned Deliverables

- [ ] Structured logging (JSON preferred)
- [ ] Correlation ID / job ID propagation across components
- [ ] Retry policy for transient failures
- [ ] Failure classification (retryable vs non-retryable)
- [ ] Health endpoint (`/health`) and readiness endpoint (`/ready`)
- [ ] Basic timeout and resource guardrails

## Acceptance Criteria

- [ ] Logs can be traced per job end-to-end
- [ ] Transient failures trigger bounded retries
- [ ] Non-retryable failures fail fast with clear diagnostics
- [ ] Health/readiness endpoints reflect service state correctly
- [ ] Operational runbook includes failure triage guidance

## Evidence to Capture

- Sample structured logs for one full job lifecycle
- Retry example with eventual success/failure
- Health/readiness endpoint outputs
- Incident-style troubleshooting note (short)

## Risks / Notes

- Over-retrying can amplify load or duplicate work
- Need idempotent processing for safe retries
- Logging verbosity vs performance trade-off