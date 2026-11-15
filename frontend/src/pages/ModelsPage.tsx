import { useEffect, useState } from 'react';
import type { FC } from 'react';
import { Sliders } from 'lucide-react';
import type { ModelInfo } from '../types';
import { ModelsAPI } from '../services/api';

export const ModelsPage: FC = () => {
  const [models, setModels] = useState<ModelInfo[]>([]);

  useEffect(() => {
    ModelsAPI.getModels().then(setModels);
  }, []);

  return (
    <div className="p-8 max-w-[1400px] mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Sliders className="w-6 h-6 text-cyan-400" />
            Model Management & Architecture
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Official English voice cloning model configurations, CPU inference optimization, and memory footprints.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {models.map((m) => (
          <div key={m.id} className="bg-[#111425] border border-[#1e233d] rounded-2xl p-6 space-y-4 shadow-xl">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-base font-bold text-white">{m.display_name}</h3>
                <span className="text-xs text-slate-400">Language: {m.language}</span>
              </div>
              <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold border ${
                m.status === 'Loaded'
                  ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                  : 'bg-slate-700/30 text-slate-400 border-slate-600/30'
              }`}>
                {m.status}
              </span>
            </div>

            <div className="space-y-2 text-xs text-slate-300">
              <div className="flex justify-between py-1 border-b border-[#1c213a]">
                <span className="text-slate-400">Inference Device</span>
                <span className="font-semibold text-emerald-400 font-mono">{m.device}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#1c213a]">
                <span className="text-slate-400">RAM Footprint</span>
                <span className="font-semibold text-blue-300 font-mono">{m.ram_usage_mb} MB</span>
              </div>
              <div className="flex justify-between py-1 border-b border-[#1c213a]">
                <span className="text-slate-400">Native Sample Rate</span>
                <span className="font-semibold text-slate-200 font-mono">{m.sample_rate} Hz</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">License</span>
                <span className="font-semibold text-purple-300">{m.license}</span>
              </div>
            </div>

            <div className="pt-2">
              <button
                disabled={m.status === 'Loaded'}
                className="w-full py-2.5 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 text-xs font-semibold disabled:opacity-40 transition-colors"
              >
                {m.status === 'Loaded' ? 'Active Model' : 'Load Model'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
