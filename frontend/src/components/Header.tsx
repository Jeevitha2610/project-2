import type { FC } from 'react';
import { Sun, Moon } from 'lucide-react';
import type { SystemMetrics } from '../types';

interface HeaderProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  systemMetrics: SystemMetrics | null;
  theme: 'dark' | 'light';
  toggleTheme: () => void;
}

export const Header: FC<HeaderProps> = ({ 
  currentTab, 
  setCurrentTab, 
  systemMetrics,
  theme,
  toggleTheme 
}) => {
  const topTabs = [
    { id: 'synthesis', label: 'Studio' },
    { id: 'profiles', label: 'Profiles' },
    { id: 'models', label: 'Models' },
    { id: 'reports', label: 'Reports' },
  ];

  return (
    <header className="h-[68px] px-8 border-b border-[var(--border-header)] flex items-center justify-between sticky top-0 z-20 backdrop-blur-md transition-colors"
      style={{ backgroundColor: 'var(--bg-header)' }}
    >
      {/* Top Pill Navigation */}
      <div 
        className="flex items-center gap-1 p-1 rounded-full border transition-colors"
        style={{ 
          backgroundColor: 'var(--bg-card-inner)',
          borderColor: 'var(--border-inner)'
        }}
      >
        {topTabs.map((tab) => {
          const isActive = (tab.id === 'synthesis' && currentTab === 'synthesis') || currentTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setCurrentTab(tab.id)}
              className={`px-5 py-1.5 rounded-full text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-md shadow-purple-600/40'
                  : 'text-slate-400 hover:text-[var(--text-hover)]'
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Right Metrics & Profile */}
      <div className="flex items-center gap-3">
        {/* Colab GPU Cloud Badge */}
        {systemMetrics?.is_colab_connected && (
          <div 
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold border transition-all shadow-sm shadow-purple-500/20"
            style={{ 
              backgroundColor: 'var(--bg-card-inner)',
              borderColor: 'rgba(168, 85, 247, 0.45)',
              color: 'var(--text-primary)'
            }}
            title={`${systemMetrics.gpu_name || 'Tesla T4'} (Colab Cloud Active)`}
          >
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              GPU ({systemMetrics.gpu_name?.includes('T4') ? 'T4' : 'Colab'})
            </span>
            <span className="text-purple-400 font-mono font-bold">
              {systemMetrics.gpu_percent ?? 0}%
            </span>
          </div>
        )}

        {/* CPU Badge */}
        <div 
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold border transition-colors"
          style={{ 
            backgroundColor: 'var(--bg-card-inner)',
            borderColor: 'var(--border-inner)',
            color: 'var(--text-primary)'
          }}
        >
          <span>CPU</span>
          <span className="text-emerald-400 font-mono font-bold">
            {systemMetrics ? `${systemMetrics.cpu_percent}%` : '12%'}
          </span>
        </div>

        {/* RAM Badge */}
        <div 
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold border transition-colors"
          style={{ 
            backgroundColor: 'var(--bg-card-inner)',
            borderColor: 'var(--border-inner)',
            color: 'var(--text-primary)'
          }}
        >
          <span>RAM</span>
          <span className="font-mono text-[var(--text-mono)]">
            {systemMetrics ? `${systemMetrics.ram_used_gb} / ${systemMetrics.ram_total_gb} GB` : '4.2 / 16 GB'}
          </span>
        </div>

        {/* Theme Toggle Pill (Sun & Moon) matching Image 1 */}
        <button 
          onClick={toggleTheme}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
          className="flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all cursor-pointer hover:scale-105 active:scale-95"
          style={{ 
            backgroundColor: 'var(--bg-card-inner)',
            borderColor: 'var(--border-inner)'
          }}
        >
          <Sun className={`w-3.5 h-3.5 transition-all ${
            theme === 'light' ? 'text-amber-500 fill-amber-500 scale-110 drop-shadow-[0_0_6px_rgba(245,158,11,0.8)]' : 'text-slate-500'
          }`} />
          <Moon className={`w-3.5 h-3.5 transition-all ${
            theme === 'dark' ? 'text-blue-400 fill-blue-400 scale-110 drop-shadow-[0_0_6px_rgba(96,165,250,0.8)]' : 'text-slate-500'
          }`} />
        </button>

        {/* User Avatar */}
        <div 
          title="User Account"
          className="w-9 h-9 rounded-full bg-[#6366f1] flex items-center justify-center text-white text-xs font-bold shadow-md shadow-indigo-600/30 cursor-pointer border border-indigo-400/40 hover:scale-105 transition-transform"
        >
          HK
        </div>
      </div>
    </header>
  );
};
