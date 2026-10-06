export type TaskStatus =
  | "CREATED"
  | "PLANNING"
  | "EXECUTING"
  | "WAITING"
  | "BLOCKED"
  | "HUMAN_REQUIRED"
  | "CALLING"
  | "AWAITING_RESPONSE"
  | "RESUMING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export type TaskPriority = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface Task {
  id: string;
  title: string;
  objective: string;
  status: TaskStatus;
  priority: TaskPriority;
  current_step: number;
  created_at: string;
  updated_at: string;
  metadata: Record<string, any>;
}

export interface TaskCheckpoint {
  id: string;
  task_id: string;
  step_index: number;
  step_name: string;
  state_snapshot: Record<string, any>;
  resumption_token: string;
  created_at: string;
}

export interface DomainEvent {
  event_id: string;
  event_type: string;
  task_id?: string;
  timestamp: string;
  payload: Record<string, any>;
  source: string;
}
