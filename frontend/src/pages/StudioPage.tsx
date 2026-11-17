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
  Upload,
  XCircle,
  Loader2,
  CheckCircle,
  Check,
  AlertCircle
} from 'lucide-react';
import type { VoiceProfile, GenerationJob, SystemMetrics } from '../types';
import { SynthesisAPI, ProfileAPI, FileDownloadAPI } from '../services/api';
import { WaveAnimation } from '../components/WaveAnimation';

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
  onRefreshProfiles,
  systemMetrics
}) => {
  // Synthesis Settings State
  const [targetText, setTargetText] = useState('Hello, this is a cloned voice sample generated using VoiceStudio.');
  const [referenceTranscript, setReferenceTranscript] = useState('Where there is righteousness in the heart, there is beauty in the character.');
  const [speechSpeed, setSpeechSpeed] = useState(1.0);
  const [pitch, setPitch] = useState(0.0);
  const [seed, setSeed] = useState<number | undefined>(42);
  const [isRandomSeed, setIsRandomSeed] = useState(false);
  const [mode, setMode] = useState<'draft' | 'final'>('draft');
  const [consentGiven, setConsentGiven] = useState(true);
  const [outputFormat, setOutputFormat] = useState('WAV (Lossless)');
  const [isGenerating, setIsGenerating] = useState(false);
  const [progressPercent, setProgressPercent] = useState(0);
  const [progressStage, setProgressStage] = useState('');
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [lastJob, setLastJob] = useState<GenerationJob | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Audio Playback State for Output
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioCurrentTime, setAudioCurrentTime] = useState(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Audio Playback State for Reference Audio
  const [isRefPlaying, setIsRefPlaying] = useState(false);
  const [refCurrentTime, setRefCurrentTime] = useState(0);
  const refAudioRef = useRef<HTMLAudioElement | null>(null);

  // Multi-Stage Audio Pipeline State: Uploading (100%) ⟶ Denoising ⟶ Transcribing with Whisper... ⟶ Ready!
  const [pipelineStage, setPipelineStage] = useState<'idle' | 'uploading' | 'denoising' | 'transcribing' | 'ready'>('idle');
  const [pipelinePercent, setPipelinePercent] = useState<number>(0);
  const [pipelineStatus, setPipelineStatus] = useState<string>('');
  const [pipelineError, setPipelineError] = useState<string | null>(null);
  const [uploadBytePercent, setUploadBytePercent] = useState<number>(0);
  const [uploadBytesLoaded, setUploadBytesLoaded] = useState<number>(0);
  const [uploadBytesTotal, setUploadBytesTotal] = useState<number>(0);
  const [uploadSuccessMessage, setUploadSuccessMessage] = useState<string | null>(null);

  // Download Progress & Status State
  const [downloadProgress, setDownloadProgress] = useState<{
    isDownloading: boolean;
    percent: number;
    loaded: number;
    total: number;
    status: string;
  }>({
    isDownloading: false,
    percent: 0,
    loaded: 0,
    total: 0,
    status: '',
  });

  // Reference Transcript Editing & Persistence State
  const [isSavingTranscript, setIsSavingTranscript] = useState(false);
  const [transcriptSavedSuccess, setTranscriptSavedSuccess] = useState(false);

  // Compute Device Selection (Auto-detect / CPU / Colab GPU)
  const [computeDevice, setComputeDevice] = useState<'auto' | 'cpu' | 'remote_gpu'>('auto');

  // Target Text Statistics
  const targetWordCount = targetText.trim() ? targetText.trim().split(/\s+/).length : 0;
  const estimatedSpeechDuration = (targetWordCount * 0.28).toFixed(1);
  const estimatedChunks = Math.max(1, Math.ceil(targetWordCount / 25));

  // Auto-reload output audio when a new job arrives
  useEffect(() => {
    if (lastJob?.output_audio_url && audioRef.current) {
      audioRef.current.load();
    }
  }, [lastJob]);

  // Auto-reload reference audio when selected profile or its audio URL changes
  useEffect(() => {
    if (refAudioRef.current) {
      refAudioRef.current.load();
      setIsRefPlaying(false);
    }
  }, [selectedProfile?.reference_audio_url, selectedProfile?.id]);

  // Update transcript when selected profile changes or auto-select first profile
  useEffect(() => {
    if (selectedProfile) {
      setReferenceTranscript(selectedProfile.reference_transcript);
    } else if (profiles && profiles.length > 0) {
      setSelectedProfile(profiles[0]);
    }
  }, [selectedProfile, profiles, setSelectedProfile]);

  const handleCancel = async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    await SynthesisAPI.cancelGeneration();
    setIsGenerating(false);
    setProgressPercent(0);
    setProgressStage('Generation cancelled by user');
  };

  const handleGenerate = async () => {
    if (!targetText.trim()) return;
    setIsGenerating(true);
    setProgressPercent(6);
    setProgressStage('Step 1/5: Analyzing acoustic timbre & phonetics...');
    setElapsedSeconds(0);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const startTime = Date.now();
    const pollInterval = setInterval(async () => {
      const elapsed = Math.round((Date.now() - startTime) / 1000);
      setElapsedSeconds(elapsed);
      try {
        const prog = await SynthesisAPI.getProgress();
        if (prog && typeof prog.percent === 'number' && prog.percent > 0) {
          if (prog.stage) setProgressStage(prog.stage);
          // Smooth time-based advance so the progress bar never freezes on long chunks
          const timeBasedEstimate = Math.min(92, Math.round(prog.percent + (92 - prog.percent) * (1.0 - Math.exp(-elapsed / 10.0))));
          setProgressPercent(prev => Math.max(prev, timeBasedEstimate));
        } else {
          // Dynamic client interpolation
          const estimated = Math.min(90, Math.round(10 + 80 * (1.0 - Math.exp(-elapsed / 10.0))));
          setProgressPercent(prev => Math.max(prev, estimated));
        }
      } catch (_) {
        const estimated = Math.min(85, Math.round(10 + 75 * (1.0 - Math.exp(-elapsed / 12.0))));
        setProgressPercent(prev => Math.max(prev, estimated));
      }
    }, 250);

    try {
      const job = await SynthesisAPI.generateSpeech({
        profile_id: selectedProfile?.id,
        profile_name: selectedProfile?.name,
        target_text: targetText,
        speech_speed: speechSpeed,
        pitch: pitch,
        temperature: 0.7,
        seed: isRandomSeed ? undefined : seed,
        output_format: outputFormat,
        mode: mode,
        consent_given: consentGiven,
        reference_transcript: referenceTranscript
      }, controller.signal);
      clearInterval(pollInterval);
      setProgressPercent(100);
      setProgressStage('Speech synthesis complete! Ready for playback.');
      setLastJob(job);
      setIsPlaying(false);
      setAudioCurrentTime(0);
      setTimeout(() => {
        if (audioRef.current) {
          audioRef.current.load();
        }
      }, 100);
    } catch (err: any) {
      clearInterval(pollInterval);
      setProgressPercent(0);
      if (err.name === 'CanceledError' || err.name === 'AbortError') {
        setProgressStage('Generation cancelled by user');
      } else {
        setProgressStage('');
        const detailMsg = err.response?.data?.detail;
        const errorMsg = detailMsg || (err.message === 'Network Error'
          ? 'Cannot reach backend server at http://127.0.0.1:8000. Please ensure the backend server is running.'
          : err.message);
        alert(`Generation failed: ${errorMsg}`);
      }
    } finally {
      clearInterval(pollInterval);
      abortControllerRef.current = null;
      setTimeout(() => {
        setIsGenerating(false);
      }, 1500);
    }
  };

  const handleReferenceUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const inputElement = e.target;
    setUploadSuccessMessage(null);
    setPipelineError(null);
    setPipelineStage('uploading');
    setPipelinePercent(10);
    setUploadBytePercent(0);
    setUploadBytesLoaded(0);
    setUploadBytesTotal(file.size);
    setPipelineStatus(`Stage 1/4: Uploading "${file.name}" (0% - 0.00 MB / ${(file.size / 1024 / 1024).toFixed(2)} MB)...`);

    // Poll server-side conversion status (denoising -> transcribing with Whisper -> ready)
    let conversionPolling: any = null;

    try {
      if (refAudioRef.current) {
        refAudioRef.current.pause();
        refAudioRef.current.currentTime = 0;
      }
      setIsRefPlaying(false);

      const baseName = file.name.replace(/\.[^/.]+$/, '').trim() || 'Voice';
      const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      const uniqueName = `${baseName} (${timeStr})`;

      const formData = new FormData();
      formData.append('name', uniqueName);
      formData.append('audio_file', file);

      // Start polling backend conversion stage after bytes start sending
      conversionPolling = setInterval(async () => {
        try {
          const prog = await ProfileAPI.getProcessingProgress();
          if (prog && prog.stage) {
            if (prog.stage === 'denoising') {
              setPipelineStage('denoising');
              setPipelinePercent(prev => Math.max(prev, 55));
              setPipelineStatus(`Stage 2/4: ${prog.message || 'Denoising audio & normalizing loudness to -1dB peak...'}`);
            } else if (prog.stage === 'transcribing') {
              setPipelineStage('transcribing');
              setPipelinePercent(prev => Math.max(prev, 82));
              setPipelineStatus(`Stage 3/4: ${prog.message || 'Transcribing speech phonetics with Whisper & aligning sentences...'}`);
            } else if (prog.stage === 'finalizing') {
              setPipelineStage('transcribing');
              setPipelinePercent(prev => Math.max(prev, 94));
              setPipelineStatus(`Stage 3/4: Trimming sentence boundaries & saving clean profile...`);
            }
          }
        } catch (_) {}
      }, 250);

      const newP = await ProfileAPI.createProfile(formData, (p) => {
        setUploadBytePercent(p.percent);
        setUploadBytesLoaded(p.loaded);
        setUploadBytesTotal(p.total);
        if (p.percent < 100) {
          setPipelineStage('uploading');
          const mappedPercent = Math.min(30, Math.round((p.percent / 100) * 30));
          setPipelinePercent(mappedPercent);
          setPipelineStatus(`Stage 1/4: Uploading "${file.name}" (${p.percent}% - ${(p.loaded / 1024 / 1024).toFixed(2)} MB / ${(p.total / 1024 / 1024).toFixed(2)} MB)...`);
        } else {
          setUploadBytePercent(100);
          setPipelineStage('denoising');
          setPipelinePercent(prev => Math.max(prev, 40));
          setPipelineStatus(`Stage 2/4: Upload complete (100%) ⟶ Denoising audio & normalizing loudness...`);
        }
      });
      
      clearInterval(conversionPolling);

      setSelectedProfile(newP);
      setReferenceTranscript(newP.reference_transcript || '');
      if (onRefreshProfiles) {
        await onRefreshProfiles();
      }
      setSelectedProfile(newP);

      // Stage 4: Ready!
      setPipelineStage('ready');
      setPipelinePercent(100);
      setPipelineStatus(`Stage 4/4: Ready! Voice profile successfully loaded for "${file.name}".`);
      setUploadSuccessMessage(`Successfully processed "${file.name}"!`);

      setTimeout(() => {
        setUploadSuccessMessage(null);
      }, 5000);
    } catch (err: any) {
      if (conversionPolling) clearInterval(conversionPolling);
      const errMsg = err.response?.data?.detail || err.message;
      setPipelineStage('idle');
      setPipelineError(`Upload failed: ${errMsg}`);
      alert(`Upload failed: ${errMsg}`);
    } finally {
      if (conversionPolling) clearInterval(conversionPolling);
      inputElement.value = '';
    }
  };

  const handleSaveTranscript = async () => {
    if (!selectedProfile) return;
    setIsSavingTranscript(true);
    try {
      await ProfileAPI.updateProfile(selectedProfile.id, {
        reference_transcript: referenceTranscript,
      });
      setTranscriptSavedSuccess(true);
      if (onRefreshProfiles) {
        onRefreshProfiles();
      }
      setTimeout(() => {
        setTranscriptSavedSuccess(false);
      }, 3000);
    } catch (err: any) {
      alert(`Failed to save transcript: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsSavingTranscript(false);
    }
  };

  const handleDownloadAudio = async () => {
    if (!lastJob?.output_audio_url) return;
    const filename = `cloned_voice_${Date.now().toString().slice(-6)}.wav`;
    setDownloadProgress({
      isDownloading: true,
      percent: 0,
      loaded: 0,
      total: 0,
      status: `Starting download of ${filename}...`,
    });

    try {
      await FileDownloadAPI.downloadAudioFile(lastJob.output_audio_url, filename, (p) => {
        setDownloadProgress({
          isDownloading: true,
          percent: p.percent,
          loaded: p.loaded,
          total: p.total,
          status: `Downloading ${filename}... ${p.percent}% (${(p.loaded / 1024).toFixed(0)} KB / ${(p.total / 1024).toFixed(0)} KB)`,
        });
      });
      setDownloadProgress({
        isDownloading: false,
        percent: 100,
        loaded: 0,
        total: 0,
        status: `Downloaded ${filename} successfully!`,
      });
      setTimeout(() => {
        setDownloadProgress(prev => ({ ...prev, status: '' }));
      }, 3500);
    } catch (err: any) {
      setDownloadProgress({
        isDownloading: false,
        percent: 0,
        loaded: 0,
        total: 0,
        status: `Download failed: ${err.message}`,
      });
    }
  };

  const toggleOutputPlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play().then(() => {
        setIsPlaying(true);
      }).catch((err) => {
        console.warn('Playback error, reloading audio element:', err);
        audioRef.current?.load();
        audioRef.current?.play().then(() => {
          setIsPlaying(true);
        }).catch((e) => {
          console.error('Final play attempt failed:', e);
        });
      });
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
    <div className="px-9 py-6 max-w-[1360px] mx-auto space-y-6 relative select-none">
      {/* Audio player element */}
      {lastJob?.output_audio_url && (
        <audio
          ref={audioRef}
          src={`http://127.0.0.1:8000${lastJob.output_audio_url}`}
          preload="auto"
          onTimeUpdate={() => setAudioCurrentTime(audioRef.current?.currentTime || 0)}
          onEnded={() => setIsPlaying(false)}
          onError={(e) => console.warn('Audio element error:', e)}
        />
      )}
      {selectedProfile?.reference_audio_url && (
        <audio
          key={selectedProfile.reference_audio_url}
          ref={refAudioRef}
          src={`http://127.0.0.1:8000${selectedProfile.reference_audio_url}`}
          onTimeUpdate={() => setRefCurrentTime(refAudioRef.current?.currentTime || 0)}
          onEnded={() => setIsRefPlaying(false)}
        />
      )}

      {/* Header Banner with LIVE Animated Glowing Wave Ribbon matching Image 1 */}
      <div className="relative pt-2 pb-3 overflow-visible">
        {/* Top Right Animated 3D Flowing Ribbon Wave */}
        <WaveAnimation />

        <div className="relative z-10">
          <h2 className="text-[36px] font-black tracking-tight studio-title-gradient">
            Voice Cloning Studio
          </h2>
          <p className="text-[13.5px] font-medium mt-1 text-slate-400">
            Clone a voice from a reference audio and generate natural speech in English
          </p>
        </div>
      </div>

      {/* Main Grid matching Image 1 */}
      <div className="grid grid-cols-12 gap-5 items-start relative z-10">
        {/* Left Side: Panel 1 & Panel 2 + Centered Generate Speech CTA (Col 1-9) */}
        <div className="col-span-12 lg:col-span-9 space-y-5">
          <div className="grid grid-cols-12 gap-5">
            {/* Panel 1: Reference Voice (Col 1-6) */}
            <div
              className="col-span-12 md:col-span-6 rounded-2xl p-5 space-y-4 shadow-xl border transition-colors"
              style={{
                backgroundColor: 'var(--bg-card)',
                borderColor: 'var(--border-card)'
              }}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <span className="w-5 h-5 rounded-full bg-[#6d28d9] text-white flex items-center justify-center text-xs font-bold shadow-md shadow-purple-600/40">
                    1
                  </span>
                  <h3 className="text-sm font-bold tracking-wide" style={{ color: 'var(--text-primary)' }}>
                    Reference Voice
                  </h3>
                </div>
                <label className="text-[11px] text-purple-400 hover:text-purple-300 font-semibold cursor-pointer flex items-center gap-1 transition-colors">
                  <Upload className="w-3 h-3" />
                  Upload
                  <input type="file" accept="audio/*" className="hidden" onChange={handleReferenceUpload} />
                </label>
              </div>

              {/* Multi-Stage Audio Pipeline Stepper: "Uploading (100%) ⟶ Denoising ⟶ Transcribing with Whisper... ⟶ Ready!" */}
              {pipelineStage !== 'idle' && (() => {
                const stageIndex = pipelineStage === 'uploading' ? 0 :
                                   pipelineStage === 'denoising' ? 1 :
                                   pipelineStage === 'transcribing' ? 2 :
                                   pipelineStage === 'ready' ? 3 : -1;
                return (
                  <div
                    className="rounded-xl p-3.5 border space-y-3 transition-all shadow-lg animate-in fade-in duration-200"
                    style={{
                      backgroundColor: 'var(--bg-card-inner)',
                      borderColor: pipelineStage === 'ready' ? 'rgba(16, 185, 129, 0.4)' : 'rgba(168, 85, 247, 0.4)'
                    }}
                  >
                    {/* Stepper Steps Row */}
                    <div className="flex items-center justify-between gap-1 overflow-x-auto py-1 no-scrollbar text-[11px] font-semibold">
                      {/* Step 1: Uploading */}
                      <div className={`flex items-center gap-1 px-2 py-1 rounded-lg border transition-all whitespace-nowrap ${
                        stageIndex > 0 ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
                        stageIndex === 0 ? 'bg-purple-500/20 border-purple-500/50 text-purple-300 ring-1 ring-purple-500/40' :
                        'bg-slate-800/40 border-slate-700/50 text-slate-500'
                      }`}>
                        {stageIndex > 0 ? (
                          <CheckCircle className="w-3 h-3 text-emerald-400 shrink-0" />
                        ) : stageIndex === 0 ? (
                          <Loader2 className="w-3 h-3 animate-spin text-purple-400 shrink-0" />
                        ) : (
                          <span className="w-3 h-3 rounded-full border border-slate-600 flex items-center justify-center text-[8px]">1</span>
                        )}
                        <span>Uploading ({uploadBytePercent}%)</span>
                      </div>

                      <span className={`text-xs font-bold transition-colors select-none ${stageIndex >= 1 ? 'text-purple-400' : 'text-slate-600'}`}>⟶</span>

                      {/* Step 2: Denoising */}
                      <div className={`flex items-center gap-1 px-2 py-1 rounded-lg border transition-all whitespace-nowrap ${
                        stageIndex > 1 ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
                        stageIndex === 1 ? 'bg-purple-500/20 border-purple-500/50 text-purple-300 ring-1 ring-purple-500/40' :
                        'bg-slate-800/40 border-slate-700/50 text-slate-500'
                      }`}>
                        {stageIndex > 1 ? (
                          <CheckCircle className="w-3 h-3 text-emerald-400 shrink-0" />
                        ) : stageIndex === 1 ? (
                          <Loader2 className="w-3 h-3 animate-spin text-purple-400 shrink-0" />
                        ) : (
                          <span className="w-3 h-3 rounded-full border border-slate-600 flex items-center justify-center text-[8px]">2</span>
                        )}
                        <span>Denoising</span>
                      </div>

                      <span className={`text-xs font-bold transition-colors select-none ${stageIndex >= 2 ? 'text-purple-400' : 'text-slate-600'}`}>⟶</span>

                      {/* Step 3: Transcribing with Whisper... */}
                      <div className={`flex items-center gap-1 px-2 py-1 rounded-lg border transition-all whitespace-nowrap ${
                        stageIndex > 2 ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' :
                        stageIndex === 2 ? 'bg-purple-500/20 border-purple-500/50 text-purple-300 ring-1 ring-purple-500/40' :
                        'bg-slate-800/40 border-slate-700/50 text-slate-500'
                      }`}>
                        {stageIndex > 2 ? (
                          <CheckCircle className="w-3 h-3 text-emerald-400 shrink-0" />
                        ) : stageIndex === 2 ? (
                          <Loader2 className="w-3 h-3 animate-spin text-purple-400 shrink-0" />
                        ) : (
                          <span className="w-3 h-3 rounded-full border border-slate-600 flex items-center justify-center text-[8px]">3</span>
                        )}
                        <span>Transcribing with Whisper...</span>
                      </div>

                      <span className={`text-xs font-bold transition-colors select-none ${stageIndex >= 3 ? 'text-emerald-400' : 'text-slate-600'}`}>⟶</span>

                      {/* Step 4: Ready! */}
                      <div className={`flex items-center gap-1 px-2 py-1 rounded-lg border transition-all whitespace-nowrap ${
                        stageIndex >= 3 ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300 ring-1 ring-emerald-500/40 font-bold' :
                        'bg-slate-800/40 border-slate-700/50 text-slate-500'
                      }`}>
                        {stageIndex >= 3 ? (
                          <CheckCircle className="w-3 h-3 text-emerald-400 shrink-0" />
                        ) : (
                          <span className="w-3 h-3 rounded-full border border-slate-600 flex items-center justify-center text-[8px]">4</span>
                        )}
                        <span>Ready!</span>
                      </div>
                    </div>

                    {/* Progress Bar & Status Text */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-purple-300 flex items-center gap-1.5 truncate max-w-[320px]">
                          {pipelineStage === 'ready' ? (
                            <CheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                          ) : (
                            <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-400 shrink-0" />
                          )}
                          <span className="truncate">{pipelineStatus}</span>
                        </span>
                        <span className={`font-mono font-bold ml-2 shrink-0 ${pipelineStage === 'ready' ? 'text-emerald-400' : 'text-purple-300'}`}>
                          {pipelinePercent}%
                        </span>
                      </div>

                      <div className="w-full bg-slate-800/80 rounded-full h-2.5 overflow-hidden border border-purple-500/20 shadow-inner">
                        <div
                          className={`h-full rounded-full transition-all duration-300 ${
                            pipelineStage === 'ready'
                              ? 'bg-gradient-to-r from-emerald-500 to-teal-400'
                              : 'bg-gradient-to-r from-purple-500 via-indigo-500 to-cyan-400'
                          }`}
                          style={{ width: `${pipelinePercent}%` }}
                        />
                      </div>

                      <div className="flex justify-between items-center text-[10.5px] text-slate-400 font-mono">
                        <span>
                          {uploadBytesTotal > 0
                            ? `${(uploadBytesLoaded / 1024 / 1024).toFixed(2)} MB / ${(uploadBytesTotal / 1024 / 1024).toFixed(2)} MB`
                            : 'Audio stream'}
                        </span>
                        <div className="flex items-center gap-2">
                          <span>
                            {pipelineStage === 'uploading' && 'Transferring audio to server...'}
                            {pipelineStage === 'denoising' && 'Bandpass filter & loudness normalization (-1 dB)...'}
                            {pipelineStage === 'transcribing' && 'Neural phoneme extraction & Whisper align...'}
                            {pipelineStage === 'ready' && 'Profile persisted and ready for synthesis!'}
                          </span>
                          {pipelineStage === 'ready' && (
                            <button
                              onClick={() => setPipelineStage('idle')}
                              className="text-[10px] text-slate-400 hover:text-white underline cursor-pointer ml-1"
                            >
                              Dismiss
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()}

              {/* Upload Success Alert */}
              {uploadSuccessMessage && (
                <div className="rounded-xl p-2.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 shrink-0 text-emerald-400" />
                  <span className="truncate">{uploadSuccessMessage}</span>
                </div>
              )}

              {/* Upload Error Alert */}
              {pipelineError && (
                <div className="rounded-xl p-2.5 bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 truncate">
                    <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
                    <span className="truncate">{pipelineError}</span>
                  </div>
                  <button
                    onClick={() => setPipelineError(null)}
                    className="text-xs hover:text-white font-semibold cursor-pointer"
                  >
                    Dismiss
                  </button>
                </div>
              )}

              {/* Reference Audio Player Pill matching Image 1 with Interactive Waveform Seeking (TODO-2) */}
              <div
                className="rounded-xl p-3 flex items-center justify-between border transition-colors"
                style={{
                  backgroundColor: 'var(--bg-card-inner)',
                  borderColor: 'var(--border-inner)'
                }}
              >
                <div className="flex items-center gap-3">
                  <button
                    onClick={toggleRefPlay}
                    className="w-8 h-8 rounded-full bg-[#2563eb] hover:bg-blue-500 active:scale-90 flex items-center justify-center text-white shadow-md shadow-blue-600/40 transition-all shrink-0 cursor-pointer"
                  >
                    {isRefPlaying ? <Pause className="w-3.5 h-3.5 fill-white" /> : <Play className="w-3.5 h-3.5 ml-0.5 fill-white" />}
                  </button>
                  <div>
                    <div className="text-xs font-semibold truncate max-w-[140px]" style={{ color: 'var(--text-primary)' }}>
                      {selectedProfile ? (selectedProfile.reference_audio_name || selectedProfile.name) : 'No file selected'}
                    </div>
                    {/* Animated Audio Equalizer Bars with Click-to-Seek */}
                    <div
                      className="flex items-center gap-0.5 mt-1 h-3.5 cursor-pointer group"
                      title="Click along waveform to seek reference audio"
                      onClick={(e) => {
                        const rect = e.currentTarget.getBoundingClientRect();
                        const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
                        const dur = selectedProfile?.duration_seconds || 1;
                        if (refAudioRef.current) {
                          refAudioRef.current.currentTime = ratio * dur;
                          setRefCurrentTime(refAudioRef.current.currentTime);
                        }
                      }}
                    >
                      {[10, 18, 14, 24, 16, 12, 22, 14, 20, 10, 16, 22, 12, 18, 14, 8, 14, 20].map((h, i) => (
                        <div
                          key={i}
                          className={`w-[2.5px] rounded-full transition-all ${
                            i < (refCurrentTime / (selectedProfile?.duration_seconds || 1)) * 18
                              ? 'bg-cyan-400'
                              : isRefPlaying ? 'bg-cyan-400/40 animate-wave-bar' : 'bg-blue-400'
                          }`}
                          style={{
                            height: `${h * 0.55}px`,
                            animationDelay: `${(i % 5) * 0.1}s`
                          }}
                        />
                      ))}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-mono" style={{ color: 'var(--text-secondary)' }}>
                    {selectedProfile
                      ? `00:0${Math.floor(refCurrentTime)} / 00:0${Math.round(selectedProfile.duration_seconds)}`
                      : '00:00'}
                  </span>
                  <button
                    title="Remove Audio"
                    onClick={() => {
                      if (refAudioRef.current) {
                        refAudioRef.current.pause();
                        refAudioRef.current.currentTime = 0;
                      }
                      setIsRefPlaying(false);
                      setRefCurrentTime(0);
                      setSelectedProfile(null);
                      setReferenceTranscript('');
                    }}
                    className="text-slate-400 hover:text-rose-400 transition-colors p-1 cursor-pointer"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Editable Reference Transcript with In-Place Persistence (TODO-3) */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold block" style={{ color: 'var(--text-primary)' }}>
                    Reference Transcript
                  </label>
                  <div className="flex items-center gap-2">
                    {transcriptSavedSuccess && (
                      <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                        <Check className="w-3 h-3" />
                        Saved to Profile!
                      </span>
                    )}
                    <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      Auto-Transcribed with Whisper
                    </span>
                  </div>
                </div>
                <textarea
                  value={referenceTranscript}
                  onChange={(e) => setReferenceTranscript(e.target.value)}
                  rows={3}
                  placeholder="Auto-transcribed text will appear here... you can edit and save corrections."
                  className="w-full rounded-xl p-3 text-xs font-sans leading-relaxed border focus:outline-none focus:border-purple-500 transition-colors resize-none select-text"
                  style={{
                    backgroundColor: 'var(--bg-card-inner)',
                    borderColor: 'var(--border-inner)',
                    color: 'var(--text-primary)'
                  }}
                />
                <div className="flex justify-between items-center text-[11px]" style={{ color: 'var(--text-muted)' }}>
                  <span>Sentence-aligned to prevent initial word clipping</span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono">{referenceTranscript.length} chars</span>
                    {selectedProfile && (
                      <button
                        type="button"
                        disabled={isSavingTranscript}
                        onClick={handleSaveTranscript}
                        className="px-2.5 py-1 rounded-lg bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 text-[11px] font-semibold flex items-center gap-1 transition-all cursor-pointer disabled:opacity-50"
                        title="Save edited transcript permanently to SQLite profile"
                      >
                        {isSavingTranscript ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <Save className="w-3 h-3" />
                        )}
                        Save Transcript
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Panel 2: Generate Speech (Col 7-12) */}
            <div
              className="col-span-12 md:col-span-6 rounded-2xl p-5 space-y-4 shadow-xl border transition-colors"
              style={{
                backgroundColor: 'var(--bg-card)',
                borderColor: 'var(--border-card)'
              }}
            >
              <div className="flex items-center gap-2.5">
                <span className="w-5 h-5 rounded-full bg-[#6d28d9] text-white flex items-center justify-center text-xs font-bold shadow-md shadow-purple-600/40">
                  2
                </span>
                <h3 className="text-sm font-bold tracking-wide" style={{ color: 'var(--text-primary)' }}>
                  Generate Speech
                </h3>
              </div>

              {/* Target Text Area */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold block" style={{ color: 'var(--text-primary)' }}>
                  Target Text <span className="text-rose-400">*</span>
                </label>
                <textarea
                  value={targetText}
                  onChange={(e) => setTargetText(e.target.value)}
                  maxLength={500}
                  rows={3}
                  className="w-full rounded-xl p-3 text-xs focus:outline-none focus:border-purple-500 transition-colors resize-none font-sans leading-relaxed border"
                  style={{
                    backgroundColor: 'var(--bg-card-inner)',
                    borderColor: 'var(--border-inner)',
                    color: 'var(--text-primary)'
                  }}
                  placeholder="Hello, this is a cloned voice sample generated using VoiceStudio."
                />
                <div className="flex justify-between items-center text-[11px]" style={{ color: 'var(--text-muted)' }}>
                  <span className="font-mono text-slate-400">
                    {targetWordCount} words · ~{estimatedSpeechDuration}s duration · {estimatedChunks} chunk{estimatedChunks > 1 ? 's' : ''}
                  </span>
                  <div className="flex items-center gap-2">
                    {targetText && (
                      <button
                        type="button"
                        onClick={() => setTargetText('')}
                        className="hover:text-rose-400 text-slate-500 transition-colors cursor-pointer text-[10.5px]"
                      >
                        Clear
                      </button>
                    )}
                    <span className="font-mono">{targetText.length} / 500</span>
                  </div>
                </div>
              </div>

              {/* Controls: Speech Speed, Pitch (Experimental), Seed & Mode */}
              <div className="space-y-3 pt-1">
                {/* Speech Speed */}
                <div className="flex items-center justify-between gap-3 text-xs">
                  <span className="font-medium w-32" style={{ color: 'var(--text-primary)' }}>Speech Speed</span>
                  <input
                    type="range"
                    min="0.5"
                    max="2.0"
                    step="0.1"
                    value={speechSpeed}
                    onChange={(e) => setSpeechSpeed(parseFloat(e.target.value))}
                    className="flex-1"
                    style={{
                      background: `linear-gradient(to right, #06b6d4 0%, #3b82f6 ${((speechSpeed - 0.5) / 1.5) * 100}%, #1e2440 ${((speechSpeed - 0.5) / 1.5) * 100}%, #1e2440 100%)`
                    }}
                  />
                  <div
                    className="px-2.5 py-1 rounded-lg font-mono text-[11px] min-w-[42px] text-center border font-semibold"
                    style={{
                      backgroundColor: 'var(--bg-card-inner)',
                      borderColor: 'var(--border-inner)',
                      color: 'var(--text-primary)'
                    }}
                  >
                    {speechSpeed.toFixed(1)}x
                  </div>
                </div>

                {/* Pitch (Marked Experimental with Tooltip Warning) */}
                <div className="flex items-center justify-between gap-3 text-xs">
                  <div className="flex items-center gap-1.5 w-32" title="Experimental: Pitch shifting is applied post-vocoder and may degrade voice similarity">
                    <span className="font-medium" style={{ color: 'var(--text-primary)' }}>Pitch</span>
                    <span className="text-[10px] text-amber-400 bg-amber-500/10 px-1 py-0.2 rounded border border-amber-500/20 font-mono">exp</span>
                  </div>
                  <input
                    type="range"
                    min="-5.0"
                    max="5.0"
                    step="0.5"
                    value={pitch}
                    onChange={(e) => setPitch(parseFloat(e.target.value))}
                    className="flex-1"
                    style={{
                      background: `linear-gradient(to right, #8b5cf6 0%, #ec4899 ${((pitch + 5.0) / 10.0) * 100}%, #1e2440 ${((pitch + 5.0) / 10.0) * 100}%, #1e2440 100%)`
                    }}
                  />
                  <div
                    className="px-2.5 py-1 rounded-lg font-mono text-[11px] min-w-[42px] text-center border font-semibold"
                    style={{
                      backgroundColor: 'var(--bg-card-inner)',
                      borderColor: 'var(--border-inner)',
                      color: 'var(--text-primary)'
                    }}
                  >
                    {pitch.toFixed(1)}
                  </div>
                </div>

                {/* Seed Control (Replaces Temperature) */}
                <div className="flex items-center justify-between gap-3 text-xs">
                  <span className="font-medium w-32" style={{ color: 'var(--text-primary)' }}>Seed</span>
                  <div className="flex items-center gap-2 flex-1">
                    <input
                      type="number"
                      disabled={isRandomSeed}
                      value={isRandomSeed ? '' : (seed ?? 42)}
                      onChange={(e) => setSeed(parseInt(e.target.value) || 0)}
                      placeholder={isRandomSeed ? "Randomized" : "Seed (e.g. 42)"}
                      className="flex-1 rounded-lg px-2.5 py-1 text-xs font-mono border focus:outline-none focus:border-purple-500 disabled:opacity-50"
                      style={{
                        backgroundColor: 'var(--bg-card-inner)',
                        borderColor: 'var(--border-inner)',
                        color: 'var(--text-primary)'
                      }}
                    />
                    <button
                      type="button"
                      onClick={() => setIsRandomSeed(!isRandomSeed)}
                      className={`px-2.5 py-1 rounded-lg text-[11px] font-medium border transition-colors cursor-pointer ${
                        isRandomSeed
                          ? 'bg-purple-600/30 text-purple-300 border-purple-500/40'
                          : 'hover:bg-slate-700/40 text-slate-400 border-slate-700'
                      }`}
                    >
                      {isRandomSeed ? "Randomized" : "Fixed Seed"}
                    </button>
                  </div>
                </div>

                {/* Synthesis Mode: Draft vs Final */}
                <div className="flex items-center justify-between gap-3 text-xs pt-0.5">
                  <span className="font-medium w-32" style={{ color: 'var(--text-primary)' }}>Quality Mode</span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setMode('draft')}
                      className={`px-3 py-1 rounded-lg text-xs font-medium border transition-colors cursor-pointer ${
                        mode === 'draft'
                          ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 font-semibold'
                          : 'text-slate-400 border-slate-700 hover:bg-slate-800/40'
                      }`}
                      title="Draft mode (10 ODE steps) for fast previews"
                    >
                      Draft (10 Steps)
                    </button>
                    <button
                      type="button"
                      onClick={() => setMode('final')}
                      className={`px-3 py-1 rounded-lg text-xs font-medium border transition-colors cursor-pointer ${
                        mode === 'final'
                          ? 'bg-purple-500/20 text-purple-300 border-purple-500/40 font-semibold'
                          : 'text-slate-400 border-slate-700 hover:bg-slate-800/40'
                      }`}
                      title="Final mode (18 ODE steps) for export quality"
                    >
                      Final (18 Steps)
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Centered Spanning Primary CTA Button, Safety Consent & Live Progress */}
          <div className="flex flex-col items-center pt-1 space-y-3">
            {/* Safety & Consent Checkbox */}
            <div className="flex items-center justify-center gap-2 text-xs">
              <input
                type="checkbox"
                id="consentCheckbox"
                checked={consentGiven}
                onChange={(e) => setConsentGiven(e.target.checked)}
                className="rounded border-slate-600 text-purple-600 focus:ring-purple-500 cursor-pointer"
              />
              <label htmlFor="consentCheckbox" className="cursor-pointer select-none" style={{ color: 'var(--text-secondary)' }}>
                I confirm I have the rights/consent to clone this voice.
              </label>
            </div>

            <button
              onClick={handleGenerate}
              disabled={isGenerating || !targetText.trim() || !consentGiven}
              className="w-full max-w-[540px] py-3.5 px-8 rounded-full generate-cta-glow text-white font-bold text-[15px] flex items-center justify-center gap-3 disabled:opacity-50 cursor-pointer shadow-xl select-none transition-all"
            >
              {/* Animated Waveform Icon Lines */}
              <div className="flex items-center gap-0.5 h-4">
                <span className={`w-0.5 rounded-full bg-white ${isGenerating ? 'animate-wave-bar' : 'h-2'}`}></span>
                <span className={`w-0.5 rounded-full bg-white ${isGenerating ? 'animate-wave-bar' : 'h-3.5'}`} style={{ animationDelay: '0.1s' }}></span>
                <span className={`w-0.5 rounded-full bg-white ${isGenerating ? 'animate-wave-bar' : 'h-2.5'}`} style={{ animationDelay: '0.2s' }}></span>
                <span className={`w-0.5 rounded-full bg-white ${isGenerating ? 'animate-wave-bar' : 'h-4'}`} style={{ animationDelay: '0.3s' }}></span>
                <span className={`w-0.5 rounded-full bg-white ${isGenerating ? 'animate-wave-bar' : 'h-1.5'}`} style={{ animationDelay: '0.15s' }}></span>
              </div>

              <span>{isGenerating ? `Synthesizing Audio (${progressPercent}%)...` : 'Generate Speech'}</span>

              <div className="w-5 h-5 rounded-full bg-white/20 flex items-center justify-center ml-1">
                <Play className="w-2.5 h-2.5 fill-white ml-0.5" />
              </div>
            </button>

            {/* Glowing Percentage Progress Bar when generating */}
            {isGenerating && (
              <div
                className="w-full max-w-[540px] p-4 rounded-2xl border shadow-2xl transition-all duration-300"
                style={{
                  backgroundColor: 'var(--bg-card)',
                  borderColor: 'var(--border-card)'
                }}
              >
                {/* Header row: Stage text, Percentage badge & Cancel button */}
                <div className="flex items-center justify-between mb-2 text-xs">
                  <div className="flex items-center gap-2 font-medium truncate max-w-[320px]" style={{ color: 'var(--text-primary)' }}>
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
                    </span>
                    <span className="truncate">{progressStage || 'Processing neural speech...'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-mono text-slate-400">
                      {elapsedSeconds}s
                    </span>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold font-mono bg-gradient-to-r from-purple-500/20 to-blue-500/20 text-cyan-300 border border-cyan-400/40 shadow-sm">
                      {progressPercent}%
                    </span>
                    <button
                      type="button"
                      onClick={handleCancel}
                      className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 flex items-center gap-1 transition-all cursor-pointer shadow-sm hover:scale-105 active:scale-95"
                      title="Cancel synthesis work"
                    >
                      <XCircle className="w-3 h-3 text-rose-400" />
                      <span>Cancel</span>
                    </button>
                  </div>
                </div>

                {/* The Progress Track and Animated Gradient Fill */}
                <div
                  className="relative w-full h-3 rounded-full overflow-hidden border"
                  style={{
                    backgroundColor: 'var(--bg-card-inner)',
                    borderColor: 'var(--border-inner)'
                  }}
                >
                  <div
                    className="h-full rounded-full transition-all duration-300 ease-out relative"
                    style={{
                      width: `${Math.max(4, Math.min(100, progressPercent))}%`,
                      background: 'linear-gradient(90deg, #06b6d4 0%, #8b5cf6 50%, #ec4899 100%)',
                      boxShadow: '0 0 16px rgba(139, 92, 246, 0.75)'
                    }}
                  >
                    {/* Glowing highlight line on leading edge */}
                    <span className="absolute top-0 bottom-0 right-0 w-2 bg-white/90 rounded-full blur-[0.5px]"></span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Side: Voice Profile, Model & Output Settings (Col 10-12) */}
        <div className="col-span-12 lg:col-span-3 space-y-4">
          {/* Card 1: Voice Profile matching Image 1 */}
          <div
            className="rounded-2xl p-4 space-y-3 shadow-xl border transition-colors"
            style={{
              backgroundColor: 'var(--bg-card)',
              borderColor: 'var(--border-card)'
            }}
          >
            <div className="flex items-center gap-2 text-xs font-bold" style={{ color: 'var(--text-primary)' }}>
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
                className="w-full rounded-xl px-3.5 py-2.5 text-xs font-medium focus:outline-none focus:border-purple-500 appearance-none pr-8 cursor-pointer border transition-colors"
                style={{
                  backgroundColor: 'var(--bg-card-inner)',
                  borderColor: 'var(--border-inner)',
                  color: 'var(--text-primary)'
                }}
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
                className="px-3 py-2 bg-[#2d1b69] hover:bg-[#3b248a] active:scale-95 text-purple-200 border border-purple-500/40 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all cursor-pointer"
              >
                <Save className="w-3.5 h-3.5 text-purple-300" />
                Save Profile
              </button>
              <button
                onClick={() => alert("Profile management opened.")}
                className="px-3 py-2 active:scale-95 text-slate-300 border rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all cursor-pointer"
                style={{
                  backgroundColor: 'var(--bg-card-inner)',
                  borderColor: 'var(--border-inner)'
                }}
              >
                <Settings className="w-3.5 h-3.5 text-slate-400" />
                Manage
              </button>
            </div>
          </div>

          {/* Card 2: Model matching Image 1 */}
          <div
            className="rounded-2xl p-4 space-y-3 shadow-xl border transition-colors"
            style={{
              backgroundColor: 'var(--bg-card)',
              borderColor: 'var(--border-card)'
            }}
          >
            <div className="flex items-center gap-2 text-xs font-bold" style={{ color: 'var(--text-primary)' }}>
              <Cpu className="w-4 h-4 text-cyan-400" />
              <span>Model</span>
            </div>
            <div className="relative">
              <div
                className="w-full rounded-xl px-3.5 py-2.5 text-xs font-medium flex items-center justify-between border transition-colors"
                style={{
                  backgroundColor: 'var(--bg-card-inner)',
                  borderColor: 'var(--border-inner)',
                  color: 'var(--text-primary)'
                }}
              >
                <span>IndicF5 (English)</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#064e3b] text-[#34d399] border border-[#059669]/40 mr-5 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  Loaded
                </span>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-3 top-3 pointer-events-none" />
            </div>
          </div>

          {/* Card 3: Output Format matching Image 1 */}
          <div
            className="rounded-2xl p-4 space-y-3 shadow-xl border transition-colors"
            style={{
              backgroundColor: 'var(--bg-card)',
              borderColor: 'var(--border-card)'
            }}
          >
            <div className="flex items-center gap-2 text-xs font-bold" style={{ color: 'var(--text-primary)' }}>
              <FileText className="w-4 h-4 text-blue-400" />
              <span>Output Format</span>
            </div>
            <div className="relative">
              <select
                value={outputFormat}
                onChange={(e) => setOutputFormat(e.target.value)}
                className="w-full rounded-xl px-3.5 py-2.5 text-xs font-medium focus:outline-none focus:border-purple-500 appearance-none pr-8 cursor-pointer border transition-colors"
                style={{
                  backgroundColor: 'var(--bg-card-inner)',
                  borderColor: 'var(--border-inner)',
                  color: 'var(--text-primary)'
                }}
              >
                <option>WAV (Lossless)</option>
                <option>MP3 (320kbps)</option>
                <option>FLAC (Lossless)</option>
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-3 top-3 pointer-events-none" />
            </div>
          </div>

          {/* Card 4: Compute Engine & Device Selector (TODO-4) */}
          <div
            className="rounded-2xl p-4 space-y-3 shadow-xl border transition-colors"
            style={{
              backgroundColor: 'var(--bg-card)',
              borderColor: 'var(--border-card)'
            }}
          >
            <div className="flex items-center justify-between text-xs font-bold" style={{ color: 'var(--text-primary)' }}>
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-purple-400" />
                <span>Compute Engine</span>
              </div>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border flex items-center gap-1 ${
                systemMetrics?.gpu_name
                  ? 'bg-purple-500/10 text-purple-300 border-purple-500/30'
                  : 'bg-blue-500/10 text-blue-300 border-blue-500/30'
              }`}>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                {systemMetrics?.gpu_name ? 'Colab GPU' : 'Intel CPU'}
              </span>
            </div>
            <div className="relative">
              <select
                value={computeDevice}
                onChange={(e) => setComputeDevice(e.target.value as any)}
                className="w-full rounded-xl px-3.5 py-2.5 text-xs font-medium focus:outline-none focus:border-purple-500 appearance-none pr-8 cursor-pointer border transition-colors"
                style={{
                  backgroundColor: 'var(--bg-card-inner)',
                  borderColor: 'var(--border-inner)',
                  color: 'var(--text-primary)'
                }}
              >
                <option value="auto">Auto-Detect (Best Available)</option>
                <option value="cpu">Local CPU (Intel Core i5-13H)</option>
                <option value="remote_gpu">Google Colab GPU Cloud (T4/A100)</option>
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-3 top-3 pointer-events-none" />
            </div>
            <div className="text-[10.5px] text-slate-400 leading-tight">
              {computeDevice === 'remote_gpu' || systemMetrics?.gpu_name
                ? '⚡ 32 ODE steps on GPU (~4.6s per utterance)'
                : '💻 10 ODE steps on local physical P-cores'}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Section: Output & Evaluation matching Image 1 */}
      <div
        className="rounded-2xl p-5 shadow-2xl space-y-3 border transition-colors"
        style={{
          backgroundColor: 'var(--bg-card)',
          borderColor: 'var(--border-card)'
        }}
      >
        <div className="flex items-center gap-2 text-xs font-bold tracking-wide" style={{ color: 'var(--text-primary)' }}>
          <div className="w-4 h-4 rounded border border-purple-400 flex items-center justify-center">
            <span className="w-1.5 h-1.5 bg-purple-400 rounded-sm"></span>
          </div>
          <span>Output & Evaluation</span>
        </div>

        {/* Real-time Download Progress Bar and Status */}
        {downloadProgress.status && (
          <div
            className="rounded-xl p-3 border space-y-1.5 transition-all shadow-sm"
            style={{
              backgroundColor: 'var(--bg-card-inner)',
              borderColor: downloadProgress.isDownloading ? 'rgba(59, 130, 246, 0.4)' : 'rgba(16, 185, 129, 0.4)'
            }}
          >
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-blue-400 flex items-center gap-1.5 truncate">
                {downloadProgress.isDownloading ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400 shrink-0" />
                ) : (
                  <CheckCircle className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                )}
                <span className="truncate">{downloadProgress.status}</span>
              </span>
              <span className="font-mono text-blue-300 font-bold ml-2 shrink-0">{downloadProgress.percent}%</span>
            </div>
            {downloadProgress.isDownloading && (
              <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full transition-all duration-150"
                  style={{ width: `${downloadProgress.percent}%` }}
                />
              </div>
            )}
          </div>
        )}

        <div className="grid grid-cols-12 gap-5 items-center">
          {/* Left Player Box matching Image 1 */}
          <div
            className="col-span-12 lg:col-span-7 rounded-2xl p-4 flex items-center gap-4 border transition-colors"
            style={{
              backgroundColor: 'var(--bg-card-inner)',
              borderColor: 'var(--border-inner)'
            }}
          >
            <button
              onClick={toggleOutputPlay}
              disabled={!lastJob}
              className="w-11 h-11 rounded-full bg-gradient-to-tr from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 active:scale-90 flex items-center justify-center text-white purple-play-glow shrink-0 disabled:opacity-40 transition-all cursor-pointer"
            >
              {isPlaying ? <Pause className="w-5 h-5 fill-white" /> : <Play className="w-5 h-5 fill-white ml-0.5" />}
            </button>

            {/* Detailed Waveform Visualization with Dynamic Active Seeking (TODO-2) */}
            <div
              className="flex-1 flex items-center gap-0.5 h-9 overflow-hidden cursor-pointer group"
              title="Click along waveform to scrub/seek playback position"
              onClick={(e) => {
                if (!lastJob || !audioRef.current) return;
                const rect = e.currentTarget.getBoundingClientRect();
                const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
                audioRef.current.currentTime = ratio * (lastJob.duration_seconds || 1);
                setAudioCurrentTime(audioRef.current.currentTime);
              }}
            >
              {[8, 16, 24, 38, 20, 48, 65, 80, 50, 62, 78, 92, 85, 70, 55, 35, 45, 60, 75, 52, 38, 22, 34, 48, 62, 42, 28, 16, 28, 45, 32, 18, 10, 22, 35, 48, 30, 16].map((h, i) => (
                <div
                  key={i}
                  className={`flex-1 rounded-full transition-all ${lastJob
                    ? i < (audioCurrentTime / (lastJob.duration_seconds || 1)) * 38
                      ? isPlaying ? 'bg-purple-300 animate-wave-bar' : 'bg-purple-300'
                      : 'bg-[#6366f1]/70'
                    : 'bg-slate-600/40'
                    }`}
                  style={{
                    height: `${h}%`,
                    animationDelay: `${(i % 6) * 0.08}s`
                  }}
                />
              ))}
            </div>

            <div className="text-xs font-mono whitespace-nowrap" style={{ color: 'var(--text-secondary)' }}>
              0:0{Math.floor(audioCurrentTime)} / 0:0{lastJob ? Math.round(lastJob.duration_seconds) : '6'}
            </div>

            <div className="flex items-center gap-2 border-l border-[#242b4e] pl-3 text-slate-400">
              <button title="Volume" className="hover:text-white transition-colors p-1 cursor-pointer">
                <Volume2 className="w-4 h-4" />
              </button>
              {lastJob?.output_audio_url && (
                <button
                  type="button"
                  onClick={handleDownloadAudio}
                  disabled={downloadProgress.isDownloading}
                  title="Download WAV with progress"
                  className="hover:text-purple-400 transition-colors p-1 cursor-pointer disabled:opacity-40"
                >
                  {downloadProgress.isDownloading ? (
                    <Loader2 className="w-4 h-4 animate-spin text-purple-400" />
                  ) : (
                    <Download className="w-4 h-4" />
                  )}
                </button>
              )}
              <button
                title="Share"
                onClick={() => alert("Audio link copied to clipboard.")}
                className="hover:text-white transition-colors p-1 cursor-pointer"
              >
                <Share2 className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Right: Evaluation (Auto) 4 Stat Cards matching Image 1 */}
          <div
            className="col-span-12 lg:col-span-5 rounded-2xl p-3.5 space-y-2 border transition-colors"
            style={{
              backgroundColor: 'var(--bg-card-inner)',
              borderColor: 'var(--border-inner)'
            }}
          >
            <div className="text-[11px] font-bold flex items-center gap-1.5" style={{ color: 'var(--text-primary)' }}>
              <span className="w-2 h-2 rounded-full bg-purple-400"></span>
              <span>Evaluation (Auto)</span>
            </div>

            <div className="grid grid-cols-4 gap-2 text-center">
              {/* Word Error Rate (WER) - Honest Whisper Metric */}
              <div
                className="rounded-xl p-2.5 border transition-colors"
                style={{
                  backgroundColor: 'var(--bg-card)',
                  borderColor: 'var(--border-card)'
                }}
              >
                <div className="text-[10px] font-medium leading-tight" style={{ color: 'var(--text-secondary)' }}>
                  Word Error<br />Rate (WER)
                </div>
                <div className={`text-lg font-extrabold mt-1 font-mono ${lastJob && lastJob.wer <= 0.08 ? 'text-[#00e676]' : 'text-amber-400'}`}>
                  {lastJob ? `${(lastJob.wer * 100).toFixed(1)}%` : '--'}
                </div>
                <div className="text-[9px] text-slate-500 mt-0.5">Whisper int8</div>
              </div>

              {/* Character Error Rate (CER) */}
              <div
                className="rounded-xl p-2.5 border transition-colors"
                style={{
                  backgroundColor: 'var(--bg-card)',
                  borderColor: 'var(--border-card)'
                }}
              >
                <div className="text-[10px] font-medium leading-tight" style={{ color: 'var(--text-secondary)' }}>
                  Character Error<br />Rate (CER)
                </div>
                <div className="text-lg font-extrabold text-[#00e676] mt-1 font-mono">
                  {lastJob ? `${(lastJob.cer * 100).toFixed(1)}%` : '--'}
                </div>
                <div className="text-[9px] text-slate-500 mt-0.5">Levenshtein</div>
              </div>

              {/* Speaker Similarity - Honest ECAPA-TDNN Cosine Similarity */}
              <div
                className="rounded-xl p-2.5 border transition-colors"
                style={{
                  backgroundColor: 'var(--bg-card)',
                  borderColor: 'var(--border-card)'
                }}
              >
                <div className="text-[10px] font-medium leading-tight" style={{ color: 'var(--text-secondary)' }}>
                  Speaker<br />Similarity
                </div>
                <div className="text-lg font-extrabold text-[#00e676] mt-1 font-mono">
                  {lastJob ? `${(lastJob.speaker_similarity * 100).toFixed(1)}%` : '--'}
                </div>
                <div className="text-[9px] text-slate-500 mt-0.5">ECAPA-TDNN</div>
              </div>

              {/* Real-Time Factor (RTF) */}
              <div
                className="rounded-xl p-2.5 border transition-colors"
                style={{
                  backgroundColor: 'var(--bg-card)',
                  borderColor: 'var(--border-card)'
                }}
              >
                <div className="text-[10px] font-medium leading-tight" style={{ color: 'var(--text-secondary)' }}>
                  Real-Time<br />Factor (RTF)
                </div>
                <div className="text-lg font-extrabold mt-1 font-mono" style={{ color: 'var(--text-primary)' }}>
                  {lastJob
                    ? `${(lastJob.rtf || (lastJob.duration_seconds > 0 ? lastJob.inference_time_seconds / lastJob.duration_seconds : 0)).toFixed(2)}x`
                    : '--'}
                </div>
                <div className="text-[9px] text-slate-500 mt-0.5 font-mono">
                  {lastJob ? `${lastJob.inference_time_seconds.toFixed(1)}s` : ''}
                </div>
              </div>
            </div>

            {/* Completeness Gate Per-Chunk Metrics Breakdown */}
            {lastJob?.chunk_metrics && lastJob.chunk_metrics.length > 0 && (
              <div className="pt-2 border-t border-[var(--border-inner)] space-y-1.5 text-left">
                <div className="flex items-center justify-between text-[11px] font-semibold text-slate-400">
                  <span>Completeness Gate ({lastJob.chunk_metrics.length} {lastJob.chunk_metrics.length === 1 ? 'chunk' : 'chunks'})</span>
                  <span className="font-mono text-[10px]">
                    Total retries: {lastJob.total_retries ?? 0}
                  </span>
                </div>
                <div className="space-y-1 max-h-24 overflow-y-auto pr-1">
                  {lastJob.chunk_metrics.map((cm, ci) => (
                    <div
                      key={ci}
                      className="flex items-center justify-between text-[11px] rounded-lg px-2.5 py-1 font-mono"
                      style={{
                        backgroundColor: 'var(--bg-card)',
                        borderColor: 'var(--border-card)'
                      }}
                    >
                      <span className="truncate max-w-[180px] text-slate-300">
                        #{ci + 1}: "{cm.text}"
                      </span>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className={`text-[10px] ${cm.wer <= 0.08 ? 'text-emerald-400' : 'text-amber-400'}`}>
                          WER: {(cm.wer * 100).toFixed(1)}%
                        </span>
                        <span className="text-[10px] text-slate-400">
                          {cm.retries === 0 ? '✓ 1st try' : `⟳ ${cm.retries} ${cm.retries === 1 ? 'retry' : 'retries'}`}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
