import React, { useState } from 'react';
import { Users, Plus, Trash2, CheckCircle } from 'lucide-react';
import type { VoiceProfile } from '../types';
import { ProfileAPI } from '../services/api';

interface ProfilesPageProps {
  profiles: VoiceProfile[];
  onRefresh: () => void;
  onSelect: (p: VoiceProfile) => void;
}

export const ProfilesPage: React.FC<ProfilesPageProps> = ({ profiles, onRefresh, onSelect }) => {
  const [showModal, setShowModal] = useState(false);
  const [name, setName] = useState('');
  const [transcript, setTranscript] = useState('');
  const [desc, setDesc] = useState('');
  const [file, setFile] = useState<File | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
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
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Users className="w-6 h-6 text-purple-400" />
            Voice Profiles Management
          </h2>
          <p className="text-xs text-slate-400 mt-1">Manage, preview, and create speaker reference embeddings.</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-semibold text-xs flex items-center gap-2 shadow-lg shadow-purple-900/30 transition-all"
        >
          <Plus className="w-4 h-4" />
          Create Profile
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {profiles.map((profile) => (
          <div key={profile.id} className="bg-[#111425] border border-[#1e233d] rounded-2xl p-6 space-y-4 hover:border-purple-500/50 transition-all shadow-xl">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-base font-bold text-white">{profile.name}</h3>
                <span className="text-[11px] text-purple-400 font-medium">{profile.model_compatibility}</span>
              </div>
              <button
                onClick={() => handleDelete(profile.id, profile.name)}
                className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                title="Delete Profile"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-400 line-clamp-2 italic">
              "{profile.reference_transcript}"
            </p>

            <div className="bg-[#161a2e] rounded-xl p-3 flex justify-between items-center text-xs text-slate-300 font-mono">
              <span>{profile.audio_format.toUpperCase()} · {profile.sample_rate}Hz</span>
              <span>{profile.duration_seconds.toFixed(1)}s</span>
            </div>

            <div className="flex gap-2 pt-2">
              <button
                onClick={() => onSelect(profile)}
                className="flex-1 py-2 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
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
          <div className="bg-[#111425] border border-[#242b4a] rounded-2xl p-6 max-w-md w-full space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white">Create Voice Profile</h3>
            <form onSubmit={handleCreate} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-medium mb-1">Profile Name *</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. My English Voice"
                  className="w-full bg-[#161a2e] border border-[#232948] rounded-xl p-2.5 text-slate-200 focus:outline-none focus:border-purple-500"
                />
              </div>
              <div>
                <label className="block text-slate-300 font-medium mb-1">Reference Audio *</label>
                <input
                  type="file"
                  required
                  accept="audio/*"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="w-full bg-[#161a2e] border border-[#232948] rounded-xl p-2 text-slate-400 file:mr-2 file:py-1 file:px-2 file:rounded-lg file:border-0 file:bg-purple-600 file:text-white file:text-xs"
                />
              </div>
              <div>
                <label className="block text-slate-300 font-medium mb-1">Reference Transcript *</label>
                <textarea
                  required
                  rows={3}
                  value={transcript}
                  onChange={(e) => setTranscript(e.target.value)}
                  placeholder="Exact words spoken in the audio file"
                  className="w-full bg-[#161a2e] border border-[#232948] rounded-xl p-2.5 text-slate-200 focus:outline-none focus:border-purple-500 resize-none"
                />
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 bg-[#161a2e] text-slate-400 hover:text-slate-200 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-xl font-semibold"
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
