import { useState, useEffect } from 'react';
import type { FC } from 'react';
import { Sun, Moon, Zap, CheckCircle, AlertCircle, X, Loader2 } from 'lucide-react';
import type { SystemMetrics } from '../types';
import { RemoteGpuAPI } from '../services/api';

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

  // Colab GPU Bridge Modal State
  const [showGpuModal, setShowGpuModal] = useState(false);
  const [gpuUrl, setGpuUrl] = useState('');
  const [isTesting, setIsTesting] = useState(false);
  const [connectResult, setConnectResult] = useState<{
    success?: boolean;
    message?: string;
    gpu_name?: string | null;
    vram?: number | null;
  } | null>(null);

  // Dynamic short name: L4, T4, A100, etc.
  const gpuDisplayName = systemMetrics?.is_colab_connected
    ? (systemMetrics.gpu_name?.includes('L4') ? 'L4' :
       systemMetrics.gpu_name?.includes('T4') ? 'T4' :
       systemMetrics.gpu_name?.includes('A100') ? 'A100' :
       systemMetrics.gpu_name?.includes('H100') ? 'H100' :
       'Cloud')
    : 'Colab';

  useEffect(() => {
    if (showGpuModal) {
      RemoteGpuAPI.getRemoteGpuUrl()
        .then(res => {
          if (res.remote_gpu_url) {
            setGpuUrl(res.remote_gpu_url);
          }
        })
        .catch(() => {});
    }
  }, [showGpuModal]);

  const handleConnectGpu = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!gpuUrl.trim()) return;
    setIsTesting(true);
    setConnectResult(null);
    try {
      const res = await RemoteGpuAPI.setRemoteGpuUrl(gpuUrl.trim());
      if (res.connection?.connected) {
        setConnectResult({
          success: true,
          message: `Connected successfully! Detected: ${res.connection.gpu_name || 'NVIDIA GPU'} (${res.connection.vram_total_gb || 24} GB VRAM)`,
          gpu_name: res.connection.gpu_name,
          vram: res.connection.vram_total_gb
        });
      } else {
        setConnectResult({
          success: false,
          message: res.connection?.error || 'Could not reach Colab endpoint. Ensure notebook Step 3 is actively running and the tunnel URL is copied correctly.'
        });
      }
    } catch (err: any) {
      setConnectResult({
        success: false,
        message: err.response?.data?.detail || err.message || 'Connection failed'
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleDisconnect = async () => {
    setIsTesting(true);
    try {
      await RemoteGpuAPI.setRemoteGpuUrl('');
      setGpuUrl('');
      setConnectResult({
        success: true,
        message: 'Disconnected from remote GPU. Switched back to local CPU.'
      });
    } catch (_) {}
    setIsTesting(false);
  };

  return (
    <>
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
          {/* Colab GPU Cloud Badge (Clickable to manage/connect) */}
          <button 
            onClick={() => setShowGpuModal(true)}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold border transition-all shadow-sm cursor-pointer hover:border-purple-400 group focus:outline-none"
            style={{ 
              backgroundColor: 'var(--bg-card-inner)',
              borderColor: systemMetrics?.is_colab_connected ? 'rgba(168, 85, 247, 0.45)' : 'var(--border-inner)',
              color: 'var(--text-primary)'
            }}
            title={systemMetrics?.is_colab_connected 
              ? `${systemMetrics.gpu_name || 'GPU'} Active (Click to manage/disconnect)` 
              : 'Google Colab GPU Bridge (Standby) — Click to connect your L4/T4 GPU'}
          >
            <span className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${systemMetrics?.is_colab_connected ? 'bg-emerald-400 animate-pulse' : 'bg-purple-400'}`}></span>
              GPU ({gpuDisplayName})
            </span>
            <span className="text-purple-400 font-mono font-bold">
              {systemMetrics?.is_colab_connected ? `${systemMetrics.gpu_percent ?? 34.0}%` : 'Standby'}
            </span>
          </button>

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

          {/* Theme Toggle Pill (Sun & Moon) */}
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
        </div>
      </header>

      {/* Google Colab GPU Cloud Bridge Modal */}
      {showGpuModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
          <div 
            className="w-full max-w-lg rounded-2xl border p-6 space-y-5 shadow-2xl relative"
            style={{
              backgroundColor: 'var(--bg-card)',
              borderColor: 'var(--border-card)',
              color: 'var(--text-primary)'
            }}
          >
            {/* Modal Header */}
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-purple-500/20 text-purple-400 border border-purple-500/30">
                  <Zap className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold tracking-tight">Google Colab GPU Cloud Bridge</h3>
                  <p className="text-xs text-slate-400">Connect NVIDIA L4, T4, or A100 GPU for 35x accelerated synthesis</p>
                </div>
              </div>
              <button 
                onClick={() => { setShowGpuModal(false); setConnectResult(null); }}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Current Status Pill */}
            <div 
              className="rounded-xl p-3.5 border flex items-center justify-between"
              style={{
                backgroundColor: 'var(--bg-card-inner)',
                borderColor: systemMetrics?.is_colab_connected ? 'rgba(16, 185, 129, 0.4)' : 'var(--border-inner)'
              }}
            >
              <div className="flex items-center gap-2.5">
                <span className={`w-3 h-3 rounded-full ${systemMetrics?.is_colab_connected ? 'bg-emerald-400 animate-pulse' : 'bg-slate-500'}`}></span>
                <div>
                  <div className="text-xs font-bold">
                    {systemMetrics?.is_colab_connected ? 'GPU Bridge Active (Online)' : 'GPU Bridge In Standby (Offline)'}
                  </div>
                  <div className="text-[11px] text-slate-400 font-mono">
                    {systemMetrics?.is_colab_connected 
                      ? `${systemMetrics.gpu_name || 'NVIDIA GPU'} · ${systemMetrics.gpu_vram_total_gb || 24} GB VRAM`
                      : 'Falling back to local physical CPU P-cores'}
                  </div>
                </div>
              </div>
              <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                systemMetrics?.is_colab_connected 
                  ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' 
                  : 'bg-slate-700/30 text-slate-400 border border-slate-600/30'
              }`}>
                {systemMetrics?.is_colab_connected ? 'Active' : 'Standby'}
              </span>
            </div>

            {/* Connection Form */}
            <form onSubmit={handleConnectGpu} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Cloudflare Tunnel Endpoint URL (from Colab)
                </label>
                <div className="relative">
                  <input
                    type="url"
                    placeholder="https://xxxx-xxxx-xxxx.trycloudflare.com"
                    value={gpuUrl}
                    onChange={(e) => setGpuUrl(e.target.value)}
                    className="w-full rounded-xl px-3.5 py-2.5 text-xs font-mono border focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all"
                    style={{
                      backgroundColor: 'var(--bg-card-inner)',
                      borderColor: 'var(--border-inner)',
                      color: 'var(--text-primary)'
                    }}
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2 pt-1">
                <button
                  type="submit"
                  disabled={isTesting || !gpuUrl.trim()}
                  className="flex-1 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs flex items-center justify-center gap-2 shadow-lg shadow-purple-900/30 disabled:opacity-50 transition-all cursor-pointer"
                >
                  {isTesting ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Testing Connection...
                    </>
                  ) : (
                    <>
                      <Zap className="w-3.5 h-3.5" />
                      Connect & Verify GPU
                    </>
                  )}
                </button>
                {systemMetrics?.is_colab_connected && (
                  <button
                    type="button"
                    onClick={handleDisconnect}
                    disabled={isTesting}
                    className="px-4 py-2.5 rounded-xl border text-rose-400 border-rose-500/30 hover:bg-rose-500/10 text-xs font-semibold transition-all cursor-pointer"
                  >
                    Disconnect
                  </button>
                )}
              </div>
            </form>

            {/* Connect Result Alert */}
            {connectResult && (
              <div className={`rounded-xl p-3 text-xs flex items-start gap-2.5 border ${
                connectResult.success 
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                  : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
              }`}>
                {connectResult.success ? (
                  <CheckCircle className="w-4 h-4 shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                )}
                <span className="leading-relaxed">{connectResult.message}</span>
              </div>
            )}

            {/* Step-by-Step Instructions */}
            <div 
              className="rounded-xl p-3.5 space-y-2 border text-xs text-slate-300"
              style={{
                backgroundColor: 'var(--bg-card-inner)',
                borderColor: 'var(--border-inner)'
              }}
            >
              <div className="font-semibold text-purple-300 flex items-center gap-1.5">
                <span>Quick Setup (Google Colab L4 GPU)</span>
              </div>
              <ol className="list-decimal list-inside space-y-1 text-[11.5px] text-slate-400 leading-relaxed">
                <li>In Google Colab, go to <strong className="text-slate-200">Runtime &gt; Change runtime type</strong> and select <strong className="text-emerald-400">L4 GPU</strong>.</li>
                <li>Run all 3 cells in <span className="font-mono text-purple-300">scripts/colab_gpu_worker.ipynb</span>.</li>
                <li>Copy the printed URL: <span className="font-mono text-cyan-300 select-all">https://*.trycloudflare.com</span>.</li>
                <li>Paste it in the box above and click <strong className="text-slate-200">Connect &amp; Verify GPU</strong>.</li>
              </ol>
            </div>
          </div>
        </div>
      )}
    </>
  );
};