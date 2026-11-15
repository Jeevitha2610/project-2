import { useState, useEffect } from 'react';
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

export function App() {
  const [currentTab, setCurrentTab] = useState('synthesis');
  const [profiles, setProfiles] = useState<VoiceProfile[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<VoiceProfile | null>(null);
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);

  const fetchProfiles = async () => {
    try {
      const data = await ProfileAPI.getProfiles();
      setProfiles(data);
      if (data.length > 0 && !selectedProfile) {
        setSelectedProfile(data[0]);
      }
    } catch (e) {
      console.warn('Could not fetch profiles:', e);
    }
  };

  const fetchMetrics = async () => {
    try {
      const m = await MonitoringAPI.getMetrics();
      setSystemMetrics(m);
    } catch (e) {
      console.warn('Could not fetch metrics:', e);
    }
  };

  useEffect(() => {
    fetchProfiles();
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex min-h-screen bg-[#0a0c16] text-slate-100 font-sans antialiased selection:bg-purple-600 selection:text-white">
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
      </div>
    </div>
  );
}

export default App;
