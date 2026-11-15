import React from 'react';
import { Settings, Shield, Save } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  return (
    <div className="p-8 max-w-[1400px] mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Settings className="w-6 h-6 text-purple-400" />
          Application & Audio Settings
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Hardware configuration, default sample rates, local storage paths, and ethical voice consent notice.
        </p>
      </div>

      <div className="bg-[#111425] border border-[#1e233d] rounded-2xl p-6 space-y-5 shadow-xl max-w-2xl">
        <div className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 font-semibold mb-1">Default Output Audio Sample Rate</label>
            <select className="w-full bg-[#161a2e] border border-[#232948] rounded-xl p-2.5 text-slate-200">
              <option>24,000 Hz (Optimal for IndicF5 / High Fidelity)</option>
              <option>22,050 Hz (Standard Speech)</option>
              <option>16,000 Hz (Compact)</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Local Storage Directory</label>
            <input 
              type="text" 
              readOnly 
              value="c:\Users\Jeevitha J R\Desktop\project2\data" 
              className="w-full bg-[#161a2e] border border-[#232948] rounded-xl p-2.5 text-slate-400 font-mono"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Max Upload Audio File Size</label>
            <input 
              type="text" 
              readOnly 
              value="50 MB" 
              className="w-full bg-[#161a2e] border border-[#232948] rounded-xl p-2.5 text-slate-400 font-mono"
            />
          </div>

          {/* Ethical Voice Consent Notice */}
          <div className="bg-[#191e36] border border-purple-500/30 rounded-xl p-4 space-y-2 mt-4">
            <div className="flex items-center gap-2 text-purple-300 font-bold">
              <Shield className="w-4 h-4 text-purple-400" />
              <span>Voice Consent & Responsible AI Notice</span>
            </div>
            <p className="text-[11px] text-slate-300 leading-relaxed">
              VoiceStudio is intended exclusively for authorized voice cloning, accessibility, creative narration, and educational research. Users must obtain explicit consent from individuals before recording or cloning their voice.
            </p>
          </div>
        </div>

        <button 
          onClick={() => alert("Settings saved.")}
          className="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs flex items-center gap-2 shadow-lg shadow-purple-900/30 transition-all"
        >
          <Save className="w-4 h-4" />
          Save Preferences
        </button>
      </div>
    </div>
  );
};
