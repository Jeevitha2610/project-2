import { useEffect, useState } from 'react';
import type { FC } from 'react';
import { Clock, Download, Trash2 } from 'lucide-react';
import type { GenerationJob } from '../types';
import { SynthesisAPI } from '../services/api';

export const HistoryPage: FC = () => {
  const [history, setHistory] = useState<GenerationJob[]>([]);

  const fetchHistory = () => {
    SynthesisAPI.getHistory().then(setHistory);
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleDelete = async (id: string) => {
    if (confirm("Delete this generation record?")) {
      await SynthesisAPI.deleteGeneration(id);
      fetchHistory();
    }
  };

  return (
    <div className="p-8 max-w-[1400px] mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Clock className="w-6 h-6 text-purple-400" />
          Generation History
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Complete log of cloned speech utterances, settings, audio metrics, and downloads.
        </p>
      </div>

      <div className="bg-[#111425] border border-[#1e233d] rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#161a2e] text-slate-400 font-semibold border-b border-[#212747]">
              <tr>
                <th className="p-4">Target Text</th>
                <th className="p-4">Voice Profile</th>
                <th className="p-4">Duration</th>
                <th className="p-4">Similarity</th>
                <th className="p-4">WER</th>
                <th className="p-4">Inference</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1e233d] text-slate-300">
              {history.map((job) => (
                <tr key={job.id} className="hover:bg-[#161a2e]/60 transition-colors">
                  <td className="p-4 max-w-xs truncate font-medium text-white">{job.target_text}</td>
                  <td className="p-4 font-mono text-purple-300">{job.profile_name}</td>
                  <td className="p-4 font-mono">{job.duration_seconds.toFixed(1)}s</td>
                  <td className="p-4 font-mono text-emerald-400 font-bold">{(job.speaker_similarity * 100).toFixed(1)}%</td>
                  <td className="p-4 font-mono text-emerald-400 font-bold">{(job.wer * 100).toFixed(1)}%</td>
                  <td className="p-4 font-mono text-slate-400">{job.inference_time_seconds}s</td>
                  <td className="p-4 text-right space-x-2">
                    {job.output_audio_url && (
                      <a
                        href={`http://127.0.0.1:8000${job.output_audio_url}`}
                        download
                        className="inline-block p-1.5 text-slate-400 hover:text-purple-400 transition-colors"
                        title="Download WAV"
                      >
                        <Download className="w-4 h-4" />
                      </a>
                    )}
                    <button
                      onClick={() => handleDelete(job.id)}
                      className="p-1.5 text-slate-400 hover:text-rose-400 transition-colors"
                      title="Delete Record"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
              {history.length === 0 && (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500">
                    No speech generations yet. Generate speech in the Studio to view history.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
