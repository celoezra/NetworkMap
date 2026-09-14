import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  Network,
  Server,
  HardDrive,
  Cpu,
  MapPin,
  Layers,
  Search,
  History,
  Database,
  Moon,
  Sun,
  Menu,
  ChevronRight,
  X,
} from 'lucide-react';
import type { SearchResult } from '../types';
import { fetchApi } from '../services/api';

interface LayoutProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  children: React.ReactNode;
  onSelectEntity?: (type: string, id: number) => void;
  headerRight?: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ currentTab, setCurrentTab, children, onSelectEntity, headerRight }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult | null>(null);
  const [showSearchResults, setShowSearchResults] = useState(false);

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (searchQuery.trim().length >= 2) {
        fetchApi<SearchResult>(`/search?q=${encodeURIComponent(searchQuery)}`)
          .then((data) => {
            setSearchResults(data);
            setShowSearchResults(true);
          })
          .catch((err) => console.error(err));
      } else {
        setSearchResults(null);
        setShowSearchResults(false);
      }
    }, 300);

    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery]);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'network-map', label: 'Mapa da Rede', icon: Network },
    { id: 'racks', label: 'Racks', icon: Server },
    { id: 'switches', label: 'Switches', icon: HardDrive },
    { id: 'devices', label: 'Equipamentos', icon: Cpu },
    { id: 'locations', label: 'Locais', icon: MapPin },
    { id: 'vlans', label: 'VLANs', icon: Layers },
    { id: 'audit', label: 'Histórico', icon: History },
    { id: 'backup', label: 'Backup e Configs', icon: Database },
  ];

  const handleResultClick = (type: string, id: number) => {
    setShowSearchResults(false);
    setSearchQuery('');
    if (type === 'switch') setCurrentTab('switches');
    else if (type === 'rack') setCurrentTab('racks');
    else if (type === 'location') setCurrentTab('locations');
    else if (type === 'vlan') setCurrentTab('vlans');
    else if (type === 'device') setCurrentTab('devices');
    
    if (onSelectEntity) onSelectEntity(type, id);
  };

  return (
    <div className={`min-h-screen flex bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-slate-100 transition-colors duration-200`}>
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-64' : 'w-20'} bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 transition-all duration-300 flex flex-col z-30 sticky top-0 h-screen`}>
        {/* Logo Header */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center space-x-3 overflow-hidden">
            <div className="bg-blue-600 text-white p-2 rounded-xl shadow-md flex-shrink-0">
              <Network className="w-5 h-5" />
            </div>
            {sidebarOpen && (
              <span className="font-bold text-lg tracking-tight text-slate-800 dark:text-white whitespace-nowrap">
                Network<span className="text-blue-600">Map</span>
              </span>
            )}
          </div>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400"
          >
            <Menu className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Menu */}
        <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentTab(item.id)}
                className={`w-full flex items-center ${sidebarOpen ? 'px-3' : 'justify-center px-0'} py-2.5 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-blue-50 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 font-semibold'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700/50 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-blue-600 dark:text-blue-400' : 'text-slate-400 dark:text-slate-500'}`} />
                {sidebarOpen && <span className="ml-3 truncate">{item.label}</span>}
              </button>
            );
          })}
        </nav>

        {/* Footer info */}
        {sidebarOpen && (
          <div className="p-4 border-t border-slate-200 dark:border-slate-700 text-xs text-slate-400 dark:text-slate-500 text-center">
            NetworkMap Enterprise v1.0 <br /> SQLCipher Encrypted DB
          </div>
        )}
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        {/* Top Header */}
        <header className="h-16 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-6 flex items-center justify-between sticky top-0 z-20 shadow-sm">
          {/* Breadcrumbs */}
          <div className="flex items-center space-x-2 text-sm text-slate-500 dark:text-slate-400">
            <span>Infraestrutura</span>
            <ChevronRight className="w-4 h-4" />
            <span className="font-semibold text-slate-800 dark:text-white capitalize">
              {navItems.find((n) => n.id === currentTab)?.label || currentTab}
            </span>
          </div>

          {/* Global Search Bar & Actions */}
          <div className="flex items-center space-x-4">
            <div className="relative w-80">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Buscar IP, Hostname, Switch, Local, MAC..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onFocus={() => searchQuery.trim().length >= 2 && setShowSearchResults(true)}
                  className="w-full pl-9 pr-8 py-1.5 bg-slate-100 dark:bg-slate-700/60 border border-transparent focus:border-blue-500 rounded-lg text-sm focus:outline-none dark:text-white placeholder-slate-400 transition"
                />
                {searchQuery && (
                  <button
                    onClick={() => {
                      setSearchQuery('');
                      setShowSearchResults(false);
                    }}
                    className="absolute right-2.5 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>

              {/* Search Results Dropdown */}
              {showSearchResults && searchResults && (
                <div className="absolute right-0 mt-2 w-96 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-2xl max-h-96 overflow-y-auto z-50 p-2 text-sm">
                  <div className="px-3 py-1.5 text-xs font-semibold text-slate-400 border-b border-slate-100 dark:border-slate-700 flex justify-between">
                    <span>Resultados da Busca</span>
                    <span>{searchResults.total_matches} encontrado(s)</span>
                  </div>

                  {searchResults.total_matches === 0 ? (
                    <div className="p-4 text-center text-slate-500 dark:text-slate-400 text-xs">
                      Nenhum item correspondente encontrado.
                    </div>
                  ) : (
                    <div className="divide-y divide-slate-100 dark:divide-slate-700/50">
                      {/* Devices */}
                      {searchResults.devices.map((d) => (
                        <div
                          key={`dev-${d.id}`}
                          onClick={() => handleResultClick('device', d.id)}
                          className="p-2.5 hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer rounded-lg transition"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-blue-600 dark:text-blue-400">{d.name}</span>
                            <span className="text-xs bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded text-slate-500">
                              {d.device_type}
                            </span>
                          </div>
                          <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                            IP: {d.ip_address || 'N/A'} | Local: {d.location_name || 'N/A'} | Switch: {d.switch_name || 'N/A'} (P{d.port_number || '?'})
                          </div>
                        </div>
                      ))}

                      {/* Switches */}
                      {searchResults.switches.map((s) => (
                        <div
                          key={`sw-${s.id}`}
                          onClick={() => handleResultClick('switch', s.id)}
                          className="p-2.5 hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer rounded-lg transition"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-indigo-600 dark:text-indigo-400">{s.name} ({s.hostname})</span>
                            <span className="text-xs bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 px-2 py-0.5 rounded">
                              Switch ({s.port_count}P)
                            </span>
                          </div>
                          <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                            IP: {s.ip_address || 'N/A'} | Rack: {s.rack_name || 'Sem Rack'}
                          </div>
                        </div>
                      ))}

                      {/* Racks */}
                      {searchResults.racks.map((r) => (
                        <div
                          key={`rack-${r.id}`}
                          onClick={() => handleResultClick('rack', r.id)}
                          className="p-2.5 hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer rounded-lg transition"
                        >
                          <div className="font-semibold text-emerald-600 dark:text-emerald-400">{r.name}</div>
                          <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Local: {r.location}</div>
                        </div>
                      ))}

                      {/* Locations */}
                      {searchResults.locations.map((l) => (
                        <div
                          key={`loc-${l.id}`}
                          onClick={() => handleResultClick('location', l.id)}
                          className="p-2.5 hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer rounded-lg transition"
                        >
                          <div className="font-semibold text-amber-600 dark:text-amber-400">{l.name}</div>
                          <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Setor: {l.sector || 'N/A'}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Action Bar Right */}
            <div className="flex items-center space-x-4">
              {headerRight}

              {/* Dark Mode Toggle */}
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="p-2 rounded-xl bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 transition"
                title="Alternar Modo Escuro"
              >
                {darkMode ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </header>

        {/* Dynamic Page Container */}
        <main className="flex-1 p-6 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
};
