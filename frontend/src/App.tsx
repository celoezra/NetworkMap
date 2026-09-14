import React, { useState, useEffect } from 'react';
import { Layout } from './components/Layout';
import { DashboardView } from './components/DashboardView';
import { RacksView } from './components/RacksView';
import { SwitchesView } from './components/SwitchesView';
import { LocationsView } from './components/LocationsView';
import { DevicesView } from './components/DevicesView';
import { VlansView } from './components/VlansView';
import { NetworkMapView } from './components/NetworkMapView';
import { AuditLogsView } from './components/AuditLogsView';
import { BackupView } from './components/BackupView';

import type { Rack, Switch, Location, VLAN, Device, DashboardStats } from './types';
import { fetchApi, setAuthToken } from './services/api';
import { useMsal, useIsAuthenticated } from '@azure/msal-react';
import { loginRequest } from './authConfig';
import { UnitSelector } from './components/UnitSelector';

export const App: React.FC = () => {
  const { instance, accounts } = useMsal();
  const isAuthenticated = useIsAuthenticated();
  const [authError, setAuthError] = useState<string | null>(null);

  const [currentTab, setCurrentTab] = useState('dashboard');
  const [selectedSwitchId, setSelectedSwitchId] = useState<number | null>(null);

  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [racks, setRacks] = useState<Rack[]>([]);
  const [switches, setSwitches] = useState<Switch[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [vlans, setVlans] = useState<VLAN[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);

  const [units, setUnits] = useState<any[]>([]);
  const [currentUnit, setCurrentUnit] = useState<number | null>(null);

  const handleLogin = () => {
    instance.loginPopup(loginRequest).catch(e => {
      console.error(e);
    });
  };

  useEffect(() => {
    if (isAuthenticated && accounts.length > 0) {
      instance.acquireTokenSilent({
        ...loginRequest,
        account: accounts[0]
      }).then((response) => {
        setAuthToken(response.accessToken);
        fetchMyProfile();
      }).catch((e) => {
        console.error("Token acquisition failed:", e);
        setAuthError("Failed to acquire token");
      });
    }
  }, [isAuthenticated, accounts, instance]);

  const fetchMyProfile = async () => {
    try {
      const profile = await fetchApi<any>('/users/me');
      setUnits(profile.units);
    } catch (err: any) {
      setAuthError(err.message || 'Access Denied');
    }
  };

  const loadData = async () => {
    if (!currentUnit) return;
    try {
      const [statsRes, racksRes, switchesRes, locsRes, vlansRes, devRes] = await Promise.all([
        fetchApi<DashboardStats>('/dashboard'),
        fetchApi<Rack[]>('/racks'),
        fetchApi<Switch[]>('/switches'),
        fetchApi<Location[]>('/locations'),
        fetchApi<VLAN[]>('/vlans'),
        fetchApi<Device[]>('/devices'),
      ]);

      setStats(statsRes);
      setRacks(racksRes);
      setSwitches(switchesRes);
      setLocations(locsRes);
      setVlans(vlansRes);
      setDevices(devRes);
    } catch (err) {
      console.error('Erro ao carregar dados do sistema:', err);
    }
  };

  useEffect(() => {
    if (currentUnit) {
      loadData();
    }
  }, [currentTab, currentUnit]);

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="bg-slate-800 p-8 rounded-lg shadow-xl text-center max-w-md w-full">
          <h1 className="text-2xl font-bold text-white mb-6">NETWORKMAP ENTERPRISE</h1>
          <button
            onClick={handleLogin}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded transition duration-200"
          >
            Entrar com Microsoft
          </button>
        </div>
      </div>
    );
  }

  if (authError) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="bg-slate-800 p-8 rounded-lg shadow-xl text-center max-w-md w-full">
          <h1 className="text-2xl font-bold text-red-500 mb-4">Acesso Negado</h1>
          <p className="text-slate-300 mb-6">{authError}</p>
          <button
            onClick={() => instance.logoutPopup()}
            className="bg-slate-700 hover:bg-slate-600 text-white font-semibold py-2 px-4 rounded"
          >
            Sair
          </button>
        </div>
      </div>
    );
  }

  const handleSelectEntity = (type: string, id: number) => {
    if (type === 'switch') {
      setSelectedSwitchId(id);
      setCurrentTab('switches');
    }
  };

  const handleSelectSwitchFromRack = (switchId: number) => {
    setSelectedSwitchId(switchId);
    setCurrentTab('switches');
  };

  return (
    <Layout 
      currentTab={currentTab} 
      setCurrentTab={setCurrentTab} 
      onSelectEntity={handleSelectEntity}
      headerRight={<UnitSelector units={units} currentUnit={currentUnit} setCurrentUnit={setCurrentUnit} />}
    >
      {currentTab === 'dashboard' && <DashboardView stats={stats} onNavigate={setCurrentTab} />}
      {currentTab === 'network-map' && <NetworkMapView />}
      {currentTab === 'racks' && (
        <RacksView
          racks={racks}
          switches={switches}
          onRefresh={loadData}
          onSelectSwitch={handleSelectSwitchFromRack}
        />
      )}
      {currentTab === 'switches' && (
        <SwitchesView
          switches={switches}
          racks={racks}
          vlans={vlans}
          locations={locations}
          devices={devices}
          selectedSwitchId={selectedSwitchId}
          onRefresh={loadData}
        />
      )}
      {currentTab === 'locations' && (
        <LocationsView locations={locations} devices={devices} switches={switches} onRefresh={loadData} />
      )}
      {currentTab === 'devices' && (
        <DevicesView
          devices={devices}
          locations={locations}
          vlans={vlans}
          switches={switches}
          onRefresh={loadData}
        />
      )}
      {currentTab === 'vlans' && <VlansView vlans={vlans} onRefresh={loadData} />}
      {currentTab === 'audit' && <AuditLogsView />}
      {currentTab === 'backup' && <BackupView />}
    </Layout>
  );
};

export default App;
