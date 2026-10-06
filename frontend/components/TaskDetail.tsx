"use client";

import React, { useEffect, useState } from "react";
import { Task, TaskCheckpoint, DomainEvent } from "../types/task";
import { fetchCheckpoints, fetchEvents, runTask, pauseTask, resumeTask } from "../lib/api";

interface TaskDetailProps {
  task: Task;
  onRefresh: () => void;
}

export const TaskDetail: React.FC<TaskDetailProps> = ({ task, onRefresh }) => {
  const [checkpoints, setCheckpoints] = useState<TaskCheckpoint[]>([]);
  const [events, setEvents] = useState<DomainEvent[]>([]);
  const [loadingAction, setLoadingAction] = useState(false);
  const [decisionInput, setDecisionInput] = useState("");

  const loadDetails = async () => {
    try {
      const [chks, evts] = await Promise.all([
        fetchCheckpoints(task.id),
        fetchEvents(task.id),
      ]);
      setCheckpoints(chks);
      setEvents(evts);
    } catch (err) {
      console.error("Failed to load details:", err);
    }
  };

  useEffect(() => {
    loadDetails();
  }, [task.id]);

  const handleRun = async () => {
    setLoadingAction(true);
    try {
      await runTask(task.id);
      await loadDetails();
      onRefresh();
    } finally {
      setLoadingAction(false);
    }
  };

  const handlePause = async () => {
    setLoadingAction(true);
    try {
      await pauseTask(task.id);
      await loadDetails();
      onRefresh();
    } finally {
      setLoadingAction(false);
    }
  };

  const handleResume = async () => {
    setLoadingAction(true);
    try {
      await resumeTask(task.id, { relocation: true, manual_input: decisionInput });
      setDecisionInput("");
      await loadDetails();
      onRefresh();
    } finally {
      setLoadingAction(false);
    }
  };

  const isAwaitingHuman = [
    "HUMAN_REQUIRED",
    "CALLING",
    "AWAITING_RESPONSE",
  ].includes(task.status);

  return (
    <div className="rounded-xl bg-surface border border-surfaceBorder overflow-hidden">
      {/* Task Header */}
      <div className="p-6 border-b border-surfaceBorder flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-white tracking-tight">{task.title}</h2>
            <span className="text-xs px-2.5 py-0.5 rounded-full border bg-surface border-surfaceBorder text-gray-300 font-mono">
              Step {task.current_step}
            </span>
          </div>
          <p className="text-sm text-gray-400 mt-2 max-w-2xl">{task.objective}</p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          {task.status === "CREATED" && (
            <button
              onClick={handleRun}
              disabled={loadingAction}
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium transition shadow-md shadow-emerald-600/20"
            >
              {loadingAction ? "Starting..." : "Start Autonomous Execution"}
            </button>
          )}

          {["EXECUTING", "PLANNING"].includes(task.status) && (
            <button
              onClick={handlePause}
              disabled={loadingAction}
              className="px-4 py-2 rounded-lg bg-yellow-600 hover:bg-yellow-500 text-white text-sm font-medium transition"
            >
              Pause
            </button>
          )}

          {isAwaitingHuman && (
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={decisionInput}
                onChange={(e) => setDecisionInput(e.target.value)}
                placeholder="Simulate user voice response..."
                className="px-3 py-1.5 rounded-lg bg-background border border-surfaceBorder text-xs text-white focus:outline-none focus:border-blue-500"
              />
              <button
                onClick={handleResume}
                disabled={loadingAction}
                className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition whitespace-nowrap"
              >
                {loadingAction ? "Resuming..." : "Provide Decision & Resume"}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Grid: Execution Timeline & State Snapshots */}
      <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-surfaceBorder">
        {/* Left Column: Activity & Events Timeline */}
        <div className="p-6">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-4">
            Agent Activity Timeline
          </h3>

          {events.length === 0 ? (
            <div className="text-xs text-gray-500 py-6 text-center">
              No audit events logged yet.
            </div>
          ) : (
            <div className="relative border-l border-surfaceBorder ml-3 space-y-6">
              {events.map((evt) => (
                <div key={evt.event_id} className="relative pl-6">
                  <div className="absolute -left-1.5 top-1.5 w-3 h-3 rounded-full bg-blue-500 border-2 border-surface"></div>
                  <div className="flex justify-between items-baseline">
                    <span className="text-xs font-mono font-semibold text-white">
                      {evt.event_type}
                    </span>
                    <span className="text-[11px] text-gray-500">
                      {new Date(evt.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  {evt.payload && (
                    <pre className="mt-1 p-2 rounded bg-background border border-surfaceBorder text-[11px] font-mono text-gray-400 overflow-x-auto">
                      {JSON.stringify(evt.payload, null, 2)}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Checkpoints & Context */}
        <div className="p-6 space-y-6">
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-4">
              Persisted Checkpoints ({checkpoints.length})
            </h3>

            {checkpoints.length === 0 ? (
              <div className="text-xs text-gray-500 py-6 text-center">
                No checkpoints created yet.
              </div>
            ) : (
              <div className="space-y-3">
                {checkpoints.map((chk) => (
                  <div
                    key={chk.id}
                    className="p-3.5 rounded-lg bg-background border border-surfaceBorder text-xs"
                  >
                    <div className="flex justify-between items-center font-mono">
                      <span className="text-blue-400 font-semibold">{chk.step_name}</span>
                      <span className="text-gray-500">Step {chk.step_index}</span>
                    </div>
                    <div className="text-[11px] text-gray-500 mt-1 truncate">
                      Token: {chk.resumption_token}
                    </div>
                    <details className="mt-2 text-gray-400">
                      <summary className="cursor-pointer text-[11px] text-gray-500 hover:text-white">
                        Inspect Snapshot
                      </summary>
                      <pre className="mt-2 p-2 rounded bg-surface border border-surfaceBorder text-[10px] overflow-x-auto text-gray-300">
                        {JSON.stringify(chk.state_snapshot, null, 2)}
                      </pre>
                    </details>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
