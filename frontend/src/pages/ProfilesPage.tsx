import { useState } from 'react';
import type { FC, FormEvent } from 'react';
import { Users, Plus, Trash2, CheckCircle, X } from 'lucide-react';
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

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!name || !transcript || !file) {
      alert("Please enter Name, Reference Transcript, and select an audio file.");
      return;
    }
    const formData = new FormData();
    formData.append('name', name);
    formData.append('reference_transcript', transcript);
    formData.append('description', desc);
    formData.append('audio_file', file);

    try {
      await ProfileAPI.createProfile(formData);
      setShowModal(false);
      setName('');
      setTranscript('');
      setDesc('');
      setFile(null);
      onRefresh();
    } catch (err: any) {
      alert(err.response?.data?.detail || err.message);
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
                <label className="block font-medium mb-1" style={{ color: 'var(--text-primary)' }}>Reference Transcript *</label>
                <textarea
                  required
                  rows={3}
                  value={transcript}
                  onChange={(e) => setTranscript(e.target.value)}
                  placeholder="Exact text spoken in the audio file"
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
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="w-full text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-purple-600 file:text-white hover:file:bg-purple-500 cursor-pointer"
                />
              </div>

              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 py-2.5 rounded-xl border font-semibold"
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
                  className="flex-1 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold transition-colors"
                >
                  Save Profile
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
