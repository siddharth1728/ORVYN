"use client";

import React from "react";
import { Task } from "../types/task";

interface OverviewStatsProps {
  tasks: Task[];
}

export const OverviewStats: React.FC<OverviewStatsProps> = ({ tasks }) => {
  const activeCount = tasks.filter((t) =>
    ["EXECUTING", "PLANNING", "RESUMING"].includes(t.status)
  ).length;

  const waitingCount = tasks.filter((t) => t.status === "WAITING").length;

  const humanRequiredCount = tasks.filter((t) =>
    ["HUMAN_REQUIRED", "CALLING", "AWAITING_RESPONSE"].includes(t.status)
  ).length;

  const completedCount = tasks.filter((t) => t.status === "COMPLETED").length;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
      {/* Active Tasks */}
      <div className="p-5 rounded-xl bg-surface border border-surfaceBorder">
        <div className="text-xs uppercase tracking-wider text-gray-400 font-medium">
          Active Tasks
        </div>
        <div className="text-3xl font-bold mt-2 text-blue-400">{activeCount}</div>
        <div className="text-xs text-gray-500 mt-1">Autonomous loop executing</div>
      </div>

      {/* Waiting Tasks */}
      <div className="p-5 rounded-xl bg-surface border border-surfaceBorder">
        <div className="text-xs uppercase tracking-wider text-gray-400 font-medium">
          Waiting Tasks
        </div>
        <div className="text-3xl font-bold mt-2 text-yellow-400">{waitingCount}</div>
        <div className="text-xs text-gray-500 mt-1">Paused or timer scheduled</div>
      </div>

      {/* Human Decisions Required */}
      <div className="p-5 rounded-xl bg-surface border border-surfaceBorder relative overflow-hidden">
        {humanRequiredCount > 0 && (
          <div className="absolute top-2 right-2 flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
          </div>
        )}
        <div className="text-xs uppercase tracking-wider text-gray-400 font-medium">
          Human Decisions
        </div>
        <div className="text-3xl font-bold mt-2 text-red-400">{humanRequiredCount}</div>
        <div className="text-xs text-gray-500 mt-1">Interventions awaiting response</div>
      </div>

      {/* Completed Tasks */}
      <div className="p-5 rounded-xl bg-surface border border-surfaceBorder">
        <div className="text-xs uppercase tracking-wider text-gray-400 font-medium">
          Completed Tasks
        </div>
        <div className="text-3xl font-bold mt-2 text-emerald-400">{completedCount}</div>
        <div className="text-xs text-gray-500 mt-1">Successfully fulfilled goals</div>
      </div>
    </div>
  );
};
