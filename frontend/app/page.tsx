"use client";

import React, { useEffect, useState } from "react";
import { Header } from "../components/Header";
import { OverviewStats } from "../components/OverviewStats";
import { TaskList } from "../components/TaskList";
import { TaskDetail } from "../components/TaskDetail";
import { CreateTaskModal } from "../components/CreateTaskModal";
import { Task } from "../types/task";
import { fetchTasks } from "../lib/api";

export default function DashboardPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  const loadTasks = async () => {
    try {
      const data = await fetchTasks();
      setTasks(data);
      if (data.length > 0 && !selectedTaskId) {
        setSelectedTaskId(data[0].id);
      }
    } catch (err) {
      console.error("Could not fetch tasks:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
    const interval = setInterval(loadTasks, 4000);
    return () => clearInterval(interval);
  }, []);

  const selectedTask = tasks.find((t) => t.id === selectedTaskId) || null;

  return (
    <div className="min-h-screen flex flex-col">
      <Header onNewTaskClick={() => setIsModalOpen(true)} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
        <OverviewStats tasks={tasks} />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Tasks List */}
          <div className="lg:col-span-5">
            <TaskList
              tasks={tasks}
              selectedTaskId={selectedTaskId}
              onSelectTask={(id) => setSelectedTaskId(id)}
            />
          </div>

          {/* Right Column: Selected Task Control & Detail */}
          <div className="lg:col-span-7">
            {selectedTask ? (
              <TaskDetail task={selectedTask} onRefresh={loadTasks} />
            ) : (
              <div className="rounded-xl bg-surface border border-surfaceBorder p-12 text-center text-sm text-gray-500">
                Select a task to inspect runtime activity, state snapshots, and intervention status.
              </div>
            )}
          </div>
        </div>
      </main>

      <CreateTaskModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onTaskCreated={(newId) => {
          setSelectedTaskId(newId);
          loadTasks();
        }}
      />
    </div>
  );
}
