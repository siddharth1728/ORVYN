# ADR 001: Modular Monolith Architecture
*Status: Accepted*
*Date: 2026-10-05*

## Context
ORVYN is an autonomous agent system with complex state transitions, event dispatching, checkpointing, and telephony callbacks. Modern AI architectures frequently rush into premature microservices (separate auth service, task service, vector service, voice service), introducing significant network latency, distributed transaction overhead, serialization drift, and high deployment complexity.

## Decision
We chose a **Modular Monolith** architecture for the ORVYN platform:
1. All domain entities, services, and event dispatchers reside in a single codebase with strict package separation (`domain/`, `application/`, `infrastructure/`, `api/`).
2. Domain logic remains decoupled from infrastructure dependencies via interfaces.
3. Checkpoints and task state transitions are ACID-guaranteed within single database transactions.
4. The system is designed such that high-throughput components (e.g. background workers or telephony webhooks) can be split into separate deployables in later phases without altering domain code.

## Consequences
- **Positive**: Extremely fast iteration, deterministic end-to-end integration tests, zero distributed transaction overhead, straightforward local debugging.
- **Negative**: Long-running blocking steps must be handled asynchronously inside worker processes or background tasks to avoid stalling the HTTP event loop.
