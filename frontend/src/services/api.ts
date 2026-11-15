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
  createProfile: async (formData: FormData): Promise<VoiceProfile> => {
    const res = await api.post('/profiles/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
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
};

export const SynthesisAPI = {
  generateSpeech: async (payload: {
    profile_id?: string;
    profile_name?: string;
    target_text: string;
    speech_speed: number;
    pitch: number;
    temperature: number;
    seed?: number;
    output_format: string;
    reference_audio_name?: string;
    reference_transcript?: string;
  }): Promise<GenerationJob> => {
    const res = await api.post('/synthesis/generate', payload);
    return res.data;
  },
  getHistory: async (): Promise<GenerationJob[]> => {
    const res = await api.get('/synthesis/history');
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
  uploadAudio: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post('/audio/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
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
