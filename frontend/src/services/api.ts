import axios from 'axios';
import type { VoiceProfile, GenerationJob, SystemMetrics, ModelInfo } from '../types';

const API_BASE = 'http://127.0.0.1:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE,
});

export const ProfileAPI = {
  getProfiles: async (): Promise<VoiceProfile[]> => {
    const res = await api.get('/profiles/');
    return res.data;
  },
  createProfile: async (
    formData: FormData,
    onUploadProgress?: (progress: { loaded: number; total: number; percent: number }) => void
  ): Promise<VoiceProfile> => {
    const res = await api.post('/profiles/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress) {
          const total = progressEvent.total || 0;
          const loaded = progressEvent.loaded || 0;
          const percent = total > 0 ? Math.round((loaded * 100) / total) : 0;
          onUploadProgress({ loaded, total, percent });
        }
      },
    });
    return res.data;
  },
  updateProfile: async (id: string, data: Partial<VoiceProfile>): Promise<VoiceProfile> => {
    const res = await api.put(`/profiles/${id}`, data);
    return res.data;
  },
  deleteProfile: async (id: string): Promise<void> => {
    await api.delete(`/profiles/${id}`);
  },
  getProcessingProgress: async (): Promise<{ stage: string; percent: number; message: string }> => {
    try {
      const res = await api.get('/profiles/progress');
      return res.data;
    } catch {
      return { stage: 'idle', percent: 0, message: '' };
    }
  },
};

export const SynthesisAPI = {
  generateSpeech: async (
    payload: {
      profile_id?: string;
      profile_name?: string;
      target_text: string;
      speech_speed: number;
      pitch: number;
      temperature: number;
      seed?: number;
      output_format: string;
      mode?: string;
      wer_threshold?: number;
      consent_given?: boolean;
      reference_audio_name?: string;
      reference_transcript?: string;
    },
    signal?: AbortSignal
  ): Promise<GenerationJob> => {
    const res = await api.post('/synthesis/generate', payload, { signal });
    return res.data;
  },
  cancelGeneration: async (): Promise<void> => {
    try {
      await api.post('/synthesis/cancel');
    } catch (_) {}
  },
  getHistory: async (): Promise<GenerationJob[]> => {
    const res = await api.get('/synthesis/history');
    return res.data;
  },
  getProgress: async (): Promise<{
    is_running: boolean;
    percent: number;
    stage: string;
    elapsed_seconds: number;
  }> => {
    const res = await api.get('/synthesis/progress');
    return res.data;
  },
  deleteGeneration: async (id: string): Promise<void> => {
    await api.delete(`/synthesis/history/${id}`);
  },
};

export const MonitoringAPI = {
  getMetrics: async (): Promise<SystemMetrics> => {
    const res = await api.get('/monitoring/');
    return res.data;
  },
};

export const ModelsAPI = {
  getModels: async (): Promise<ModelInfo[]> => {
    const res = await api.get('/models/');
    return res.data;
  },
  loadModel: async (modelId: string): Promise<void> => {
    await api.post(`/models/${modelId}/load`);
  },
  unloadModel: async (modelId: string): Promise<void> => {
    await api.post(`/models/${modelId}/unload`);
  },
};

export const AudioAPI = {
  uploadAudio: async (
    file: File,
    onProgress?: (progress: { loaded: number; total: number; percent: number }) => void
  ) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post('/audio/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const total = progressEvent.total || 0;
          const loaded = progressEvent.loaded || 0;
          const percent = total > 0 ? Math.round((loaded * 100) / total) : 0;
          onProgress({ loaded, total, percent });
        }
      },
    });
    return res.data;
  },
  transcribeAudio: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post('/audio/transcribe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },
};

export const FileDownloadAPI = {
  downloadAudioFile: async (
    audioUrl: string,
    filename: string,
    onProgress?: (progress: { loaded: number; total: number; percent: number }) => void
  ): Promise<void> => {
    const fullUrl = audioUrl.startsWith('http') ? audioUrl : `http://127.0.0.1:8000${audioUrl}`;
    const response = await axios.get(fullUrl, {
      responseType: 'blob',
      onDownloadProgress: (progressEvent) => {
        const total = progressEvent.total || 0;
        const loaded = progressEvent.loaded || 0;
        const percent = total > 0 ? Math.round((loaded * 100) / total) : 100;
        if (onProgress) {
          onProgress({ loaded, total, percent });
        }
      },
    });

    const blobUrl = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = blobUrl;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
  },
};
