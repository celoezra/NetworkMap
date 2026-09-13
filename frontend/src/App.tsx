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
import { fetchApi } from './services/api';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [selectedSwitchId, setSelectedSwitchId] = useState<number | null>(null);

  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [racks, setRacks] = useState<Rack[]>([]);
  const [switches, setSwitches] = useState<Switch[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [vlans, setVlans] = useState<VLAN[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);

  const loadData = async () => {
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
    loadData();
  }, [currentTab]);

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
    <Layout currentTab={currentTab} setCurrentTab={setCurrentTab} onSelectEntity={handleSelectEntity}>
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
