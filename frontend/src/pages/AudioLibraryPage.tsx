import { useEffect, useState } from 'react';
import type { FC } from 'react';
import { FileAudio } from 'lucide-react';
import type { GenerationJob, VoiceProfile } from '../types';
import { SynthesisAPI, ProfileAPI } from '../services/api';

export const AudioLibraryPage: FC = () => {
  const [history, setHistory] = useState<GenerationJob[]>([]);
  const [profiles, setProfiles] = useState<VoiceProfile[]>([]);

  useEffect(() => {
    SynthesisAPI.getHistory().then(setHistory);
    ProfileAPI.getProfiles().then(setProfiles);
  }, []);

  return (
    <div className="p-8 max-w-[1400px] mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <FileAudio className="w-6 h-6 text-blue-400" />
          Audio Library & Recordings
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Catalog of reference recordings and synthesized audio outputs.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Reference Audio Card */}
        <div className="bg-[#111425] border border-[#1e233d] rounded-2xl p-6 space-y-4 shadow-xl">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <FileAudio className="w-4 h-4 text-purple-400" />
            Reference Voice Samples ({profiles.length})
          </h3>
          <div className="space-y-2.5 max-h-96 overflow-y-auto">
            {profiles.map((p) => (
              <div key={p.id} className="bg-[#161a2e] p-3 rounded-xl flex items-center justify-between text-xs">
                <div>
                  <div className="font-semibold text-slate-200">{p.reference_audio_name}</div>
                  <div className="text-[11px] text-slate-500">{p.name} · {p.duration_seconds.toFixed(1)}s</div>
                </div>
                {p.reference_audio_url && (
                  <audio controls className="h-8 w-44" src={`http://127.0.0.1:8000${p.reference_audio_url}`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Generated Audio Card */}
        <div className="bg-[#111425] border border-[#1e233d] rounded-2xl p-6 space-y-4 shadow-xl">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <FileAudio className="w-4 h-4 text-emerald-400" />
            Generated Voice Outputs ({history.length})
          </h3>
          <div className="space-y-2.5 max-h-96 overflow-y-auto">
            {history.map((h) => (
              <div key={h.id} className="bg-[#161a2e] p-3 rounded-xl flex items-center justify-between text-xs">
                <div className="max-w-[200px] truncate">
                  <div className="font-semibold text-slate-200 truncate">{h.target_text}</div>
                  <div className="text-[11px] text-slate-500">{h.profile_name} · {h.duration_seconds.toFixed(1)}s</div>
                </div>
                {h.output_audio_url && (
                  <audio controls className="h-8 w-44" src={`http://127.0.0.1:8000${h.output_audio_url}`} />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
