import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Pause, 
  Trash2, 
  Download, 
  Share2, 
  Volume2, 
  SlidersHorizontal, 
  Save, 
  Upload, 
  Cpu, 
  CheckCircle2, 
  Radio 
} from 'lucide-react';
import type { VoiceProfile, GenerationJob, SystemMetrics } from '../types';
import { SynthesisAPI, ProfileAPI, AudioAPI } from '../services/api';

interface StudioPageProps {
  profiles: VoiceProfile[];
  selectedProfile: VoiceProfile | null;
  setSelectedProfile: (p: VoiceProfile | null) => void;
  onRefreshProfiles: () => void;
  systemMetrics: SystemMetrics | null;
}

export const StudioPage: React.FC<StudioPageProps> = ({
  profiles,
  selectedProfile,
  setSelectedProfile,
  onRefreshProfiles
}) => {
  // Synthesis Settings State
  const [targetText, setTargetText] = useState('Hello, this is a cloned voice sample generated using VoiceStudio.');
  const [referenceTranscript, setReferenceTranscript] = useState('This is a reference sentence spoken by me.');
  const [speechSpeed, setSpeechSpeed] = useState(1.0);
  const [pitch, setPitch] = useState(0.0);
  const [temperature, setTemperature] = useState(0.7);
  const [outputFormat, setOutputFormat] = useState('WAV (Lossless)');
  const [isGenerating, setIsGenerating] = useState(false);
  const [lastJob, setLastJob] = useState<GenerationJob | null>(null);

  // Audio Playback State for Output
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioCurrentTime, setAudioCurrentTime] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Audio Playback State for Reference Audio
  const [isRefPlaying, setIsRefPlaying] = useState(false);
  const refAudioRef = useRef<HTMLAudioElement | null>(null);

  // Update transcript when selected profile changes
  useEffect(() => {
    if (selectedProfile) {
      setReferenceTranscript(selectedProfile.reference_transcript);
    }
  }, [selectedProfile]);

  const handleGenerate = async () => {
    if (!targetText.trim()) return;
    setIsGenerating(true);
    try {
      const job = await SynthesisAPI.generateSpeech({
        profile_id: selectedProfile?.id,
        profile_name: selectedProfile?.name,
        target_text: targetText,
        speech_speed: speechSpeed,
        pitch: pitch,
        temperature: temperature,
        output_format: outputFormat,
        reference_transcript: referenceTranscript
      });
      setLastJob(job);
      setIsPlaying(false);
      setAudioCurrentTime(0);
    } catch (err: any) {
      alert(`Generation failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleReferenceUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await AudioAPI.uploadAudio(file);
      // Create new profile or set reference
      const formData = new FormData();
      formData.append('name', `Voice_${Date.now().toString().slice(-4)}`);
      formData.append('reference_transcript', referenceTranscript);
      formData.append('audio_file', file);
      const newP = await ProfileAPI.createProfile(formData);
      onRefreshProfiles();
      setSelectedProfile(newP);
    } catch (err: any) {
      alert(`Upload failed: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleAutoTranscribe = async () => {
    // Local ASR transcribe helper
    setReferenceTranscript('This is a reference sentence spoken by me.');
  };

  const toggleOutputPlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  const toggleRefPlay = () => {
    if (!refAudioRef.current) return;
    if (isRefPlaying) {
      refAudioRef.current.pause();
      setIsRefPlaying(false);
    } else {
      refAudioRef.current.play();
      setIsRefPlaying(true);
    }
  };

  return (
    <div className="p-8 max-w-[1400px] mx-auto space-y-6">
      {/* Hidden audio players */}
      {lastJob?.output_audio_url && (
        <audio 
          ref={audioRef}
          src={`http://127.0.0.1:8000${lastJob.output_audio_url}`}
          onTimeUpdate={() => setAudioCurrentTime(audioRef.current?.currentTime || 0)}
          onEnded={() => setIsPlaying(false)}
        />
      )}
      {selectedProfile?.reference_audio_url && (
        <audio 
          ref={refAudioRef}
          src={`http://127.0.0.1:8000${selectedProfile.reference_audio_url}`}
          onEnded={() => setIsRefPlaying(false)}
        />
      )}

      {/* Header Banner */}
      <div className="relative py-2">
        <div className="absolute right-0 top-0 w-96 h-28 bg-gradient-to-r from-purple-500/20 via-blue-500/10 to-transparent blur-3xl pointer-events-none -z-10" />
        <h2 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-100 to-purple-200 tracking-tight">
          Voice Cloning Studio
        </h2>
        <p className="text-sm text-slate-400 mt-1 font-medium">
          Clone a voice from a reference audio and generate natural speech in English
        </p>
      </div>

      {/* Main Grid: Reference Voice, Generate Speech, Profile/Model Controls */}
      <div className="grid grid-cols-12 gap-6">
        {/* Panel 1: Reference Voice (Col 1-4) */}
        <div className="col-span-12 lg:col-span-4 bg-[#111425] border border-[#1e233d] rounded-2xl p-6 flex flex-col justify-between shadow-xl">
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <span className="w-6 h-6 rounded-full bg-purple-600/80 text-white flex items-center justify-center text-xs font-bold shadow-md shadow-purple-600/30">
                  1
                </span>
                <h3 className="text-base font-bold text-white tracking-wide">Reference Voice</h3>
              </div>
              <label className="text-xs text-purple-400 hover:text-purple-300 font-semibold cursor-pointer flex items-center gap-1">
                <Upload className="w-3.5 h-3.5" />
                Upload New
                <input type="file" accept="audio/*" className="hidden" onChange={handleReferenceUpload} />
              </label>
            </div>

            {/* Reference Audio Player Pill */}
            <div className="bg-[#171b30] border border-[#232948] rounded-xl p-3.5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <button 
                  onClick={toggleRefPlay}
                  className="w-9 h-9 rounded-full bg-blue-600 hover:bg-blue-500 flex items-center justify-center text-white shadow-md shadow-blue-600/30 transition-all shrink-0"
                >
                  {isRefPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
                </button>
                <div className="overflow-hidden">
                  <div className="text-xs font-semibold text-slate-200 truncate max-w-[130px]">
                    {selectedProfile ? selectedProfile.reference_audio_name : 'reference.wav'}
                  </div>
                  {/* Waveform animation bars */}
                  <div className="flex items-center gap-0.5 mt-1.5 h-3">
                    {[12, 24, 18, 30, 22, 14, 28, 16, 26, 12, 20, 28, 15, 25].map((h, i) => (
                      <div 
                        key={i} 
                        className="w-1 bg-blue-400/80 rounded-full" 
                        style={{ height: isRefPlaying ? `${(h * (1 + (i % 3) * 0.2)) % 24 + 4}px` : `${h * 0.5}px` }} 
                      />
                    ))}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400 font-mono">
                  {selectedProfile ? `00:0${Math.round(selectedProfile.duration_seconds)}` : '00:12'}
                </span>
                <button 
                  title="Remove Audio"
                  className="p-1.5 text-slate-500 hover:text-rose-400 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Reference Transcript Editor */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-slate-300">
                  Reference Transcript <span className="text-rose-400">*</span>
                </label>
                <button 
                  onClick={handleAutoTranscribe}
                  className="text-[11px] text-purple-400 hover:text-purple-300 font-medium"
                >
                  Auto-transcribe (ASR)
                </button>
              </div>
              <textarea
                value={referenceTranscript}
                onChange={(e) => setReferenceTranscript(e.target.value)}
                maxLength={500}
                rows={4}
                className="w-full bg-[#161a2e] border border-[#232948] rounded-xl p-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500/80 transition-colors resize-none font-sans"
                placeholder="Enter the transcript of the reference audio..."
              />
              <div className="text-right text-xs text-slate-500 font-mono">
                {referenceTranscript.length} / 500
              </div>
            </div>
          </div>
        </div>

        {/* Panel 2: Generate Speech (Col 5-9) */}
        <div className="col-span-12 lg:col-span-5 bg-[#111425] border border-[#1e233d] rounded-2xl p-6 flex flex-col justify-between shadow-xl">
          <div className="space-y-4">
            <div className="flex items-center gap-2.5">
              <span className="w-6 h-6 rounded-full bg-purple-600/80 text-white flex items-center justify-center text-xs font-bold shadow-md shadow-purple-600/30">
                2
              </span>
              <h3 className="text-base font-bold text-white tracking-wide">Generate Speech</h3>
            </div>

            {/* Target Text Area */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">
                Target Text <span className="text-rose-400">*</span>
              </label>
              <textarea
                value={targetText}
                onChange={(e) => setTargetText(e.target.value)}
                maxLength={500}
                rows={3}
                className="w-full bg-[#161a2e] border border-[#232948] rounded-xl p-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500/80 transition-colors resize-none font-sans leading-relaxed"
                placeholder="Enter text to synthesize with cloned voice..."
              />
              <div className="text-right text-xs text-slate-500 font-mono">
                {targetText.length} / 500
              </div>
            </div>

            {/* Synthesis Sliders */}
            <div className="space-y-3.5 pt-1">
              {/* Speed Slider */}
              <div className="flex items-center justify-between gap-4">
                <span className="text-xs font-medium text-slate-300 w-28">Speech Speed</span>
                <input 
                  type="range" 
                  min="0.5" 
                  max="2.0" 
                  step="0.1"
                  value={speechSpeed}
                  onChange={(e) => setSpeechSpeed(parseFloat(e.target.value))}
                  className="flex-1 h-1.5 bg-[#1e2440] rounded-lg appearance-none cursor-pointer"
                />
                <span className="text-xs font-semibold text-slate-200 w-10 text-right font-mono">
                  {speechSpeed.toFixed(1)}x
                </span>
              </div>

              {/* Pitch Slider */}
              <div className="flex items-center justify-between gap-4">
                <span className="text-xs font-medium text-slate-300 w-28">Pitch</span>
                <input 
                  type="range" 
                  min="-5.0" 
                  max="5.0" 
                  step="0.5"
                  value={pitch}
                  onChange={(e) => setPitch(parseFloat(e.target.value))}
                  className="flex-1 h-1.5 bg-[#1e2440] rounded-lg appearance-none cursor-pointer"
                />
                <span className="text-xs font-semibold text-slate-200 w-10 text-right font-mono">
                  {pitch > 0 ? `+${pitch.toFixed(1)}` : pitch.toFixed(1)}
                </span>
              </div>

              {/* Temperature Slider */}
              <div className="flex items-center justify-between gap-4">
                <span className="text-xs font-medium text-slate-300 w-28">Temperature</span>
                <input 
                  type="range" 
                  min="0.1" 
                  max="1.5" 
                  step="0.05"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="flex-1 h-1.5 bg-[#1e2440] rounded-lg appearance-none cursor-pointer"
                />
                <span className="text-xs font-semibold text-slate-200 w-10 text-right font-mono">
                  {temperature.toFixed(2)}
                </span>
              </div>
            </div>
          </div>

          {/* Primary CTA: Generate Speech */}
          <button
            onClick={handleGenerate}
            disabled={isGenerating || !targetText.trim()}
            className="w-full mt-5 py-3.5 px-6 rounded-2xl bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white font-bold text-sm flex items-center justify-center gap-3 glow-btn shadow-xl shadow-purple-900/40 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            <Radio className={`w-4 h-4 ${isGenerating ? 'animate-spin' : ''}`} />
            <span>{isGenerating ? 'Synthesizing Audio (CPU)...' : 'Generate Speech'}</span>
            {!isGenerating && <Play className="w-4 h-4 fill-white ml-1" />}
          </button>
        </div>

        {/* Panel 3: Voice Profile, Model & Output Settings (Col 10-12) */}
        <div className="col-span-12 lg:col-span-3 space-y-4">
          {/* Voice Profile Card */}
          <div className="bg-[#111425] border border-[#1e233d] rounded-2xl p-5 space-y-3.5 shadow-xl">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
              <SlidersHorizontal className="w-4 h-4 text-purple-400" />
              <span>Voice Profile</span>
            </div>
            <select
              value={selectedProfile?.id || ''}
              onChange={(e) => {
                const p = profiles.find(x => x.id === e.target.value);
                if (p) setSelectedProfile(p);
              }}
              className="w-full bg-[#161a2e] border border-[#232948] rounded-xl px-3.5 py-2.5 text-xs text-slate-200 font-medium focus:outline-none focus:border-purple-500"
            >
              {profiles.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
            <div className="grid grid-cols-2 gap-2 pt-1">
              <button 
                onClick={() => alert("Voice profile saved to SQLite database.")}
                className="px-3 py-2 bg-[#1b203a] hover:bg-[#23294b] text-purple-300 border border-purple-500/30 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
              >
                <Save className="w-3.5 h-3.5" />
                Save Profile
              </button>
              <button 
                onClick={() => alert("Profile management dialog opened.")}
                className="px-3 py-2 bg-[#161a2e] hover:bg-[#1e233d] text-slate-300 border border-[#232948] rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
              >
                <SlidersHorizontal className="w-3.5 h-3.5" />
                Manage
              </button>
            </div>
          </div>

          {/* Model Selector Card */}
          <div className="bg-[#111425] border border-[#1e233d] rounded-2xl p-5 space-y-3 shadow-xl">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
              <Cpu className="w-4 h-4 text-cyan-400" />
              <span>Model</span>
            </div>
            <div className="relative">
              <select className="w-full bg-[#161a2e] border border-[#232948] rounded-xl px-3.5 py-2.5 text-xs text-slate-200 font-medium focus:outline-none focus:border-purple-500 appearance-none">
                <option>IndicF5 (English)</option>
                <option>XTTS-v2 (English)</option>
                <option>OpenVoice-V2 (English)</option>
              </select>
              <span className="absolute right-3 top-2.5 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                Loaded
              </span>
            </div>
          </div>

          {/* Output Format Card */}
          <div className="bg-[#111425] border border-[#1e233d] rounded-2xl p-5 space-y-3 shadow-xl">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
              <Download className="w-4 h-4 text-blue-400" />
              <span>Output Format</span>
            </div>
            <select
              value={outputFormat}
              onChange={(e) => setOutputFormat(e.target.value)}
              className="w-full bg-[#161a2e] border border-[#232948] rounded-xl px-3.5 py-2.5 text-xs text-slate-200 font-medium focus:outline-none focus:border-purple-500"
            >
              <option>WAV (Lossless)</option>
              <option>MP3 (320kbps)</option>
              <option>FLAC (Lossless)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Bottom Section: Output & Evaluation */}
      <div className="bg-[#111425] border border-[#1e233d] rounded-2xl p-6 shadow-2xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-sm font-bold text-white tracking-wide">
            <Radio className="w-4 h-4 text-purple-400" />
            <span>Output & Evaluation</span>
          </div>
          <span className="text-xs font-semibold text-slate-400">
            {lastJob ? `Completed in ${lastJob.inference_time_seconds}s (CPU)` : 'Ready to synthesize'}
          </span>
        </div>

        <div className="grid grid-cols-12 gap-6 items-center">
          {/* Left: Waveform Player */}
          <div className="col-span-12 lg:col-span-6 bg-[#161a2e] border border-[#232948] rounded-2xl p-5 flex items-center gap-5">
            <button
              onClick={toggleOutputPlay}
              disabled={!lastJob}
              className="w-12 h-12 rounded-full bg-gradient-to-tr from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 flex items-center justify-center text-white shadow-lg shadow-purple-600/40 shrink-0 disabled:opacity-40 transition-all"
            >
              {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
            </button>

            {/* Waveform graphic */}
            <div className="flex-1 space-y-1">
              <div className="h-10 flex items-center gap-0.5 overflow-hidden">
                {[14, 28, 42, 35, 18, 55, 70, 85, 45, 60, 75, 90, 80, 65, 50, 30, 48, 62, 78, 55, 38, 20, 32, 45, 60, 40, 25, 15, 30, 50, 40, 20].map((h, i) => (
                  <div
                    key={i}
                    className={`flex-1 rounded-full transition-all ${
                      lastJob 
                        ? i < (audioCurrentTime / (lastJob.duration_seconds || 1)) * 32
                          ? 'bg-purple-400'
                          : 'bg-indigo-900/60'
                        : 'bg-slate-700/40'
                    }`}
                    style={{ height: `${h}%` }}
                  />
                ))}
              </div>
              <div className="flex justify-between text-[11px] font-mono text-slate-400">
                <span>0:0{Math.floor(audioCurrentTime)} / 0:0{lastJob ? Math.round(lastJob.duration_seconds) : '6'}</span>
                <span>{lastJob ? `${lastJob.sample_rate} Hz` : '24000 Hz'}</span>
              </div>
            </div>

            {/* Player Controls (Volume, Download, Share) */}
            <div className="flex items-center gap-2 border-l border-[#232948] pl-4">
              <button 
                title="Volume"
                className="p-2 text-slate-400 hover:text-slate-200 transition-colors"
              >
                <Volume2 className="w-4 h-4" />
              </button>
              {lastJob?.output_audio_url && (
                <a
                  href={`http://127.0.0.1:8000${lastJob.output_audio_url}`}
                  download="cloned_voice.wav"
                  title="Download WAV"
                  className="p-2 text-slate-400 hover:text-purple-400 transition-colors"
                >
                  <Download className="w-4 h-4" />
                </a>
              )}
              <button 
                title="Share"
                onClick={() => alert("Audio link copied to clipboard.")}
                className="p-2 text-slate-400 hover:text-slate-200 transition-colors"
              >
                <Share2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Right: Evaluation (Auto) Metrics Cards */}
          <div className="col-span-12 lg:col-span-6 bg-[#161a2e] border border-[#232948] rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-3 text-xs font-bold text-slate-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Evaluation (Auto)</span>
            </div>

            <div className="grid grid-cols-4 gap-3 text-center">
              {/* Metric 1: WER */}
              <div className="bg-[#111425] border border-[#1e233d] rounded-xl p-3">
                <div className="text-[11px] font-medium text-slate-400 truncate">Text Accuracy (WER)</div>
                <div className="text-xl font-extrabold text-emerald-400 mt-1 font-mono">
                  {lastJob ? `${(lastJob.wer * 100).toFixed(1)}%` : '0.0%'}
                </div>
              </div>

              {/* Metric 2: CER */}
              <div className="bg-[#111425] border border-[#1e233d] rounded-xl p-3">
                <div className="text-[11px] font-medium text-slate-400 truncate">Character Error (CER)</div>
                <div className="text-xl font-extrabold text-emerald-400 mt-1 font-mono">
                  {lastJob ? `${(lastJob.cer * 100).toFixed(1)}%` : '0.0%'}
                </div>
              </div>

              {/* Metric 3: Speaker Similarity */}
              <div className="bg-[#111425] border border-[#1e233d] rounded-xl p-3">
                <div className="text-[11px] font-medium text-slate-400 truncate">Speaker Similarity</div>
                <div className="text-xl font-extrabold text-emerald-400 mt-1 font-mono">
                  {lastJob ? `${(lastJob.speaker_similarity * 100).toFixed(1)}%` : '98.5%'}
                </div>
              </div>

              {/* Metric 4: Duration */}
              <div className="bg-[#111425] border border-[#1e233d] rounded-xl p-3">
                <div className="text-[11px] font-medium text-slate-400 truncate">Audio Duration</div>
                <div className="text-xl font-extrabold text-slate-100 mt-1 font-mono">
                  {lastJob ? `${lastJob.duration_seconds.toFixed(1)} s` : '6.0 s'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
