"use client";

import React from "react";

interface HeaderProps {
  onNewTaskClick: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onNewTaskClick }) => {
  return (
    <header className="border-b border-surfaceBorder bg-surface/50 backdrop-blur sticky top-0 z-20">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/20">
            O
          </div>
          <div>
            <h1 className="font-semibold text-lg tracking-tight text-white flex items-center gap-2">
              ORVYN
              <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 font-normal border border-blue-500/20">
                Agent Control Center
              </span>
            </h1>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="text-xs text-gray-400 hidden sm:block">
            Autonomous Human-in-the-Loop Runtime
          </div>
          <button
            onClick={onNewTaskClick}
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition shadow-md shadow-blue-600/20 flex items-center gap-2"
          >
            <span>+</span> New Autonomous Task
          </button>
        </div>
      </div>
    </header>
  );
};
