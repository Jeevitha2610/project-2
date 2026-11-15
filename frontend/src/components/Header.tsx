import React from 'react';
import { Sun, Moon } from 'lucide-react';
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
    <header className="h-[68px] px-8 bg-[#080a14] border-b border-[#161a33] flex items-center justify-between sticky top-0 z-20">
      {/* Top Pill Navigation */}
      <div className="flex items-center gap-1 p-1 bg-[#121528] rounded-full border border-[#1e233d]">
        {topTabs.map((tab) => {
          const isActive = (tab.id === 'synthesis' && currentTab === 'synthesis') || currentTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setCurrentTab(tab.id)}
              className={`px-5 py-1.5 rounded-full text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-md shadow-purple-600/40'
                  : 'text-slate-300 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Right Metrics & Profile */}
      <div className="flex items-center gap-3">
        {/* CPU Badge */}
        <div className="flex items-center gap-2 px-3.5 py-1.5 bg-[#121528] border border-[#1e233d] rounded-full text-xs font-semibold text-slate-200">
          <span>CPU</span>
          <span className="text-emerald-400 font-mono font-bold">
            {systemMetrics ? `${systemMetrics.cpu_percent}%` : '12%'}
          </span>
        </div>

        {/* RAM Badge */}
        <div className="flex items-center gap-2 px-3.5 py-1.5 bg-[#121528] border border-[#1e233d] rounded-full text-xs font-semibold text-slate-200">
          <span>RAM</span>
          <span className="text-slate-200 font-mono">
            {systemMetrics ? `${systemMetrics.ram_used_gb} / ${systemMetrics.ram_total_gb} GB` : '4.2 / 16 GB'}
          </span>
        </div>

        {/* Theme Toggle with Dual Sun/Moon Icons */}
        <button 
          title="Toggle Theme"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#121528] border border-[#1e233d] text-slate-300 hover:text-white transition-colors"
        >
          <Sun className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
          <Moon className="w-3.5 h-3.5 text-blue-400 fill-blue-400" />
        </button>

        {/* User Avatar */}
        <div 
          title="User Account"
          className="w-9 h-9 rounded-full bg-[#6366f1] flex items-center justify-center text-white text-xs font-bold shadow-md shadow-indigo-600/30 cursor-pointer border border-indigo-400/40"
        >
          HK
        </div>
      </div>
    </header>
  );
};
