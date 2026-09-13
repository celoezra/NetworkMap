import React, { useState } from 'react';
import { Plus, Edit2, Trash2, Search, MapPin, HardDrive, Filter } from 'lucide-react';
import type { Device, Location, VLAN, Switch } from '../types';
import { fetchApi } from '../services/api';

interface DevicesViewProps {
  devices: Device[];
  locations: Location[];
  vlans: VLAN[];
  switches: Switch[];
  onRefresh: () => void;
}

export const DevicesView: React.FC<DevicesViewProps> = ({ devices, locations, vlans, onRefresh }) => {
  const [filterQuery, setFilterQuery] = useState('');
  const [filterType, setFilterType] = useState('all');

  const [modalOpen, setModalOpen] = useState(false);
  const [editingDev, setEditingDev] = useState<Device | null>(null);

  const [name, setName] = useState('');
  const [hostname, setHostname] = useState('');
  const [ipAddress, setIpAddress] = useState('');
  const [macAddress, setMacAddress] = useState('');
  const [deviceType, setDeviceType] = useState('computador');
  const [locationId, setLocationId] = useState<number | ''>('');
  const [vlanId, setVlanId] = useState<number | ''>('');
  const [assetTag, setAssetTag] = useState('');
  const [serialNumber, setSerialNumber] = useState('');
  const [error, setError] = useState('');

  const openCreateModal = () => {
    setEditingDev(null);
    setName('');
    setHostname('');
    setIpAddress('');
    setMacAddress('');
    setDeviceType('computador');
    setLocationId('');
    setVlanId('');
    setAssetTag('');
    setSerialNumber('');
    setError('');
    setModalOpen(true);
  };

  const openEditModal = (dev: Device) => {
    setEditingDev(dev);
    setName(dev.name);
    setHostname(dev.hostname || '');
    setIpAddress(dev.ip_address || '');
    setMacAddress(dev.mac_address || '');
    setDeviceType(dev.device_type);
    setLocationId(dev.location_id || '');
    setVlanId(dev.vlan_id || '');
    setAssetTag(dev.asset_tag || '');
    setSerialNumber(dev.serial_number || '');
    setError('');
    setModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const body = {
      name,
      hostname: hostname || null,
      ip_address: ipAddress || null,
      mac_address: macAddress || null,
      device_type: deviceType,
      location_id: locationId !== '' ? Number(locationId) : null,
      vlan_id: vlanId !== '' ? Number(vlanId) : null,
      asset_tag: assetTag || null,
      serial_number: serialNumber || null,
    };

    try {
      if (editingDev) {
        await fetchApi(`/devices/${editingDev.id}`, { method: 'PUT', body: JSON.stringify(body) });
      } else {
        await fetchApi('/devices', { method: 'POST', body: JSON.stringify(body) });
      }
      setModalOpen(false);
      onRefresh();
    } catch (err: any) {
      setError(err.message || 'Erro ao salvar equipamento');
    }
  };

  const handleDelete = async (dev: Device) => {
    if (!confirm(`Tem certeza que deseja excluir o equipamento "${dev.name}"?`)) return;

    try {
      await fetchApi(`/devices/${dev.id}`, { method: 'DELETE' });
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Erro ao excluir equipamento');
    }
  };

  const filteredDevices = devices.filter((d) => {
    const matchesQuery =
      d.name.toLowerCase().includes(filterQuery.toLowerCase()) ||
      (d.hostname && d.hostname.toLowerCase().includes(filterQuery.toLowerCase())) ||
      (d.ip_address && d.ip_address.includes(filterQuery)) ||
      (d.asset_tag && d.asset_tag.toLowerCase().includes(filterQuery.toLowerCase()));

    const matchesType = filterType === 'all' || d.device_type === filterType;

    return matchesQuery && matchesType;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-white">Inventário de Equipamentos</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Gerencie computadores, impressoras, access points, servidores e outros ativos de rede.
          </p>
        </div>
        <button
          onClick={openCreateModal}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold flex items-center space-x-2 transition shadow-md"
        >
          <Plus className="w-4 h-4" />
          <span>Cadastrar Equipamento</span>
        </button>
      </div>

      {/* Filters Bar */}
      <div className="bg-white dark:bg-slate-800 p-4 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col md:flex-row gap-3 justify-between items-center">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Filtrar por nome, IP, hostname ou patrimônio..."
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-slate-50 dark:bg-slate-700/60 border border-slate-200 dark:border-slate-600 rounded-xl text-xs"
          />
        </div>

        <div className="flex items-center space-x-2 w-full md:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-xs"
          >
            <option value="all">Todos os Tipos</option>
            <option value="computador">Computador</option>
            <option value="notebook">Notebook</option>
            <option value="impressora">Impressora</option>
            <option value="access_point">Access Point</option>
            <option value="servidor">Servidor</option>
            <option value="camera">Câmera</option>
            <option value="telefone_ip">Telefone IP</option>
            <option value="roteador">Roteador</option>
            <option value="switch">Switch</option>
            <option value="firewall">Firewall</option>
          </select>
        </div>
      </div>

      {/* Devices Table */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-700/50 border-b border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 uppercase font-semibold">
                <th className="p-4">Equipamento</th>
                <th className="p-4">Tipo</th>
                <th className="p-4">Endereço IP</th>
                <th className="p-4">Local</th>
                <th className="p-4">Conectado Em</th>
                <th className="p-4">VLAN</th>
                <th className="p-4 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700/60">
              {filteredDevices.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-400">
                    Nenhum equipamento encontrado.
                  </td>
                </tr>
              ) : (
                filteredDevices.map((dev) => (
                  <tr key={dev.id} className="hover:bg-slate-50/80 dark:hover:bg-slate-700/30 transition">
                    <td className="p-4">
                      <div className="font-bold text-slate-800 dark:text-white">{dev.name}</div>
                      <div className="text-[10px] text-slate-400 font-mono">{dev.hostname || 'Sem hostname'}</div>
                    </td>
                    <td className="p-4">
                      <span className="capitalize px-2.5 py-1 bg-purple-50 dark:bg-purple-950/40 text-purple-600 dark:text-purple-400 rounded-lg font-semibold text-[10px]">
                        {dev.device_type.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="p-4 font-mono font-semibold text-slate-700 dark:text-slate-300">
                      {dev.ip_address || '-'}
                    </td>
                    <td className="p-4">
                      <div className="flex items-center space-x-1 text-slate-600 dark:text-slate-300">
                        <MapPin className="w-3.5 h-3.5 text-teal-500" />
                        <span>{dev.location_name || 'Não informado'}</span>
                      </div>
                    </td>
                    <td className="p-4">
                      {dev.connected_switch_name ? (
                        <div className="flex items-center space-x-1.5 text-blue-600 dark:text-blue-400 font-semibold">
                          <HardDrive className="w-3.5 h-3.5" />
                          <span>
                            {dev.connected_switch_name} (P{dev.connected_port_number})
                          </span>
                        </div>
                      ) : (
                        <span className="text-slate-400 italic">Desconectado</span>
                      )}
                    </td>
                    <td className="p-4">
                      {dev.vlan_name ? (
                        <span className="px-2 py-0.5 bg-sky-50 dark:bg-sky-950/40 text-sky-600 dark:text-sky-400 rounded font-semibold text-[10px]">
                          VLAN {dev.vlan_name}
                        </span>
                      ) : (
                        <span className="text-slate-400">-</span>
                      )}
                    </td>
                    <td className="p-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => openEditModal(dev)}
                          className="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 rounded-lg transition"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(dev)}
                          className="p-1.5 hover:bg-rose-100 dark:hover:bg-rose-950/50 text-rose-600 rounded-lg transition"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Form */}
      {modalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-2xl max-w-lg w-full p-6 space-y-4">
            <h2 className="text-xl font-bold text-slate-800 dark:text-white">
              {editingDev ? 'Editar Equipamento' : 'Novo Equipamento'}
            </h2>

            {error && (
              <div className="p-3 bg-rose-50 dark:bg-rose-950/40 text-rose-600 rounded-xl text-xs">{error}</div>
            )}

            <form onSubmit={handleSubmit} className="space-y-3 text-sm">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                    Nome / Identificação *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Ex: CONSULT05-PC01"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                    Hostname
                  </label>
                  <input
                    type="text"
                    placeholder="Ex: CONSULT05-PC01"
                    value={hostname}
                    onChange={(e) => setHostname(e.target.value)}
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
                    placeholder="Ex: 10.10.20.35"
                    value={ipAddress}
                    onChange={(e) => setIpAddress(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                    Endereço MAC
                  </label>
                  <input
                    type="text"
                    placeholder="Ex: 00:11:22:33:44:55"
                    value={macAddress}
                    onChange={(e) => setMacAddress(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                    Tipo de Equipamento
                  </label>
                  <select
                    value={deviceType}
                    onChange={(e) => setDeviceType(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                  >
                    <option value="computador">Computador</option>
                    <option value="notebook">Notebook</option>
                    <option value="impressora">Impressora</option>
                    <option value="access_point">Access Point</option>
                    <option value="servidor">Servidor</option>
                    <option value="camera">Câmera</option>
                    <option value="telefone_ip">Telefone IP</option>
                    <option value="painel">Painel</option>
                    <option value="roteador">Roteador</option>
                    <option value="switch">Switch</option>
                    <option value="firewall">Firewall</option>
                    <option value="equipamento_medico">Equipamento Médico</option>
                    <option value="equipamento_generico">Genérico</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                    Local de Instalação
                  </label>
                  <select
                    value={locationId}
                    onChange={(e) => setLocationId(e.target.value ? Number(e.target.value) : '')}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                  >
                    <option value="">Sem local vinculado</option>
                    {locations.map((l) => (
                      <option key={l.id} value={l.id}>
                        {l.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">VLAN</label>
                <select
                  value={vlanId}
                  onChange={(e) => setVlanId(e.target.value ? Number(e.target.value) : '')}
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

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
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
    </div>
  );
};
