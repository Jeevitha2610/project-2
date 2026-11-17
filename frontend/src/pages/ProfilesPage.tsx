import { useState } from 'react';
import type { FC, FormEvent } from 'react';
import { Users, Plus, Trash2, CheckCircle, X, Loader2 } from 'lucide-react';
import type { VoiceProfile } from '../types';
import { ProfileAPI } from '../services/api';

interface ProfilesPageProps {
  profiles: VoiceProfile[];
  onRefresh: () => void;
  onSelect: (p: VoiceProfile) => void;
}

export const ProfilesPage: FC<ProfilesPageProps> = ({ profiles, onRefresh, onSelect }) => {
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState('');
  const [transcript, setTranscript] = useState('');
  const [desc, setDesc] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [pipelineStage, setPipelineStage] = useState<'idle' | 'uploading' | 'denoising' | 'transcribing' | 'ready'>('idle');
  const [pipelinePercent, setPipelinePercent] = useState(0);
  const [uploadBytePercent, setUploadBytePercent] = useState(0);
  const [pipelineStatus, setPipelineStatus] = useState('');

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!name || !file) {
      alert("Please enter Name and select an audio file.");
      return;
    }
    const formData = new FormData();
    formData.append('name', name);
    if (transcript.trim()) {
      formData.append('reference_transcript', transcript);
    }
    formData.append('description', desc);
    formData.append('audio_file', file);

    setIsSaving(true);
    setPipelineStage('uploading');
    setPipelinePercent(10);
    setUploadBytePercent(0);
    setPipelineStatus(`Stage 1/4: Uploading "${file.name}"...`);

    let conversionPolling: any = null;

    try {
      conversionPolling = setInterval(async () => {
        try {
          const prog = await ProfileAPI.getProcessingProgress();
          if (prog && prog.stage) {
            if (prog.stage === 'denoising') {
              setPipelineStage('denoising');
              setPipelinePercent(prev => Math.max(prev, 55));
              setPipelineStatus(`Stage 2/4: ${prog.message || 'Denoising audio...'}`);
            } else if (prog.stage === 'transcribing') {
              setPipelineStage('transcribing');
              setPipelinePercent(prev => Math.max(prev, 82));
              setPipelineStatus(`Stage 3/4: ${prog.message || 'Transcribing with Whisper...'}`);
            } else if (prog.stage === 'finalizing') {
              setPipelineStage('transcribing');
              setPipelinePercent(prev => Math.max(prev, 94));
              setPipelineStatus(`Stage 3/4: Finalizing voice profile...`);
            }
          }
        } catch (_) {}
      }, 250);

      await ProfileAPI.createProfile(formData, (p) => {
        setUploadBytePercent(p.percent);
        if (p.percent < 100) {
          setPipelineStage('uploading');
          const mapped = Math.min(30, Math.round((p.percent / 100) * 30));
          setPipelinePercent(mapped);
          setPipelineStatus(`Stage 1/4: Uploading ${p.percent}% (${(p.loaded / 1024 / 1024).toFixed(1)} MB / ${(p.total / 1024 / 1024).toFixed(1)} MB)`);
        } else {
          setUploadBytePercent(100);
          setPipelineStage('denoising');
          setPipelinePercent(prev => Math.max(prev, 40));
          setPipelineStatus('Stage 2/4: Upload complete (100%) ⟶ Denoising audio...');
        }
      });

      clearInterval(conversionPolling);
      setPipelineStage('ready');
      setPipelinePercent(100);
      setPipelineStatus('Stage 4/4: Ready! Profile created successfully.');

      setTimeout(() => {
        setShowModal(false);
        setName('');
        setTranscript('');
        setDesc('');
        setFile(null);
        setPipelineStage('idle');
        setPipelinePercent(0);
        setPipelineStatus('');
        onRefresh();
      }, 800);
    } catch (err: any) {
      if (conversionPolling) clearInterval(conversionPolling);
      setPipelineStage('idle');
      alert(err.response?.data?.detail || err.message);
    } finally {
      if (conversionPolling) clearInterval(conversionPolling);
      setIsSaving(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (confirm(`Are you sure you want to delete profile "${name}"?`)) {
      try {
        await ProfileAPI.deleteProfile(id);
        onRefresh();
      } catch (err: any) {
        alert(err.response?.data?.detail || err.message);
      }
    }
  };

  return (
    <div className="p-8 max-w-[1400px] mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
            <Users className="w-6 h-6 text-purple-400" />
            Voice Profiles Management
          </h2>
          <p className="text-xs mt-1" style={{ color: 'var(--text-secondary)' }}>
            Manage, preview, and create speaker reference embeddings.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-semibold text-xs flex items-center gap-2 shadow-lg shadow-purple-900/30 transition-all cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          Create Profile
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {profiles.map((profile) => (
          <div 
            key={profile.id} 
            className="rounded-2xl p-6 space-y-4 hover:border-purple-500/50 transition-all shadow-xl border"
            style={{
              backgroundColor: 'var(--bg-card)',
              borderColor: 'var(--border-card)'
            }}
          >
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-base font-bold" style={{ color: 'var(--text-primary)' }}>{profile.name}</h3>
                <span className="text-[11px] text-purple-400 font-medium">{profile.model_compatibility}</span>
              </div>
              <button
                onClick={() => handleDelete(profile.id, profile.name)}
                className="text-slate-400 hover:text-rose-400 transition-colors p-1 cursor-pointer"
                title="Delete Profile"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs line-clamp-2 italic" style={{ color: 'var(--text-secondary)' }}>
              "{profile.reference_transcript}"
            </p>

            <div 
              className="rounded-xl p-3 flex justify-between items-center text-xs font-mono border"
              style={{
                backgroundColor: 'var(--bg-card-inner)',
                borderColor: 'var(--border-inner)',
                color: 'var(--text-primary)'
              }}
            >
              <span>{profile.audio_format.toUpperCase()} · {profile.sample_rate}Hz</span>
              <span>{profile.duration_seconds.toFixed(1)}s</span>
            </div>

            <div className="flex gap-2 pt-2">
              <button
                onClick={() => onSelect(profile)}
                className="flex-1 py-2 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 text-purple-400 dark:text-purple-300 border border-purple-500/30 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
              >
                <CheckCircle className="w-3.5 h-3.5" />
                Select Voice
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Modal Dialog */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div 
            className="rounded-2xl p-6 max-w-md w-full space-y-4 shadow-2xl border"
            style={{
              backgroundColor: 'var(--bg-card)',
              borderColor: 'var(--border-card)'
            }}
          >
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>Create Voice Profile</h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-200">
                <X className="w-4 h-4" />
              </button>
            </div>
            <form onSubmit={handleCreate} className="space-y-4 text-xs">
              <div>
                <label className="block font-medium mb-1" style={{ color: 'var(--text-primary)' }}>Profile Name *</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Host Narrator"
                  className="w-full rounded-xl p-2.5 border focus:outline-none focus:border-purple-500"
                  style={{
                    backgroundColor: 'var(--bg-card-inner)',
                    borderColor: 'var(--border-inner)',
                    color: 'var(--text-primary)'
                  }}
                />
              </div>

              <div>
                <label className="block font-medium mb-1" style={{ color: 'var(--text-primary)' }}>
                  Reference Transcript <span className="text-xs text-slate-400 font-normal">(Optional - auto-transcribed via Whisper if blank)</span>
                </label>
                <textarea
                  rows={3}
                  value={transcript}
                  onChange={(e) => setTranscript(e.target.value)}
                  placeholder="Leave empty to auto-transcribe with Whisper, or specify exact text"
                  className="w-full rounded-xl p-2.5 border focus:outline-none focus:border-purple-500 resize-none"
                  style={{
                    backgroundColor: 'var(--bg-card-inner)',
                    borderColor: 'var(--border-inner)',
                    color: 'var(--text-primary)'
                  }}
                />
              </div>

              <div>
                <label className="block font-medium mb-1" style={{ color: 'var(--text-primary)' }}>Description</label>
                <input
                  type="text"
                  value={desc}
                  onChange={(e) => setDesc(e.target.value)}
                  placeholder="Optional notes about this voice"
                  className="w-full rounded-xl p-2.5 border focus:outline-none focus:border-purple-500"
                  style={{
                    backgroundColor: 'var(--bg-card-inner)',
                    borderColor: 'var(--border-inner)',
                    color: 'var(--text-primary)'
                  }}
                />
              </div>

              <div>
                <label className="block font-medium mb-1" style={{ color: 'var(--text-primary)' }}>Audio File (WAV/MP3) *</label>
                <input
                  type="file"
                  required
                  accept="audio/*"
                  onChange={(e) => {
                    const f = e.target.files?.[0] || null;
                    setFile(f);
                    if (f && !name) {
                      setName(f.name.replace(/\.[^/.]+$/, '').trim());
                    }
                  }}
                  className="w-full text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-purple-600 file:text-white hover:file:bg-purple-500 cursor-pointer"
                />
              </div>

              {/* Multi-Stage Audio Pipeline Stepper: "Uploading (100%) ⟶ Denoising ⟶ Transcribing with Whisper... ⟶ Ready!" */}
              {pipelineStage !== 'idle' && (() => {
                const stageIndex = pipelineStage === 'uploading' ? 0 :
                                   pipelineStage === 'denoising' ? 1 :
                                   pipelineStage === 'transcribing' ? 2 :
                                   pipelineStage === 'ready' ? 3 : -1;
                return (
                  <div
                    className="rounded-xl p-3 border space-y-2.5 transition-all shadow-md"
                    style={{
                      backgroundColor: 'var(--bg-card-inner)',
                      borderColor: pipelineStage === 'ready' ? 'rgba(16, 185, 129, 0.4)' : 'rgba(168, 85, 247, 0.4)'
                    }}
                  >
                    {/* Stepper Steps Row */}
                    <div className="flex items-center justify-between gap-1 overflow-x-auto py-0.5 no-scrollbar text-[10.5px] font-semibold">
                      <span className={`px-2 py-0.5 rounded border whitespace-nowrap ${
                        stageIndex > 0 ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
                        stageIndex === 0 ? 'bg-purple-500/20 border-purple-500/50 text-purple-300' :
                        'bg-slate-800/40 border-slate-700/50 text-slate-500'
                      }`}>
                        Uploading ({uploadBytePercent}%)
                      </span>
                      <span className="text-slate-600 text-xs">⟶</span>
                      <span className={`px-2 py-0.5 rounded border whitespace-nowrap ${
                        stageIndex > 1 ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
                        stageIndex === 1 ? 'bg-purple-500/20 border-purple-500/50 text-purple-300' :
                        'bg-slate-800/40 border-slate-700/50 text-slate-500'
                      }`}>
                        Denoising
                      </span>
                      <span className="text-slate-600 text-xs">⟶</span>
                      <span className={`px-2 py-0.5 rounded border whitespace-nowrap ${
                        stageIndex > 2 ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
                        stageIndex === 2 ? 'bg-purple-500/20 border-purple-500/50 text-purple-300' :
                        'bg-slate-800/40 border-slate-700/50 text-slate-500'
                      }`}>
                        Transcribing with Whisper...
                      </span>
                      <span className="text-slate-600 text-xs">⟶</span>
                      <span className={`px-2 py-0.5 rounded border whitespace-nowrap ${
                        stageIndex >= 3 ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300 font-bold' :
                        'bg-slate-800/40 border-slate-700/50 text-slate-500'
                      }`}>
                        Ready!
                      </span>
                    </div>

                    <div className="flex justify-between text-[11px] font-semibold text-purple-300">
                      <span className="flex items-center gap-1.5 truncate max-w-[280px]">
                        {pipelineStage === 'ready' ? (
                          <CheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                        ) : (
                          <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-400 shrink-0" />
                        )}
                        <span className="truncate">{pipelineStatus}</span>
                      </span>
                      <span className="font-mono text-purple-300 font-bold ml-2 shrink-0">{pipelinePercent}%</span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden border border-purple-500/20">
                      <div
                        className={`h-full rounded-full transition-all duration-200 ${
                          pipelineStage === 'ready'
                            ? 'bg-gradient-to-r from-emerald-500 to-teal-400'
                            : 'bg-gradient-to-r from-purple-500 via-indigo-500 to-cyan-400'
                        }`}
                        style={{ width: `${pipelinePercent}%` }}
                      />
                    </div>
                  </div>
                );
              })()}

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  disabled={isSaving}
                  onClick={() => setShowModal(false)}
                  className="flex-1 py-2.5 rounded-xl border font-semibold disabled:opacity-50"
                  style={{
                    backgroundColor: 'var(--bg-card-inner)',
                    borderColor: 'var(--border-inner)',
                    color: 'var(--text-secondary)'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSaving}
                  className="flex-1 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold transition-colors disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer"
                >
                  {isSaving ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Saving...</span>
                    </>
                  ) : (
                    <span>Save Profile</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
