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
    <aside 
      className="w-[240px] border-r flex flex-col justify-between shrink-0 h-screen sticky top-0 select-none z-30 transition-colors"
      style={{ 
        backgroundColor: 'var(--bg-sidebar)',
        borderColor: 'var(--border-card)'
      }}
    >
      <div>
        {/* Logo Section matching Image 1 */}
        <div className="pt-7 pb-6 px-6 flex items-center gap-3">
          {/* Waveform Logo Icon matching Image 1 */}
          <div className="flex items-center gap-1 h-6">
            <span className="w-1 h-3.5 bg-cyan-400 rounded-full animate-pulse"></span>
            <span className="w-1 h-6 bg-cyan-300 rounded-full"></span>
            <span className="w-1 h-4.5 bg-purple-400 rounded-full"></span>
            <span className="w-1 h-7 bg-purple-500 rounded-full"></span>
            <span className="w-1 h-3 bg-purple-600 rounded-full animate-pulse"></span>
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight leading-tight font-sans" style={{ color: 'var(--text-primary)' }}>
              VoiceStudio
            </h1>
            <p className="text-[11px] font-medium tracking-normal mt-0.5" style={{ color: 'var(--text-secondary)' }}>
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
                className={`w-full flex items-center gap-3.5 px-4 py-3 rounded-2xl text-[13.5px] font-semibold transition-all cursor-pointer ${
                  isActive
                    ? 'active-nav-glow text-white'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#13172e] dark:hover:bg-[#13172e] light:hover:bg-slate-100 light:text-slate-600'
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
      <div 
        className="p-4 m-3.5 rounded-2xl border shadow-lg transition-colors"
        style={{ 
          backgroundColor: 'var(--bg-card)',
          borderColor: 'var(--border-card)'
        }}
      >
        <div className="flex items-center gap-2 mb-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
          </span>
          <span className="text-xs font-bold tracking-wide" style={{ color: 'var(--text-primary)' }}>
            {systemMetrics?.device || 'Local (CPU)'}
          </span>
        </div>
        <div className="text-[11.5px] font-medium" style={{ color: 'var(--text-secondary)' }}>
          Model: {systemMetrics?.model_name || 'IndicF5 (English)'}
        </div>
        <div className="text-[11.5px] mt-1 flex justify-between" style={{ color: 'var(--text-secondary)' }}>
          <span>RAM: {systemMetrics ? `${systemMetrics.ram_total_gb} GB` : '16 GB'}</span>
          <span>
            Status: <span className="text-emerald-400 font-semibold">Ready</span>
          </span>
        </div>
      </div>
    </aside>
  );
};
