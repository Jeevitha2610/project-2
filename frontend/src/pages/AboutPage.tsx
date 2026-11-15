import React from 'react';
import { Info, ShieldCheck, Layers } from 'lucide-react';

export const AboutPage: React.FC = () => {
  return (
    <div className="p-8 max-w-[1400px] mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <Info className="w-6 h-6 text-purple-400" />
          About VoiceStudio & System Architecture
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          A production-grade, local-first English voice cloning desktop web application for Windows 11.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-[#111425] border border-[#1e233d] rounded-2xl p-6 space-y-4 shadow-xl">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Layers className="w-4 h-4 text-purple-400" />
            Layered System Design
          </h3>
          <div className="space-y-3 text-xs text-slate-300">
            <div className="p-3 bg-[#161a2e] rounded-xl">
              <span className="font-bold text-purple-300 block">1. Presentation Layer</span>
              <p className="text-slate-400 text-[11px] mt-0.5">React 19 + TypeScript + Vite + Tailwind CSS + Wavesurfer.js.</p>
            </div>
            <div className="p-3 bg-[#161a2e] rounded-xl">
              <span className="font-bold text-blue-300 block">2. API Layer</span>
              <p className="text-slate-400 text-[11px] mt-0.5">FastAPI REST service with CORS, request validation, and static audio mounts.</p>
            </div>
            <div className="p-3 bg-[#161a2e] rounded-xl">
              <span className="font-bold text-cyan-300 block">3. Application & ML Layer</span>
              <p className="text-slate-400 text-[11px] mt-0.5">Reference-conditioned voice cloning engine on CPU with acoustic timbre modulation.</p>
            </div>
            <div className="p-3 bg-[#161a2e] rounded-xl">
              <span className="font-bold text-emerald-300 block">4. Data & Evaluation Layer</span>
              <p className="text-slate-400 text-[11px] mt-0.5">SQLite database with WAL mode + Levenshtein WER/CER + Speaker embedding similarity.</p>
            </div>
          </div>
        </div>

        <div className="bg-[#111425] border border-[#1e233d] rounded-2xl p-6 space-y-4 shadow-xl">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Licensing & Local-First Integrity
          </h3>
          <div className="space-y-3 text-xs text-slate-300">
            <div className="p-3 bg-[#161a2e] rounded-xl">
              <span className="font-bold text-white block">Open Source License</span>
              <p className="text-slate-400 text-[11px] mt-0.5">MIT License for Application Source; Apache-2.0 compatibility for models and evaluation.</p>
            </div>
            <div className="p-3 bg-[#161a2e] rounded-xl">
              <span className="font-bold text-white block">Strict Privacy Guarantee</span>
              <p className="text-slate-400 text-[11px] mt-0.5">Zero external telemetry, zero audio leakage. Runs entirely offline after installation.</p>
            </div>
            <div className="p-3 bg-[#161a2e] rounded-xl">
              <span className="font-bold text-white block">Hardware Optimization</span>
              <p className="text-slate-400 text-[11px] mt-0.5">Designed specifically for Windows 11 Intel 13th-Gen CPUs without GPU requirement.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
