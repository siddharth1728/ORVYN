# ORVYN: Task State Machine Specification

## 1. Legal States
- `CREATED`: Task instantiated, awaiting initial planning.
- `PLANNING`: Objective is being decomposed into steps.
- `EXECUTING`: Actively executing steps through tools.
- `WAITING`: Temporarily paused or waiting for an external timer/event.
- `BLOCKED`: Encountered an impasse requiring manual clearance.
- `HUMAN_REQUIRED`: An intervention request has been generated.
- `CALLING`: Voice bridge has dialed the user's phone.
- `AWAITING_RESPONSE`: Call connected or notification dispatched, awaiting human decision.
- `RESUMING`: Structured decision received, restoring state from checkpoint.
- `COMPLETED`: All planned steps succeeded.
- `FAILED`: Unrecoverable execution failure.
- `CANCELLED`: User or system aborted execution.

## 2. Transition Rules Matrix
Every transition is centrally verified by `TaskStateMachine.can_transition()`. Attempts to perform illegal jumps (e.g. `CREATED` -> `RESUMING` or `COMPLETED` -> `EXECUTING`) raise an `InvalidStateTransitionError`.
