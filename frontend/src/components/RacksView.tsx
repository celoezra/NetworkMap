import React, { useState } from 'react';
import { Server, Plus, Edit2, Trash2, HardDrive, MapPin, FileText } from 'lucide-react';
import type { Rack, Switch } from '../types';
import { fetchApi } from '../services/api';

interface RacksViewProps {
  racks: Rack[];
  switches: Switch[];
  onRefresh: () => void;
  onSelectSwitch: (switchId: number) => void;
}

export const RacksView: React.FC<RacksViewProps> = ({ racks, switches, onRefresh, onSelectSwitch }) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [editingRack, setEditingRack] = useState<Rack | null>(null);
  const [name, setName] = useState('');
  const [locationDescription, setLocationDescription] = useState('');
  const [description, setDescription] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');

  const openCreateModal = () => {
    setEditingRack(null);
    setName('');
    setLocationDescription('');
    setDescription('');
    setNotes('');
    setError('');
    setModalOpen(true);
  };

  const openEditModal = (rack: Rack) => {
    setEditingRack(rack);
    setName(rack.name);
    setLocationDescription(rack.location_description);
    setDescription(rack.description || '');
    setNotes(rack.notes || '');
    setError('');
    setModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      if (editingRack) {
        await fetchApi(`/racks/${editingRack.id}`, {
          method: 'PUT',
          body: JSON.stringify({ name, location_description: locationDescription, description, notes }),
        });
      } else {
        await fetchApi('/racks', {
          method: 'POST',
          body: JSON.stringify({ name, location_description: locationDescription, description, notes }),
        });
      }
      setModalOpen(false);
      onRefresh();
    } catch (err: any) {
      setError(err.message || 'Erro ao salvar rack');
    }
  };

  const handleDelete = async (rack: Rack) => {
    const rackSwitches = switches.filter((s) => s.rack_id === rack.id);
    if (rackSwitches.length > 0) {
      alert(`Não é possível excluir o rack "${rack.name}" pois ele possui ${rackSwitches.length} switch(es) instalado(s). Remova ou realoque os switches primeiro.`);
      return;
    }

    if (!confirm(`Deseja realmente excluir o rack "${rack.name}"?`)) return;

    try {
      await fetchApi(`/racks/${rack.id}`, { method: 'DELETE' });
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Erro ao excluir rack');
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-white">Gerenciamento de Racks</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Cadastre os Racks físicos da empresa e visualize os switches instalados em cada um.
          </p>
        </div>
        <button
          onClick={openCreateModal}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold flex items-center space-x-2 transition shadow-md"
        >
          <Plus className="w-4 h-4" />
          <span>Cadastrar Rack</span>
        </button>
      </div>

      {/* Racks Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {racks.map((rack) => {
          const installedSwitches = switches.filter((s) => s.rack_id === rack.id);

          return (
            <div
              key={rack.id}
              className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-md transition overflow-hidden flex flex-col justify-between"
            >
              <div>
                {/* Rack Header */}
                <div className="p-5 border-b border-slate-100 dark:border-slate-700 flex items-start justify-between bg-slate-50/50 dark:bg-slate-800/80">
                  <div className="flex items-center space-x-3">
                    <div className="p-2.5 bg-indigo-100 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 rounded-xl">
                      <Server className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="font-bold text-lg text-slate-800 dark:text-white">{rack.name}</h3>
                      <div className="flex items-center text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                        <MapPin className="w-3.5 h-3.5 mr-1 text-slate-400" />
                        <span>{rack.location_description}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-1">
                    <button
                      onClick={() => openEditModal(rack)}
                      className="p-1.5 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-500 rounded-lg transition"
                      title="Editar"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(rack)}
                      className="p-1.5 hover:bg-rose-100 dark:hover:bg-rose-950/50 text-rose-600 rounded-lg transition"
                      title="Excluir"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Rack Body */}
                <div className="p-5 space-y-4">
                  {rack.description && (
                    <p className="text-xs text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-slate-700/40 p-2.5 rounded-lg border border-slate-100 dark:border-slate-700">
                      {rack.description}
                    </p>
                  )}

                  {/* Installed Switches Section */}
                  <div>
                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
                      <span>Switches Instalados</span>
                      <span className="bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 px-2 py-0.5 rounded-full text-[10px]">
                        {installedSwitches.length}
                      </span>
                    </h4>

                    {installedSwitches.length === 0 ? (
                      <div className="text-xs text-slate-400 dark:text-slate-500 italic py-2">
                        Nenhum switch instalado neste rack.
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {installedSwitches.map((sw) => (
                          <div
                            key={sw.id}
                            onClick={() => onSelectSwitch(sw.id)}
                            className="flex items-center justify-between p-2.5 rounded-xl border border-slate-200 dark:border-slate-700 hover:border-blue-500 dark:hover:border-blue-400 hover:bg-blue-50/30 dark:hover:bg-blue-900/20 cursor-pointer transition"
                          >
                            <div className="flex items-center space-x-2.5">
                              <HardDrive className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                              <div>
                                <div className="text-xs font-bold text-slate-800 dark:text-white">{sw.name}</div>
                                <div className="text-[10px] text-slate-400">{sw.hostname} ({sw.port_count} portas)</div>
                              </div>
                            </div>
                            <span className="text-[10px] font-semibold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950 px-2 py-1 rounded-md">
                              {sw.ip_address || 'Sem IP'}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Footer */}
              {rack.notes && (
                <div className="px-5 py-3 border-t border-slate-100 dark:border-slate-700/60 bg-slate-50/50 dark:bg-slate-800/40 text-[11px] text-slate-400 flex items-center">
                  <FileText className="w-3.5 h-3.5 mr-1.5 flex-shrink-0" />
                  <span className="truncate">{rack.notes}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Modal Form */}
      {modalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-2xl max-w-md w-full p-6 space-y-4">
            <h2 className="text-xl font-bold text-slate-800 dark:text-white">
              {editingRack ? 'Editar Rack' : 'Novo Rack'}
            </h2>

            {error && (
              <div className="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-600 dark:text-rose-400 rounded-xl text-xs">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                  Nome do Rack *
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ex: Rack 3º Andar"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                  Localização *
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ex: Sala de TI / CPD"
                  value={locationDescription}
                  onChange={(e) => setLocationDescription(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                  Descrição
                </label>
                <textarea
                  placeholder="Ex: Rack principal do terceiro andar."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                  Observações
                </label>
                <textarea
                  placeholder="Observações técnicas..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-800 dark:text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 rounded-xl hover:bg-slate-200 transition"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold transition"
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
