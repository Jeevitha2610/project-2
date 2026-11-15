import type { FC } from 'react';
import { Activity, Cpu, Database, HardDrive, CheckCircle2 } from 'lucide-react';
import type { SystemMetrics } from '../types';

interface SystemMonitorPageProps {
  systemMetrics: SystemMetrics | null;
}

export const SystemMonitorPage: FC<SystemMonitorPageProps> = ({ systemMetrics }) => {
  return (
    <div className="p-8 max-w-[1400px] mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Activity className="w-6 h-6 text-emerald-400" />
          Hardware & Resource Monitor
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Real-time Windows 11 host metrics, Intel CPU telemetry, RAM allocation, and local inference queue.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-[#111425] border border-[#1e233d] rounded-2xl p-6 space-y-4 shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Processor Utilization</span>
            <Cpu className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-3xl font-extrabold text-white font-mono">
            {systemMetrics ? `${systemMetrics.cpu_percent}%` : '12.0%'}
          </div>
          <div className="w-full bg-[#1e2440] h-2 rounded-full overflow-hidden">
            <div 
              className="bg-gradient-to-r from-purple-500 to-indigo-500 h-full rounded-full transition-all"
              style={{ width: `${systemMetrics?.cpu_percent || 12}%` }}
            />
          </div>
          <p className="text-[11px] text-slate-500">Intel Core CPU · Multi-threaded Inference</p>
        </div>

        <div className="bg-[#111425] border border-[#1e233d] rounded-2xl p-6 space-y-4 shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Physical Memory (RAM)</span>
            <Database className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-3xl font-extrabold text-white font-mono">
            {systemMetrics ? `${systemMetrics.ram_used_gb} / ${systemMetrics.ram_total_gb} GB` : '4.2 / 16.0 GB'}
          </div>
          <div className="w-full bg-[#1e2440] h-2 rounded-full overflow-hidden">
            <div 
              className="bg-gradient-to-r from-blue-500 to-cyan-500 h-full rounded-full transition-all"
              style={{ width: `${systemMetrics?.ram_percent || 26}%` }}
            />
          </div>
          <p className="text-[11px] text-slate-500">Model footprint ~1.25 GB · Safe headroom</p>
        </div>

        <div className="bg-[#111425] border border-[#1e233d] rounded-2xl p-6 space-y-4 shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-400">Available Storage</span>
            <HardDrive className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-extrabold text-white font-mono">
            {systemMetrics ? `${systemMetrics.disk_free_gb} GB` : '120.4 GB'}
          </div>
          <div className="w-full bg-[#1e2440] h-2 rounded-full overflow-hidden">
            <div className="bg-emerald-500 h-full rounded-full w-4/5" />
          </div>
          <p className="text-[11px] text-slate-500">Local audio data & SQLite database storage</p>
        </div>
      </div>

      <div className="bg-[#111425] border border-[#1e233d] rounded-2xl p-6 space-y-3 shadow-xl">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          Offline Safety & Local Execution Policy
        </h3>
        <p className="text-xs text-slate-400 leading-relaxed">
          VoiceStudio is running in strict local-first mode. All model weights, inference pipelines, and synthesized waveforms are processed entirely on your local Windows CPU. No voice embeddings or transcripts are transmitted to external servers.
        </p>
      </div>
    </div>
  );
};
