"use client";

import React from "react";
import { Task, TaskStatus } from "../types/task";

interface TaskListProps {
  tasks: Task[];
  selectedTaskId: string | null;
  onSelectTask: (taskId: string) => void;
}

export const TaskList: React.FC<TaskListProps> = ({
  tasks,
  selectedTaskId,
  onSelectTask,
}) => {
  const getStatusBadge = (status: TaskStatus) => {
    switch (status) {
      case "EXECUTING":
      case "PLANNING":
      case "RESUMING":
        return "bg-blue-500/10 text-blue-400 border-blue-500/20";
      case "WAITING":
        return "bg-yellow-500/10 text-yellow-400 border-yellow-500/20";
      case "HUMAN_REQUIRED":
      case "CALLING":
      case "AWAITING_RESPONSE":
        return "bg-red-500/10 text-red-400 border-red-500/20 animate-pulse";
      case "COMPLETED":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "FAILED":
      case "CANCELLED":
        return "bg-gray-500/10 text-gray-400 border-gray-500/20";
      default:
        return "bg-gray-500/10 text-gray-300 border-gray-500/20";
    }
  };

  const getNextAction = (task: Task) => {
    switch (task.status) {
      case "CREATED":
        return "Decompose objective into step DAG";
      case "PLANNING":
        return "Synthesize step dependencies";
      case "EXECUTING":
        return `Execute step ${task.current_step + 1}`;
      case "HUMAN_REQUIRED":
      case "CALLING":
      case "AWAITING_RESPONSE":
        return "Awaiting user voice decision";
      case "WAITING":
        return "Wait for resumption trigger";
      case "RESUMING":
        return "Rehydrate checkpoint and continue";
      case "COMPLETED":
        return "Workflow completed";
      case "CANCELLED":
      case "FAILED":
        return "Terminated";
    }
  };

  return (
    <div className="rounded-xl bg-surface border border-surfaceBorder overflow-hidden">
      <div className="px-5 py-4 border-b border-surfaceBorder flex justify-between items-center">
        <h2 className="font-semibold text-white text-sm">Autonomous Workflows</h2>
        <span className="text-xs text-gray-400">{tasks.length} total</span>
      </div>

      {tasks.length === 0 ? (
        <div className="p-8 text-center text-sm text-gray-500">
          No tasks found. Create a new autonomous task to get started.
        </div>
      ) : (
        <div className="divide-y divide-surfaceBorder">
          {tasks.map((task) => {
            const isSelected = selectedTaskId === task.id;
            return (
              <div
                key={task.id}
                onClick={() => onSelectTask(task.id)}
                className={`p-4 cursor-pointer transition ${
                  isSelected ? "bg-blue-600/10 border-l-4 border-l-blue-500" : "hover:bg-white/[0.02]"
                }`}
              >
                <div className="flex justify-between items-start gap-4">
                  <div>
                    <h3 className="text-sm font-medium text-white">{task.title}</h3>
                    <p className="text-xs text-gray-400 mt-1 line-clamp-1">{task.objective}</p>
                  </div>
                  <span
                    className={`text-[11px] px-2 py-0.5 rounded-full border font-medium uppercase tracking-wider ${getStatusBadge(
                      task.status
                    )}`}
                  >
                    {task.status}
                  </span>
                </div>

                <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
                  <div className="flex items-center gap-3">
                    <span className="font-medium text-gray-400">Next: {getNextAction(task)}</span>
                    <span className="text-gray-600">•</span>
                    <span>Priority: {task.priority}</span>
                  </div>
                  <span>{new Date(task.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
