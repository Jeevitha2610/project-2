export interface VoiceProfile {
  id: string;
  name: string;
  description?: string;
  reference_audio_path: string;
  reference_audio_name: string;
  reference_audio_url?: string;
  reference_transcript: string;
  duration_seconds: number;
  sample_rate: number;
  channels: number;
  audio_format: string;
  model_compatibility: string;
  created_at: string;
  updated_at: string;
}

export interface GenerationJob {
  id: string;
  profile_id?: string;
  profile_name: string;
  target_text: string;
  speech_speed: number;
  pitch: number;
  temperature: number;
  seed?: number;
  output_format: string;
  status: string;
  output_audio_path?: string;
  output_audio_url?: string;
  duration_seconds: number;
  sample_rate: number;
  channels: number;
  peak_amplitude: number;
  snr_estimate: number;
  clipping_detected: boolean;
  silence_ratio: number;
  wer: number;
  cer: number;
  speaker_similarity: number;
  recognized_transcript?: string;
  inference_time_seconds: number;
  cpu_peak: number;
  ram_peak_mb: number;
  created_at: string;
}

export interface SystemMetrics {
  cpu_percent: number;
  ram_used_gb: number;
  ram_total_gb: number;
  ram_percent: number;
  disk_free_gb: number;
  device: string;
  model_name: string;
  model_status: string;
  queue_length: number;
}

export interface ModelInfo {
  id: string;
  name: string;
  display_name: string;
  language: string;
  license: string;
  device: string;
  status: string;
  ram_usage_mb: number;
  sample_rate: number;
}
