import React from 'react';
import { Moon, Cpu, Database } from 'lucide-react';
import type { SystemMetrics } from '../types';

interface HeaderProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  systemMetrics: SystemMetrics | null;
}

export const Header: React.FC<HeaderProps> = ({ currentTab, setCurrentTab, systemMetrics }) => {
  const topTabs = [
    { id: 'synthesis', label: 'Studio' },
    { id: 'profiles', label: 'Profiles' },
    { id: 'models', label: 'Models' },
    { id: 'reports', label: 'Reports' },
  ];

  return (
    <header className="h-16 px-8 border-b border-[#1a1f38] bg-[#0c0e1a]/80 backdrop-blur-md flex items-center justify-between sticky top-0 z-20">
      {/* Top Pill Navigation */}
      <div className="flex items-center gap-1.5 p-1 bg-[#13172b] rounded-full border border-[#1f2545]">
        {topTabs.map((tab) => {
          const isActive = currentTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setCurrentTab(tab.id)}
              className={`px-5 py-1.5 rounded-full text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-md shadow-purple-600/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Right Metrics & Profile */}
      <div className="flex items-center gap-4">
        {/* CPU Badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 bg-[#14172a] border border-[#212747] rounded-xl text-xs font-medium text-slate-300">
          <Cpu className="w-3.5 h-3.5 text-purple-400" />
          <span>CPU</span>
          <span className="text-emerald-400 font-bold">{systemMetrics ? `${systemMetrics.cpu_percent}%` : '12%'}</span>
        </div>

        {/* RAM Badge */}
        <div className="flex items-center gap-2 px-3 py-1.5 bg-[#14172a] border border-[#212747] rounded-xl text-xs font-medium text-slate-300">
          <Database className="w-3.5 h-3.5 text-blue-400" />
          <span>RAM</span>
          <span className="text-blue-300 font-bold">
            {systemMetrics ? `${systemMetrics.ram_used_gb} / ${systemMetrics.ram_total_gb} GB` : '4.2 / 16 GB'}
          </span>
        </div>

        {/* Theme Toggle */}
        <button 
          title="Toggle Theme"
          className="p-2 rounded-xl bg-[#14172a] border border-[#212747] text-slate-400 hover:text-slate-200 transition-colors"
        >
          <Moon className="w-4 h-4 text-purple-300" />
        </button>

        {/* User Avatar */}
        <div 
          title="User Account"
          className="w-9 h-9 rounded-full bg-gradient-to-tr from-purple-600 to-indigo-500 flex items-center justify-center text-white text-xs font-bold border-2 border-[#2b2f57] shadow-md shadow-purple-900/30 cursor-pointer"
        >
          HK
        </div>
      </div>
    </header>
  );
};
