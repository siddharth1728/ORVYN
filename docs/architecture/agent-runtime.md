# ORVYN: Autonomous Agent Runtime

## 1. Execution Loop
The autonomous agent runtime drives goals through an iterative, observable cycle:

```text
Receive Objective
       ↓
Create Task & Context
       ↓
AgentPlanner.create_plan()
       ↓
Enter Step Loop:
  ├── Check DecisionEngine for current step safety / missing info
  │     ├── IF HUMAN REQUIRED:
  │     │     ├── Capture TaskCheckpoint
  │     │     ├── Transition state (HUMAN_REQUIRED / CALLING / AWAITING_RESPONSE)
  │     │     └── Pause execution and yield AgentResult
  │     │
  │     └── IF SAFE:
  │           ├── Execute tool via ToolRegistry
  │           ├── Observe result & update working memory
  │           ├── Atomic Step Checkpoint
  │           └── Advance current_step
  │
Complete all steps
       ↓
Transition to COMPLETED
```

## 2. Key Abstractions
- **`AgentContext`**: Encapsulates the active `Task`, volatile `working_memory`, historical `checkpoints`, and `user_preferences`.
- **`AgentPlanner`**: Decomposes high-level text intent into an ordered sequence of discrete step specifications.
- **`AgentExecutor`**: Invokes tools through the typed `ToolRegistry` and captures outputs.
- **`AgentResult`**: The final or intermediate outcome indicating current status, step progress, checkpoints, and interruption reasons.
