import React, { useState } from 'react';
import { MapPin, Plus, Edit2, Trash2, Cpu } from 'lucide-react';
import type { Location, Device, Switch } from '../types';
import { fetchApi } from '../services/api';

interface LocationsViewProps {
  locations: Location[];
  devices: Device[];
  switches: Switch[];
  onRefresh: () => void;
}

export const LocationsView: React.FC<LocationsViewProps> = ({ locations, devices, onRefresh }) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [editingLoc, setEditingLoc] = useState<Location | null>(null);
  const [name, setName] = useState('');
  const [sector, setSector] = useState('');
  const [floor, setFloor] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');

  const openCreateModal = () => {
    setEditingLoc(null);
    setName('');
    setSector('');
    setFloor('');
    setDescription('');
    setError('');
    setModalOpen(true);
  };

  const openEditModal = (loc: Location) => {
    setEditingLoc(loc);
    setName(loc.name);
    setSector(loc.sector || '');
    setFloor(loc.floor || '');
    setDescription(loc.description || '');
    setError('');
    setModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const body = { name, sector, floor, description };

    try {
      if (editingLoc) {
        await fetchApi(`/locations/${editingLoc.id}`, { method: 'PUT', body: JSON.stringify(body) });
      } else {
        await fetchApi('/locations', { method: 'POST', body: JSON.stringify(body) });
      }
      setModalOpen(false);
      onRefresh();
    } catch (err: any) {
      setError(err.message || 'Erro ao salvar local');
    }
  };

  const handleDelete = async (loc: Location) => {
    const locDevices = devices.filter((d) => d.location_id === loc.id);
    if (locDevices.length > 0) {
      alert(`Não é possível excluir o local "${loc.name}" pois ele possui ${locDevices.length} equipamento(s) cadastrado(s). Realoque ou remova os equipamentos primeiro.`);
      return;
    }

    if (!confirm(`Deseja realmente excluir o local "${loc.name}"?`)) return;

    try {
      await fetchApi(`/locations/${loc.id}`, { method: 'DELETE' });
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Erro ao excluir local');
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-white">Locais da Empresa</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Mapeamento de consultórios, salas, laboratórios e setores físicos.
          </p>
        </div>
        <button
          onClick={openCreateModal}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold flex items-center space-x-2 transition shadow-md"
        >
          <Plus className="w-4 h-4" />
          <span>Cadastrar Local</span>
        </button>
      </div>

      {/* Locations Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {locations.map((loc) => {
          const locDevices = devices.filter((d) => d.location_id === loc.id);

          return (
            <div
              key={loc.id}
              className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-md transition overflow-hidden flex flex-col justify-between"
            >
              <div className="p-5 space-y-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2.5 bg-teal-100 dark:bg-teal-950/60 text-teal-600 dark:text-teal-400 rounded-xl">
                      <MapPin className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="font-bold text-lg text-slate-800 dark:text-white">{loc.name}</h3>
                      <div className="text-xs text-slate-400">
                        {loc.sector || 'Sem setor'} {loc.floor ? `• ${loc.floor}` : ''}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-1">
                    <button
                      onClick={() => openEditModal(loc)}
                      className="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 rounded-lg transition"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(loc)}
                      className="p-1.5 hover:bg-rose-100 dark:hover:bg-rose-950/50 text-rose-600 rounded-lg transition"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {loc.description && (
                  <p className="text-xs text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-slate-700/40 p-2.5 rounded-lg border border-slate-100 dark:border-slate-700">
                    {loc.description}
                  </p>
                )}

                {/* Attached Devices */}
                <div>
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex justify-between">
                    <span>Equipamentos Presentes</span>
                    <span className="bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded-full text-[10px]">
                      {locDevices.length}
                    </span>
                  </h4>

                  {locDevices.length === 0 ? (
                    <div className="text-xs text-slate-400 italic">Nenhum equipamento vinculado a este local.</div>
                  ) : (
                    <div className="space-y-1.5 max-h-40 overflow-y-auto">
                      {locDevices.map((d) => (
                        <div
                          key={d.id}
                          className="p-2 bg-slate-50 dark:bg-slate-700/50 rounded-lg flex items-center justify-between text-xs"
                        >
                          <div className="flex items-center space-x-2">
                            <Cpu className="w-3.5 h-3.5 text-purple-500" />
                            <span className="font-semibold text-slate-700 dark:text-slate-200">{d.name}</span>
                          </div>
                          <span className="text-[10px] text-slate-400 font-mono">{d.ip_address || 'Sem IP'}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal Form */}
      {modalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-2xl max-w-md w-full p-6 space-y-4">
            <h2 className="text-xl font-bold text-slate-800 dark:text-white">
              {editingLoc ? 'Editar Local' : 'Novo Local'}
            </h2>

            {error && (
              <div className="p-3 bg-rose-50 dark:bg-rose-950/40 text-rose-600 rounded-xl text-xs">{error}</div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                  Nome do Local *
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ex: Consultório 05 / Recepção"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                    Setor
                  </label>
                  <input
                    type="text"
                    placeholder="Ex: Ambulatório"
                    value={sector}
                    onChange={(e) => setSector(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                    Andar
                  </label>
                  <input
                    type="text"
                    placeholder="Ex: 1º Andar"
                    value={floor}
                    onChange={(e) => setFloor(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                  Descrição
                </label>
                <textarea
                  placeholder="Descrição das atividades do local..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                />
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
