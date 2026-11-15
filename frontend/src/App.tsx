import { useState, useEffect, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { StudioPage } from './pages/StudioPage';
import { ProfilesPage } from './pages/ProfilesPage';
import { ModelsPage } from './pages/ModelsPage';
import { EvaluationPage } from './pages/EvaluationPage';
import { HistoryPage } from './pages/HistoryPage';
import { SystemMonitorPage } from './pages/SystemMonitorPage';
import { AudioLibraryPage } from './pages/AudioLibraryPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';
import { AboutPage } from './pages/AboutPage';

import type { VoiceProfile, SystemMetrics } from './types';
import { ProfileAPI, MonitoringAPI } from './services/api';

type Theme = 'dark' | 'light';

const THEME_KEY = 'voicestudio_theme';

function readStoredTheme(): Theme {
  try {
    return localStorage.getItem(THEME_KEY) === 'light' ? 'light' : 'dark';
  } catch {
    return 'dark';
  }
}

export function App() {
  const [currentTab, setCurrentTab] = useState('synthesis');
  const [profiles, setProfiles] = useState<VoiceProfile[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<VoiceProfile | null>(null);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [theme, setTheme] = useState<Theme>(readStoredTheme);

  // Sync the theme class on <html> (drives CSS variables + `dark:` variant) and persist it.
  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle('light', theme === 'light');
    root.classList.toggle('dark', theme === 'dark');
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch {
      // storage unavailable (e.g. privacy mode) — theme still applies for this session
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  };

  const fetchProfiles = useCallback(
    () =>
      ProfileAPI.getProfiles()
        .then((data) => {
          setProfiles(data);
          if (data.length > 0) {
            setSelectedProfile(prev => prev ?? data[0]);
          }
        })
        .catch((e: unknown) => console.warn('Could not fetch profiles:', e)),
    []
  );

  const fetchMetrics = useCallback(
    () =>
      MonitoringAPI.getMetrics()
        .then((m) => setSystemMetrics(m))
        .catch((e: unknown) => console.warn('Could not fetch metrics:', e)),
    []
  );

  useEffect(() => {
    fetchProfiles();
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 4000);
    return () => clearInterval(interval);
  }, [fetchProfiles, fetchMetrics]);

  return (
    <div 
      className="flex min-h-screen font-sans antialiased selection:bg-purple-600 selection:text-white transition-colors duration-200"
      style={{
        backgroundColor: 'var(--bg-page)',
        color: 'var(--text-primary)'
      }}
    >
      {/* Sidebar */}
      <Sidebar 
        currentTab={currentTab} 
        setCurrentTab={setCurrentTab} 
        systemMetrics={systemMetrics} 
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header 
          currentTab={currentTab} 
          setCurrentTab={setCurrentTab} 
          systemMetrics={systemMetrics} 
          theme={theme}
          toggleTheme={toggleTheme}
        />

        <main className="flex-1 pb-16">
          {currentTab === 'synthesis' && (
            <StudioPage
              profiles={profiles}
              selectedProfile={selectedProfile}
              setSelectedProfile={setSelectedProfile}
              onRefreshProfiles={fetchProfiles}
              systemMetrics={systemMetrics}
            />
          )}
          {currentTab === 'profiles' && (
            <ProfilesPage
              profiles={profiles}
              onRefresh={fetchProfiles}
              onSelect={(p) => {
                setSelectedProfile(p);
                setCurrentTab('synthesis');
              }}
            />
          )}
          {currentTab === 'models' && <ModelsPage />}
          {currentTab === 'evaluation' && <EvaluationPage />}
          {currentTab === 'history' && <HistoryPage />}
          {currentTab === 'monitor' && <SystemMonitorPage systemMetrics={systemMetrics} />}
          {currentTab === 'library' && <AudioLibraryPage />}
          {currentTab === 'reports' && <ReportsPage />}
          {currentTab === 'settings' && <SettingsPage />}
          {currentTab === 'about' && <AboutPage />}
        </main>

        {/* Global Footer with CC-BY-NC Non-Commercial Notice */}
        <footer
          className="py-2.5 px-6 border-t text-xs flex flex-wrap justify-between items-center gap-2 select-none"
          style={{
            backgroundColor: 'var(--bg-card)',
            borderColor: 'var(--border-card)',
            color: 'var(--text-muted)'
          }}
        >
          <span>VoiceStudio &bull; Local-first Neural Voice Cloning</span>
          <span className="font-mono text-[11px] text-amber-400 bg-amber-500/10 px-2.5 py-0.5 rounded-full border border-amber-500/20">
            F5-TTS pretrained weights are non-commercial (CC-BY-NC-4.0)
          </span>
        </footer>
      </div>
    </div>
  );
}

export default App;
