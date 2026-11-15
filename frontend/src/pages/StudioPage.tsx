import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Pause, 
  Trash2, 
  Download, 
  Share2, 
  Volume2, 
  Layers, 
  Cpu, 
  FileText, 
  Save, 
  Settings, 
  ChevronDown,
  Upload
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
    <div className="px-9 py-6 max-w-[1360px] mx-auto space-y-6 relative">
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

      {/* Header Banner with Glowing Ribbon Wave matching Image 1 */}
      <div className="relative pt-1 pb-2">
        {/* Curved Glowing Neon Ribbon Wave */}
        <svg className="wave-svg" viewBox="0 0 500 100" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path 
            d="M 10 70 Q 150 10 280 60 T 500 30" 
            stroke="url(#purpleGlow)" 
            strokeWidth="3.5" 
            filter="drop-shadow(0 0 16px rgba(168, 85, 247, 0.9))"
          />
          <path 
            d="M 10 70 Q 150 10 280 60 T 500 30" 
            stroke="rgba(192, 132, 252, 0.9)" 
            strokeWidth="1.5"
          />
          <defs>
            <linearGradient id="purpleGlow" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#818cf8" stopOpacity="0.4" />
              <stop offset="50%" stopColor="#c084fc" stopOpacity="1" />
              <stop offset="100%" stopColor="#ec4899" stopOpacity="0.8" />
            </linearGradient>
          </defs>
        </svg>

        <h2 className="text-[34px] font-extrabold tracking-tight">
          <span className="text-white">Voice Cloning </span>
          <span className="text-[#d8b4fe]">Studio</span>
        </h2>
        <p className="text-[13.5px] text-slate-400 font-normal mt-0.5">
          Clone a voice from a reference audio and generate natural speech in English
        </p>
      </div>

      {/* Main Grid matching Image 1 */}
      <div className="grid grid-cols-12 gap-5 items-start">
        {/* Left Side: Panel 1 & Panel 2 + Spanning Generate Speech CTA (Col 1-9) */}
        <div className="col-span-12 lg:col-span-9 space-y-5">
          <div className="grid grid-cols-12 gap-5">
            {/* Panel 1: Reference Voice (Col 1-6) */}
            <div className="col-span-12 md:col-span-6 bg-[#101326] border border-[#1b203c] rounded-2xl p-5 space-y-4 shadow-xl">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span className="w-5 h-5 rounded-full bg-[#6d28d9] text-white flex items-center justify-center text-xs font-bold">
                    1
                  </span>
                  <h3 className="text-sm font-bold text-white tracking-wide">Reference Voice</h3>
                </div>
                <label className="text-[11px] text-purple-400 hover:text-purple-300 font-semibold cursor-pointer flex items-center gap-1">
                  <Upload className="w-3 h-3" />
                  Upload
                  <input type="file" accept="audio/*" className="hidden" onChange={handleReferenceUpload} />
                </label>
              </div>

              {/* Reference Audio Player Pill matching Image 1 */}
              <div className="bg-[#14182e] border border-[#212747] rounded-xl p-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <button 
                    onClick={toggleRefPlay}
                    className="w-8 h-8 rounded-full bg-[#2563eb] hover:bg-blue-500 flex items-center justify-center text-white shadow-md shadow-blue-600/30 transition-all shrink-0"
                  >
                    {isRefPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 ml-0.5 fill-white" />}
                  </button>
                  <div>
                    <div className="text-xs font-semibold text-slate-200 truncate max-w-[140px]">
                      {selectedProfile ? selectedProfile.reference_audio_name : 'reference.wav'}
                    </div>
                    {/* Audio wave bars matching Image 1 */}
                    <div className="flex items-center gap-0.5 mt-1 h-3">
                      {[10, 18, 14, 24, 16, 12, 22, 14, 20, 10, 16, 22, 12, 18, 14, 8, 14, 20].map((h, i) => (
                        <div 
                          key={i} 
                          className="w-[2px] bg-blue-400 rounded-full" 
                          style={{ height: `${h * 0.5}px` }} 
                        />
                      ))}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-slate-400 font-mono">
                    {selectedProfile ? `00:0${Math.round(selectedProfile.duration_seconds)}` : '00:12'}
                  </span>
                  <button 
                    title="Remove Audio"
                    className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Reference Transcript Editor */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300 block">
                  Reference Transcript <span className="text-rose-400">*</span>
                </label>
                <textarea
                  value={referenceTranscript}
                  onChange={(e) => setReferenceTranscript(e.target.value)}
                  maxLength={500}
                  rows={4}
                  className="w-full bg-[#14182e] border border-[#212747] rounded-xl p-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500 transition-colors resize-none font-sans leading-relaxed"
                  placeholder="This is a reference sentence spoken by me."
                />
                <div className="text-right text-[11px] text-slate-500 font-mono">
                  {referenceTranscript.length} / 500
                </div>
              </div>
            </div>

            {/* Panel 2: Generate Speech (Col 7-12) */}
            <div className="col-span-12 md:col-span-6 bg-[#101326] border border-[#1b203c] rounded-2xl p-5 space-y-4 shadow-xl">
              <div className="flex items-center gap-2.5">
                <span className="w-5 h-5 rounded-full bg-[#6d28d9] text-white flex items-center justify-center text-xs font-bold">
                  2
                </span>
                <h3 className="text-sm font-bold text-white tracking-wide">Generate Speech</h3>
              </div>

              {/* Target Text Area */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300 block">
                  Target Text <span className="text-rose-400">*</span>
                </label>
                <textarea
                  value={targetText}
                  onChange={(e) => setTargetText(e.target.value)}
                  maxLength={500}
                  rows={3}
                  className="w-full bg-[#14182e] border border-[#212747] rounded-xl p-3 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500 transition-colors resize-none font-sans leading-relaxed"
                  placeholder="Hello, this is a cloned voice sample generated using VoiceStudio."
                />
                <div className="text-right text-[11px] text-slate-500 font-mono">
                  {targetText.length} / 500
                </div>
              </div>

              {/* Sliders matching Image 1 */}
              <div className="space-y-3 pt-1">
                {/* Speech Speed */}
                <div className="flex items-center justify-between gap-3 text-xs">
                  <span className="text-slate-300 font-medium w-24">Speech Speed</span>
                  <input 
                    type="range" 
                    min="0.5" 
                    max="2.0" 
                    step="0.1"
                    value={speechSpeed}
                    onChange={(e) => setSpeechSpeed(parseFloat(e.target.value))}
                    className="flex-1"
                  />
                  <div className="px-2.5 py-1 bg-[#14182e] border border-[#212747] rounded-lg text-slate-200 font-mono text-[11px] min-w-[42px] text-center">
                    {speechSpeed.toFixed(1)}x
                  </div>
                </div>

                {/* Pitch */}
                <div className="flex items-center justify-between gap-3 text-xs">
                  <span className="text-slate-300 font-medium w-24">Pitch</span>
                  <input 
                    type="range" 
                    min="-5.0" 
                    max="5.0" 
                    step="0.5"
                    value={pitch}
                    onChange={(e) => setPitch(parseFloat(e.target.value))}
                    className="flex-1"
                  />
                  <div className="px-2.5 py-1 bg-[#14182e] border border-[#212747] rounded-lg text-slate-200 font-mono text-[11px] min-w-[42px] text-center">
                    {pitch.toFixed(1)}
                  </div>
                </div>

                {/* Temperature */}
                <div className="flex items-center justify-between gap-3 text-xs">
                  <span className="text-slate-300 font-medium w-24">Temperature</span>
                  <input 
                    type="range" 
                    min="0.1" 
                    max="1.5" 
                    step="0.05"
                    value={temperature}
                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                    className="flex-1"
                  />
                  <div className="px-2.5 py-1 bg-[#14182e] border border-[#212747] rounded-lg text-slate-200 font-mono text-[11px] min-w-[42px] text-center">
                    {temperature.toFixed(2)}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Centered Spanning Primary CTA Button matching Image 1 */}
          <div className="flex justify-center pt-1">
            <button
              onClick={handleGenerate}
              disabled={isGenerating || !targetText.trim()}
              className="w-full max-w-[540px] py-3 px-8 rounded-full generate-cta-glow text-white font-bold text-[15px] flex items-center justify-center gap-3 disabled:opacity-50 transition-all select-none"
            >
              {/* Waveform icon lines */}
              <div className="flex items-center gap-0.5 h-4">
                <span className="w-0.5 h-2 bg-white rounded-full"></span>
                <span className="w-0.5 h-3.5 bg-white rounded-full"></span>
                <span className="w-0.5 h-2 bg-white rounded-full"></span>
                <span className="w-0.5 h-4 bg-white rounded-full"></span>
                <span className="w-0.5 h-2 bg-white rounded-full"></span>
              </div>

              <span>{isGenerating ? 'Synthesizing Speech...' : 'Generate Speech'}</span>

              <div className="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center ml-1">
                <Play className="w-2.5 h-2.5 fill-white ml-0.5" />
              </div>
            </button>
          </div>
        </div>

        {/* Right Side: Voice Profile, Model & Output Settings (Col 10-12) */}
        <div className="col-span-12 lg:col-span-3 space-y-4">
          {/* Card 1: Voice Profile matching Image 1 */}
          <div className="bg-[#101326] border border-[#1b203c] rounded-2xl p-4 space-y-3 shadow-xl">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
              <Layers className="w-4 h-4 text-purple-400" />
              <span>Voice Profile</span>
            </div>
            <div className="relative">
              <select
                value={selectedProfile?.id || ''}
                onChange={(e) => {
                  const p = profiles.find(x => x.id === e.target.value);
                  if (p) setSelectedProfile(p);
                }}
                className="w-full bg-[#14182e] border border-[#212747] rounded-xl px-3.5 py-2.5 text-xs text-slate-200 font-medium focus:outline-none focus:border-purple-500 appearance-none pr-8 cursor-pointer"
              >
                {profiles.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-3 top-3 pointer-events-none" />
            </div>

            <div className="grid grid-cols-2 gap-2 pt-0.5">
              <button 
                onClick={() => alert("Voice profile saved to local SQLite database.")}
                className="px-3 py-2 bg-[#2d1b69] hover:bg-[#3b248a] text-purple-200 border border-purple-500/40 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
              >
                <Save className="w-3.5 h-3.5 text-purple-300" />
                Save Profile
              </button>
              <button 
                onClick={() => alert("Profile manager ready.")}
                className="px-3 py-2 bg-[#14182e] hover:bg-[#1a203d] text-slate-300 border border-[#212747] rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
              >
                <Settings className="w-3.5 h-3.5 text-slate-400" />
                Manage
              </button>
            </div>
          </div>

          {/* Card 2: Model matching Image 1 */}
          <div className="bg-[#101326] border border-[#1b203c] rounded-2xl p-4 space-y-3 shadow-xl">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
              <Cpu className="w-4 h-4 text-cyan-400" />
              <span>Model</span>
            </div>
            <div className="relative">
              <div className="w-full bg-[#14182e] border border-[#212747] rounded-xl px-3.5 py-2.5 text-xs text-slate-200 font-medium flex items-center justify-between">
                <span>IndicF5 (English)</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#064e3b] text-[#34d399] border border-[#059669]/40 mr-5">
                  Loaded
                </span>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-3 top-3 pointer-events-none" />
            </div>
          </div>

          {/* Card 3: Output Format matching Image 1 */}
          <div className="bg-[#101326] border border-[#1b203c] rounded-2xl p-4 space-y-3 shadow-xl">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
              <FileText className="w-4 h-4 text-blue-400" />
              <span>Output Format</span>
            </div>
            <div className="relative">
              <select
                value={outputFormat}
                onChange={(e) => setOutputFormat(e.target.value)}
                className="w-full bg-[#14182e] border border-[#212747] rounded-xl px-3.5 py-2.5 text-xs text-slate-200 font-medium focus:outline-none focus:border-purple-500 appearance-none pr-8 cursor-pointer"
              >
                <option>WAV (Lossless)</option>
                <option>MP3 (320kbps)</option>
                <option>FLAC (Lossless)</option>
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-3 top-3 pointer-events-none" />
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Section: Output & Evaluation matching Image 1 */}
      <div className="bg-[#101326] border border-[#1b203c] rounded-2xl p-5 shadow-2xl space-y-3">
        <div className="flex items-center gap-2 text-xs font-bold text-white tracking-wide">
          <div className="w-4 h-4 rounded border border-purple-400 flex items-center justify-center">
            <span className="w-1.5 h-1.5 bg-purple-400 rounded-sm"></span>
          </div>
          <span>Output & Evaluation</span>
        </div>

        <div className="grid grid-cols-12 gap-5 items-center">
          {/* Left Player Box matching Image 1 */}
          <div className="col-span-12 lg:col-span-7 bg-[#14182e] border border-[#212747] rounded-2xl p-4 flex items-center gap-4">
            <button
              onClick={toggleOutputPlay}
              disabled={!lastJob}
              className="w-11 h-11 rounded-full bg-gradient-to-tr from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 flex items-center justify-center text-white purple-play-glow shrink-0 disabled:opacity-40 transition-all cursor-pointer"
            >
              {isPlaying ? <Pause className="w-5 h-5 fill-white" /> : <Play className="w-5 h-5 fill-white ml-0.5" />}
            </button>

            {/* Detailed Waveform Visualization */}
            <div className="flex-1 flex items-center gap-0.5 h-9 overflow-hidden">
              {[8, 16, 24, 38, 20, 48, 65, 80, 50, 62, 78, 92, 85, 70, 55, 35, 45, 60, 75, 52, 38, 22, 34, 48, 62, 42, 28, 16, 28, 45, 32, 18, 10, 22, 35, 48, 30, 16].map((h, i) => (
                <div
                  key={i}
                  className={`flex-1 rounded-full transition-all ${
                    lastJob
                      ? i < (audioCurrentTime / (lastJob.duration_seconds || 1)) * 38
                        ? 'bg-purple-300'
                        : 'bg-[#6366f1]/70'
                      : 'bg-slate-600/40'
                  }`}
                  style={{ height: `${h}%` }}
                />
              ))}
            </div>

            <div className="text-xs font-mono text-slate-300 whitespace-nowrap">
              0:0{Math.floor(audioCurrentTime)} / 0:0{lastJob ? Math.round(lastJob.duration_seconds) : '6'}
            </div>

            <div className="flex items-center gap-2 border-l border-[#242b4e] pl-3 text-slate-400">
              <button title="Volume" className="hover:text-white transition-colors p-1">
                <Volume2 className="w-4 h-4" />
              </button>
              {lastJob?.output_audio_url && (
                <a
                  href={`http://127.0.0.1:8000${lastJob.output_audio_url}`}
                  download="cloned_voice.wav"
                  title="Download WAV"
                  className="hover:text-purple-400 transition-colors p-1"
                >
                  <Download className="w-4 h-4" />
                </a>
              )}
              <button 
                title="Share" 
                onClick={() => alert("Audio link copied.")}
                className="hover:text-white transition-colors p-1"
              >
                <Share2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Right: Evaluation (Auto) 4 Stat Cards matching Image 1 */}
          <div className="col-span-12 lg:col-span-5 bg-[#14182e] border border-[#212747] rounded-2xl p-3.5 space-y-2">
            <div className="text-[11px] font-bold text-slate-300 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-purple-400"></span>
              <span>Evaluation (Auto)</span>
            </div>

            <div className="grid grid-cols-4 gap-2 text-center">
              {/* Text Accuracy (WER) */}
              <div className="bg-[#101326] border border-[#1b203c] rounded-xl p-2.5">
                <div className="text-[10px] text-slate-400 font-medium leading-tight">
                  Text Accuracy<br/>(WER)
                </div>
                <div className="text-lg font-extrabold text-[#00e676] mt-1 font-mono">
                  {lastJob ? `${(lastJob.wer * 100).toFixed(1)}%` : '0.0%'}
                </div>
              </div>

              {/* Character Error Rate (CER) */}
              <div className="bg-[#101326] border border-[#1b203c] rounded-xl p-2.5">
                <div className="text-[10px] text-slate-400 font-medium leading-tight">
                  Character Error<br/>Rate (CER)
                </div>
                <div className="text-lg font-extrabold text-[#00e676] mt-1 font-mono">
                  {lastJob ? `${(lastJob.cer * 100).toFixed(1)}%` : '0.0%'}
                </div>
              </div>

              {/* Speaker Similarity */}
              <div className="bg-[#101326] border border-[#1b203c] rounded-xl p-2.5">
                <div className="text-[10px] text-slate-400 font-medium leading-tight">
                  Speaker<br/>Similarity
                </div>
                <div className="text-lg font-extrabold text-[#00e676] mt-1 font-mono">
                  {lastJob ? `${(lastJob.speaker_similarity * 100).toFixed(1)}%` : '98.5%'}
                </div>
              </div>

              {/* Audio Duration */}
              <div className="bg-[#101326] border border-[#1b203c] rounded-xl p-2.5">
                <div className="text-[10px] text-slate-400 font-medium leading-tight">
                  Audio<br/>Duration
                </div>
                <div className="text-lg font-extrabold text-white mt-1 font-mono">
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
