# Phase 05: Async Job Orchestration and Worker Model

## Objective

Introduce asynchronous processing by decoupling request ingestion from deduplication execution using a queue + worker model.

## Scope

This phase transitions from direct synchronous execution to:

- API ingestion endpoint
- Job queue dispatch
- Background worker execution
- Job status tracking

## Planned Deliverables

- [ ] Minimal API service (submit dedupe job)
- [ ] Queue integration (e.g., Redis/RabbitMQ-backed)
- [ ] Worker service for pipeline execution
- [ ] Job status model (`pending/running/completed/failed`)
- [ ] Basic result retrieval endpoint or artifact lookup mechanism

## Target Flow

1. Client submits job request
2. API validates request and enqueues job
3. Worker consumes job and runs 3-stage pipeline
4. Worker stores status + output references
5. Client queries job status/result

## Acceptance Criteria

- [ ] API returns job ID on submission
- [ ] Worker processes queued jobs successfully
- [ ] Job state transitions are visible and consistent
- [ ] Failed jobs are marked correctly with error context
- [ ] Duplicate job submissions are handled safely (idempotency strategy defined)

## Evidence to Capture

- Example API request/response payloads
- Queue/worker logs showing end-to-end execution
- Sample job lifecycle (pending -> running -> completed)
- Failure scenario evidence (invalid input or worker error)

## Risks / Notes

- Exactly-once vs at-least-once processing trade-offs
- Queue visibility timeout / retry semantics
- Result storage and lifecycle management