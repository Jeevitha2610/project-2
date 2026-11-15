import React from 'react';
import { 
  Activity, 
  BarChart2, 
  Clock, 
  FileText, 
  FileAudio, 
  Info, 
  Mic2, 
  Radio, 
  Settings, 
  Sliders, 
  Users 
} from 'lucide-react';
import type { SystemMetrics } from '../types';

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  systemMetrics: SystemMetrics | null;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, setCurrentTab, systemMetrics }) => {
  const navItems = [
    { id: 'synthesis', label: 'Synthesis', icon: Radio },
    { id: 'profiles', label: 'Voice Profiles', icon: Users },
    { id: 'models', label: 'Model & Settings', icon: Sliders },
    { id: 'evaluation', label: 'Evaluation', icon: BarChart2 },
    { id: 'history', label: 'History', icon: Clock },
    { id: 'monitor', label: 'System Monitor', icon: Activity },
    { id: 'library', label: 'Audio Library', icon: FileAudio },
    { id: 'reports', label: 'Reports', icon: FileText },
    { id: 'settings', label: 'Settings', icon: Settings },
    { id: 'about', label: 'About & License', icon: Info },
  ];

  return (
    <aside className="w-64 bg-[#0d0f1d] border-r border-[#1a1f38] flex flex-col justify-between shrink-0 h-screen sticky top-0 select-none">
      <div>
        {/* Logo Section */}
        <div className="p-6 flex items-center gap-3 border-b border-[#1a1f38]">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 via-purple-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-purple-500/20">
            <Mic2 className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-1.5">
              VoiceStudio
            </h1>
            <p className="text-xs text-slate-400 font-medium">Voice Cloning Studio</p>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-3 space-y-1.5 overflow-y-auto max-h-[calc(100vh-230px)]">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                className={`w-full flex items-center gap-3.5 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-purple-600/90 to-blue-600/90 text-white shadow-lg shadow-purple-900/30 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#161a2e]'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Status Box */}
      <div className="p-4 m-3 rounded-2xl bg-[#121526] border border-[#1e233d]">
        <div className="flex items-center gap-2 mb-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
          </span>
          <span className="text-xs font-semibold text-emerald-400 tracking-wide">
            {systemMetrics?.device || 'Local (CPU)'}
          </span>
        </div>
        <div className="text-xs text-slate-300 font-medium truncate">
          Model: {systemMetrics?.model_name || 'IndicF5 (English)'}
        </div>
        <div className="text-[11px] text-slate-400 mt-1 flex justify-between">
          <span>RAM: {systemMetrics ? `${systemMetrics.ram_total_gb} GB` : '16 GB'}</span>
          <span className="text-emerald-400 font-semibold">Status: Ready</span>
        </div>
      </div>
    </aside>
  );
};
