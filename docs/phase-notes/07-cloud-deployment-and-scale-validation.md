# Phase 07: Cloud Deployment and Scale Validation

## Objective

Demonstrate deployability and scaling characteristics in a cloud-native environment (local orchestration and/or cloud platform).

## Scope

This phase validates the architecture under deployment conditions:

- Container orchestration
- Service composition
- Horizontal scaling behaviour
- Environment portability

## Planned Deliverables

- [ ] Docker Compose stack (API, queue, worker, optional storage)
- [ ] Optional Kubernetes manifests (deployment/service/configmap/secret)
- [ ] Deployment documentation
- [ ] Scale test notes (worker replicas and throughput behaviour)
- [ ] Cloud-native evaluation summary for dissertation

## Acceptance Criteria

- [ ] Full stack starts and processes jobs end-to-end
- [ ] Worker replica count can be increased without code changes
- [ ] System remains functionally correct under scaled worker execution
- [ ] Results are reproducible with documented commands
- [ ] Dissertation includes cloud-native architecture + trade-off discussion

## Evidence to Capture

- Compose/K8s startup commands and status output
- Demonstration of N-worker run vs 1-worker run
- Throughput/latency comparison (simple table acceptable)
- Architecture diagram and deployment topology diagram

## Risks / Notes

- Local machine constraints may limit meaningful scale testing
- Queue/backend tuning may be needed for fair comparisons
- Cloud cost/time constraints may limit full managed-cloud deployment