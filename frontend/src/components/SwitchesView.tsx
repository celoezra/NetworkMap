import React, { useState } from 'react';
import { HardDrive, Plus, Edit2, Trash2 } from 'lucide-react';
import type { Switch, Rack, VLAN, Location, Device, SwitchPort } from '../types';
import { fetchApi } from '../services/api';

interface SwitchesViewProps {
  switches: Switch[];
  racks: Rack[];
  vlans: VLAN[];
  locations: Location[];
  devices: Device[];
  selectedSwitchId?: number | null;
  onRefresh: () => void;
}

export const SwitchesView: React.FC<SwitchesViewProps> = ({
  switches,
  racks,
  vlans,
  locations,
  devices,
  selectedSwitchId,
  onRefresh,
}) => {
  const [activeSwitchId, setActiveSwitchId] = useState<number | null>(
    selectedSwitchId || (switches.length > 0 ? switches[0].id : null)
  );

  // Switch modal state
  const [switchModalOpen, setSwitchModalOpen] = useState(false);
  const [editingSwitch, setEditingSwitch] = useState<Switch | null>(null);
  const [swName, setSwName] = useState('');
  const [swHostname, setSwHostname] = useState('');
  const [swIp, setSwIp] = useState('');
  const [swMac, setSwMac] = useState('');
  const [swPortCount, setSwPortCount] = useState<number>(24);
  const [swRackId, setSwRackId] = useState<number | ''>('');
  const [swManufacturer, setSwManufacturer] = useState('');
  const [swModel, setSwModel] = useState('');
  const [swError, setSwError] = useState('');

  // Port modal state
  const [portModalOpen, setPortModalOpen] = useState(false);
  const [selectedPort, setSelectedPort] = useState<SwitchPort | null>(null);
  const [portVlanId, setPortVlanId] = useState<number | ''>('');
  const [portLocId, setPortLocId] = useState<number | ''>('');
  const [portDeviceId, setPortDeviceId] = useState<number | ''>('');
  const [portConnType, setPortConnType] = useState('Access');
  const [portStatus, setPortStatus] = useState('free');
  const [portDesc, setPortDesc] = useState('');

  // Quick Inline Creation inside Port modal
  const [newLocName, setNewLocName] = useState('');
  const [newDevName, setNewDevName] = useState('');

  const activeSwitch = switches.find((s) => s.id === activeSwitchId) || switches[0] || null;

  const openCreateSwitchModal = () => {
    setEditingSwitch(null);
    setSwName('');
    setSwHostname('');
    setSwIp('');
    setSwMac('');
    setSwPortCount(24);
    setSwRackId('');
    setSwManufacturer('');
    setSwModel('');
    setSwError('');
    setSwitchModalOpen(true);
  };

  const openEditSwitchModal = (sw: Switch) => {
    setEditingSwitch(sw);
    setSwName(sw.name);
    setSwHostname(sw.hostname);
    setSwIp(sw.ip_address || '');
    setSwMac(sw.mac_address || '');
    setSwPortCount(sw.port_count);
    setSwRackId(sw.rack_id || '');
    setSwManufacturer(sw.manufacturer || '');
    setSwModel(sw.model || '');
    setSwError('');
    setSwitchModalOpen(true);
  };

  const handleSaveSwitch = async (e: React.FormEvent) => {
    e.preventDefault();
    setSwError('');

    const body = {
      name: swName,
      hostname: swHostname,
      ip_address: swIp || null,
      mac_address: swMac || null,
      port_count: swPortCount,
      rack_id: swRackId !== '' ? Number(swRackId) : null,
      manufacturer: swManufacturer || null,
      model: swModel || null,
    };

    try {
      if (editingSwitch) {
        await fetchApi(`/switches/${editingSwitch.id}`, { method: 'PUT', body: JSON.stringify(body) });
      } else {
        const created: Switch = await fetchApi('/switches', { method: 'POST', body: JSON.stringify(body) });
        setActiveSwitchId(created.id);
      }
      setSwitchModalOpen(false);
      onRefresh();
    } catch (err: any) {
      setSwError(err.message || 'Erro ao salvar switch');
    }
  };

  const handleDeleteSwitch = async (sw: Switch) => {
    if (!confirm(`Tem certeza que deseja excluir o switch "${sw.name}"? Todas as portas serão removidas.`)) return;

    try {
      await fetchApi(`/switches/${sw.id}`, { method: 'DELETE' });
      setActiveSwitchId(null);
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Erro ao excluir switch');
    }
  };

  const openPortModal = (port: SwitchPort) => {
    setSelectedPort(port);
    setPortVlanId(port.vlan_id || '');
    setPortLocId(port.destination_location_id || '');
    setPortDeviceId(port.connected_device_id || '');
    setPortConnType(port.connection_type || 'Access');
    setPortStatus(port.status || 'free');
    setPortDesc(port.description || '');
    setNewLocName('');
    setNewDevName('');
    setPortModalOpen(true);
  };

  const handleSavePort = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeSwitch || !selectedPort) return;

    const body = {
      vlan_id: portVlanId !== '' ? Number(portVlanId) : null,
      destination_location_id: portLocId !== '' ? Number(portLocId) : null,
      connected_device_id: portDeviceId !== '' ? Number(portDeviceId) : null,
      connection_type: portConnType,
      status: portStatus,
      description: portDesc,
      new_location_name: newLocName.trim() || undefined,
      new_device_name: newDevName.trim() || undefined,
    };

    try {
      await fetchApi(`/switches/${activeSwitch.id}/ports/${selectedPort.port_number}`, {
        method: 'PUT',
        body: JSON.stringify(body),
      });
      setPortModalOpen(false);
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Erro ao atualizar porta');
    }
  };

  const getPortBadgeColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'bg-emerald-500 text-white border-emerald-600 hover:bg-emerald-600'; // Verde
      case 'uplink':
        return 'bg-amber-500 text-white border-amber-600 hover:bg-amber-600'; // Amarelo
      case 'network_device':
        return 'bg-blue-500 text-white border-blue-600 hover:bg-blue-600'; // Azul
      case 'issue':
        return 'bg-rose-500 text-white border-rose-600 hover:bg-rose-600'; // Vermelho
      default:
        return 'bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300 border-slate-300 dark:border-slate-600 hover:bg-slate-300'; // Cinza (Livre)
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-white">Gerenciamento de Switches</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Selecione um switch para visualizar e gerenciar visualmente cada porta de rede.
          </p>
        </div>
        <button
          onClick={openCreateSwitchModal}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold flex items-center space-x-2 transition shadow-md"
        >
          <Plus className="w-4 h-4" />
          <span>Cadastrar Switch</span>
        </button>
      </div>

      {/* Switch Tabs Horizontal Scroll */}
      <div className="flex space-x-2 overflow-x-auto pb-2 border-b border-slate-200 dark:border-slate-700">
        {switches.map((sw) => {
          const isActive = activeSwitch?.id === sw.id;
          return (
            <button
              key={sw.id}
              onClick={() => setActiveSwitchId(sw.id)}
              className={`px-4 py-2.5 rounded-xl text-sm font-semibold whitespace-nowrap transition flex items-center space-x-2 ${
                isActive
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700'
              }`}
            >
              <HardDrive className="w-4 h-4" />
              <span>{sw.name}</span>
              <span className={`text-xs px-2 py-0.5 rounded-full ${isActive ? 'bg-blue-700 text-white' : 'bg-slate-100 dark:bg-slate-700 text-slate-500'}`}>
                {sw.port_count}P
              </span>
            </button>
          );
        })}
      </div>

      {/* Switch Content View */}
      {activeSwitch ? (
        <div className="space-y-6">
          {/* Switch Overview Card */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-blue-100 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 rounded-2xl">
                <HardDrive className="w-8 h-8" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h2 className="text-2xl font-bold text-slate-800 dark:text-white">{activeSwitch.name}</h2>
                  <span className="text-xs bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 font-mono px-2 py-0.5 rounded-md">
                    {activeSwitch.hostname}
                  </span>
                </div>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500 dark:text-slate-400 mt-1">
                  <span>
                    <strong>IP:</strong> {activeSwitch.ip_address || 'Não configurado'}
                  </span>
                  <span>
                    <strong>Rack:</strong> {activeSwitch.rack_name || 'Sem Rack'}
                  </span>
                  <span>
                    <strong>Modelo:</strong> {activeSwitch.manufacturer || ''} {activeSwitch.model || ''}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => openEditSwitchModal(activeSwitch)}
                className="px-3 py-2 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition"
              >
                <Edit2 className="w-3.5 h-3.5" />
                <span>Editar Switch</span>
              </button>
              <button
                onClick={() => handleDeleteSwitch(activeSwitch)}
                className="px-3 py-2 bg-rose-50 dark:bg-rose-950/40 hover:bg-rose-100 dark:hover:bg-rose-900/60 text-rose-600 dark:text-rose-400 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Excluir</span>
              </button>
            </div>
          </div>

          {/* Port Color Legend */}
          <div className="bg-slate-100 dark:bg-slate-800/60 rounded-xl p-3 border border-slate-200 dark:border-slate-700 flex flex-wrap items-center gap-4 text-xs font-medium">
            <span className="text-slate-500 dark:text-slate-400 mr-2">Legenda das Portas:</span>
            <div className="flex items-center space-x-1.5">
              <div className="w-3 h-3 bg-emerald-500 rounded-sm" />
              <span>Conectada (Verde)</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <div className="w-3 h-3 bg-slate-400 dark:bg-slate-600 rounded-sm" />
              <span>Livre (Cinza)</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <div className="w-3 h-3 bg-amber-500 rounded-sm" />
              <span>Uplink (Amarelo)</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <div className="w-3 h-3 bg-blue-500 rounded-sm" />
              <span>Equipamento de Rede (Azul)</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <div className="w-3 h-3 bg-rose-500 rounded-sm" />
              <span>Problema/Alerta (Vermelho)</span>
            </div>
          </div>

          {/* Interactive Switch Port Matrix */}
          <div className="bg-slate-900 text-white rounded-2xl p-6 border border-slate-800 shadow-2xl space-y-4">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <span className="text-xs font-mono tracking-wider text-slate-400 uppercase">
                Matriz Interativa de Portas ({activeSwitch.port_count} Portas)
              </span>
              <span className="text-xs text-slate-400">Passe o mouse para info rápida | Clique para editar</span>
            </div>

            {/* Ports Grid */}
            <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-12 gap-2.5">
              {activeSwitch.ports.map((port) => {
                const formattedNum = String(port.port_number).padStart(2, '0');
                return (
                  <div key={port.id} className="relative group">
                    <button
                      onClick={() => openPortModal(port)}
                      className={`w-full h-11 rounded-lg border flex flex-col items-center justify-center font-mono font-bold text-xs transition transform group-hover:scale-105 shadow-sm ${getPortBadgeColor(
                        port.status
                      )}`}
                    >
                      <span>{formattedNum}</span>
                      {port.vlan_number && <span className="text-[9px] opacity-80 font-normal">V{port.vlan_number}</span>}
                    </button>

                    {/* Hover Quick Tooltip */}
                    <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 hidden group-hover:block w-48 bg-slate-800 text-white text-[11px] p-2.5 rounded-xl shadow-2xl border border-slate-700 z-50 pointer-events-none">
                      <div className="font-bold text-blue-400 border-b border-slate-700 pb-1 mb-1">
                        Porta {formattedNum} ({port.status})
                      </div>
                      <div><strong>VLAN:</strong> {port.vlan_name ? `VLAN ${port.vlan_number} (${port.vlan_name})` : 'Nenhum'}</div>
                      <div><strong>Local:</strong> {port.destination_location_name || 'Nenhum'}</div>
                      <div><strong>Equipamento:</strong> {port.connected_device_name || 'Nenhum'}</div>
                      {port.connected_device_ip && <div><strong>IP:</strong> {port.connected_device_ip}</div>}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      ) : (
        <div className="p-12 text-center bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700">
          <p className="text-slate-500">Nenhum switch cadastrado. Clique em "Cadastrar Switch" para começar.</p>
        </div>
      )}

      {/* Switch Create/Edit Modal */}
      {switchModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-2xl max-w-lg w-full p-6 space-y-4">
            <h2 className="text-xl font-bold text-slate-800 dark:text-white">
              {editingSwitch ? 'Editar Switch' : 'Novo Switch'}
            </h2>

            {swError && (
              <div className="p-3 bg-rose-50 dark:bg-rose-950/40 text-rose-600 rounded-xl text-xs">{swError}</div>
            )}

            <form onSubmit={handleSaveSwitch} className="space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                    Nome do Switch *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Ex: Switch 01"
                    value={swName}
                    onChange={(e) => setSwName(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                    Hostname *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Ex: HOD-SW01"
                    value={swHostname}
                    onChange={(e) => setSwHostname(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                    Endereço IP
                  </label>
                  <input
                    type="text"
                    placeholder="Ex: 10.10.10.10"
                    value={swIp}
                    onChange={(e) => setSwIp(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                    Quantidade de Portas *
                  </label>
                  <select
                    value={swPortCount}
                    onChange={(e) => setSwPortCount(Number(e.target.value))}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                  >
                    <option value={8}>8 Portas</option>
                    <option value={12}>12 Portas</option>
                    <option value={24}>24 Portas</option>
                    <option value={48}>48 Portas</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                  Rack onde está instalado
                </label>
                <select
                  value={swRackId}
                  onChange={(e) => setSwRackId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                >
                  <option value="">Sem Rack vinculado</option>
                  {racks.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name} ({r.location_description})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setSwitchModalOpen(false)}
                  className="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-xl"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold"
                >
                  Salvar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Port Modal Detail / Quick Inline Edit */}
      {portModalOpen && selectedPort && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-2xl max-w-md w-full p-6 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 dark:border-slate-700 pb-3">
              <h2 className="text-lg font-bold text-slate-800 dark:text-white flex items-center space-x-2">
                <span>Configurar Porta {String(selectedPort.port_number).padStart(2, '0')}</span>
                <span className="text-xs bg-blue-100 dark:bg-blue-900/50 text-blue-600 px-2 py-0.5 rounded-md">
                  {activeSwitch?.name}
                </span>
              </h2>
            </div>

            <form onSubmit={handleSavePort} className="space-y-3 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                  VLAN
                </label>
                <select
                  value={portVlanId}
                  onChange={(e) => setPortVlanId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                >
                  <option value="">Nenhuma VLAN</option>
                  {vlans.map((v) => (
                    <option key={v.id} value={v.id}>
                      VLAN {v.vlan_number} - {v.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                  Local de Destino
                </label>
                <select
                  value={portLocId}
                  onChange={(e) => setPortLocId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                >
                  <option value="">Selecione um local...</option>
                  {locations.map((l) => (
                    <option key={l.id} value={l.id}>
                      {l.name} ({l.sector || 'Geral'})
                    </option>
                  ))}
                </select>
                <input
                  type="text"
                  placeholder="Ou crie um novo local rapidamente..."
                  value={newLocName}
                  onChange={(e) => {
                    setNewLocName(e.target.value);
                    if (e.target.value) setPortLocId('');
                  }}
                  className="mt-1 w-full px-3 py-1.5 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                  Equipamento Conectado
                </label>
                <select
                  value={portDeviceId}
                  onChange={(e) => setPortDeviceId(e.target.value ? Number(e.target.value) : '')}
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                >
                  <option value="">Nenhum equipamento conectado</option>
                  {devices.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.ip_address || 'Sem IP'})
                    </option>
                  ))}
                </select>
                <input
                  type="text"
                  placeholder="Ou crie um novo equipamento rapidamente..."
                  value={newDevName}
                  onChange={(e) => {
                    setNewDevName(e.target.value);
                    if (e.target.value) setPortDeviceId('');
                  }}
                  className="mt-1 w-full px-3 py-1.5 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                    Tipo de Conexão
                  </label>
                  <select
                    value={portConnType}
                    onChange={(e) => setPortConnType(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                  >
                    <option value="Access">Access</option>
                    <option value="Trunk">Trunk</option>
                    <option value="Uplink">Uplink</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                    Estado Visual
                  </label>
                  <select
                    value={portStatus}
                    onChange={(e) => setPortStatus(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                  >
                    <option value="connected">Verde (Conectada)</option>
                    <option value="free">Cinza (Livre)</option>
                    <option value="uplink">Amarelo (Uplink)</option>
                    <option value="network_device">Azul (Equip. Rede)</option>
                    <option value="issue">Vermelho (Problema)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                  Descrição do Ponto
                </label>
                <input
                  type="text"
                  placeholder="Ex: Ponto de rede do computador principal"
                  value={portDesc}
                  onChange={(e) => setPortDesc(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setPortModalOpen(false)}
                  className="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-xl"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold"
                >
                  Salvar Porta
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
