import React from 'react';
import { 
  Sliders, 
  BarChart2, 
  Clock, 
  Terminal, 
  User 
} from 'lucide-react';
import type { SystemMetrics } from '../types';

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  systemMetrics: SystemMetrics | null;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, setCurrentTab, systemMetrics }) => {
  const navItems = [
    { id: 'synthesis', label: 'Synthesis', icon: 'waveform' },
    { id: 'profiles', label: 'Voice Profiles', icon: 'user' },
    { id: 'models', label: 'Model & Settings', icon: 'settings' },
    { id: 'evaluation', label: 'Evaluation', icon: 'chart' },
    { id: 'history', label: 'History', icon: 'clock' },
    { id: 'monitor', label: 'System Monitor', icon: 'monitor' },
  ];

  return (
    <aside className="w-[240px] bg-[#0b0d1b] border-r border-[#191e38] flex flex-col justify-between shrink-0 h-screen sticky top-0 select-none z-30">
      <div>
        {/* Logo Section */}
        <div className="pt-7 pb-6 px-6 flex items-center gap-3">
          {/* Waveform Logo Icon matching Image 1 */}
          <div className="flex items-center gap-1 h-6">
            <span className="w-1 h-3.5 bg-cyan-400 rounded-full"></span>
            <span className="w-1 h-6 bg-cyan-300 rounded-full"></span>
            <span className="w-1 h-4.5 bg-purple-400 rounded-full"></span>
            <span className="w-1 h-7 bg-purple-500 rounded-full"></span>
            <span className="w-1 h-3 bg-purple-600 rounded-full"></span>
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white leading-tight font-sans">
              VoiceStudio
            </h1>
            <p className="text-[11px] text-slate-400 font-medium tracking-normal mt-0.5">
              Voice Cloning Studio
            </p>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="px-3.5 mt-2 space-y-2">
          {navItems.map((item) => {
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                className={`w-full flex items-center gap-3.5 px-4 py-3 rounded-2xl text-[13.5px] font-semibold transition-all ${
                  isActive
                    ? 'active-nav-glow text-white'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#13172e]'
                }`}
              >
                {/* Custom Icons matching Image 1 */}
                {item.icon === 'waveform' && (
                  <div className="flex items-center gap-0.5 h-4">
                    <span className="w-0.5 h-2 bg-white rounded-full"></span>
                    <span className="w-0.5 h-3.5 bg-white rounded-full"></span>
                    <span className="w-0.5 h-2.5 bg-white rounded-full"></span>
                    <span className="w-0.5 h-4 bg-white rounded-full"></span>
                    <span className="w-0.5 h-1.5 bg-white rounded-full"></span>
                  </div>
                )}
                {item.icon === 'user' && <User className="w-4 h-4 text-slate-400" />}
                {item.icon === 'settings' && <Sliders className="w-4 h-4 text-slate-400" />}
                {item.icon === 'chart' && <BarChart2 className="w-4 h-4 text-slate-400" />}
                {item.icon === 'clock' && <Clock className="w-4 h-4 text-slate-400" />}
                {item.icon === 'monitor' && <Terminal className="w-4 h-4 text-slate-400" />}
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Status Card matching Image 1 */}
      <div className="p-4 m-3.5 rounded-2xl bg-[#101328] border border-[#1c2242] shadow-lg">
        <div className="flex items-center gap-2 mb-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
          </span>
          <span className="text-xs font-bold text-white tracking-wide">
            {systemMetrics?.device || 'Local (CPU)'}
          </span>
        </div>
        <div className="text-[11.5px] text-slate-400 font-medium">
          Model: {systemMetrics?.model_name || 'IndicF5 (English)'}
        </div>
        <div className="text-[11.5px] text-slate-400 mt-1 flex justify-between">
          <span>RAM: {systemMetrics ? `${systemMetrics.ram_total_gb} GB` : '16 GB'}</span>
          <span className="text-slate-400">
            Status: <span className="text-emerald-400 font-semibold">Ready</span>
          </span>
        </div>
      </div>
    </aside>
  );
};
