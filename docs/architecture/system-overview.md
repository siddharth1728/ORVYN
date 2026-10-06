# ORVYN: System Overview Architecture
*Phase 01 Foundation Architecture*

## 1. Core Operating Invariant
> **ORVYN operates autonomously until the human becomes the missing piece.**

ORVYN is an autonomous agentic platform designed to execute long-running workflows without human babysitting. When ambiguity, high impact, or missing constraints emerge, ORVYN interrupts the user (via telephony or targeted notification), obtains a structured decision, and resumes execution from its exact checkpoint.

## 2. Monolithic Layering & Clean Architecture

ORVYN is structured as a modular monolith to maximize development speed, testability, and deterministic consistency:

```text
+-------------------------------------------------------------+
|                        API Layer                            |
|             (FastAPI routes, schemas, CORS)                 |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                    Application Services                     |
|  (TaskService, AgentRuntime, DecisionService, MemoryService) |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                        Domain Core                          |
|    (Tasks, StateMachine, Events, Checkpoints, Decisions)    |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                   Infrastructure Layer                      |
| (SQLAlchemy, Alembic, ToolRegistry, Provider Registries)   |
+-------------------------------------------------------------+
```

## 3. Communication & Decoupling
- **Domain Independence**: The core domain (`Task`, `TaskStateMachine`, `Event`) has zero dependencies on web frameworks, databases, or specific LLM SDKs.
- **Provider Registry**: External services (LLM, Voice, Telephony, Search) are accessed solely via abstract provider interfaces (`LLMProvider`, `TelephonyProvider`, `SearchProvider`).
- **Event-Driven Auditability**: All state transitions and agent actions publish typed `Event` objects through an asynchronous `EventDispatcher`.
