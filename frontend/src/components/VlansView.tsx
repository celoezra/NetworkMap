import React, { useState } from 'react';
import { Plus, Edit2, Trash2 } from 'lucide-react';
import type { VLAN } from '../types';
import { fetchApi } from '../services/api';

interface VlansViewProps {
  vlans: VLAN[];
  onRefresh: () => void;
}

export const VlansView: React.FC<VlansViewProps> = ({ vlans, onRefresh }) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [editingVlan, setEditingVlan] = useState<VLAN | null>(null);

  const [vlanNumber, setVlanNumber] = useState<number | ''>('');
  const [name, setName] = useState('');
  const [subnet, setSubnet] = useState('');
  const [gateway, setGateway] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState('');

  const openCreateModal = () => {
    setEditingVlan(null);
    setVlanNumber('');
    setName('');
    setSubnet('');
    setGateway('');
    setDescription('');
    setError('');
    setModalOpen(true);
  };

  const openEditModal = (vlan: VLAN) => {
    setEditingVlan(vlan);
    setVlanNumber(vlan.vlan_number);
    setName(vlan.name);
    setSubnet(vlan.subnet || '');
    setGateway(vlan.gateway || '');
    setDescription(vlan.description || '');
    setError('');
    setModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const body = {
      vlan_number: Number(vlanNumber),
      name,
      subnet: subnet || null,
      gateway: gateway || null,
      description: description || null,
    };

    try {
      if (editingVlan) {
        await fetchApi(`/vlans/${editingVlan.id}`, { method: 'PUT', body: JSON.stringify(body) });
      } else {
        await fetchApi('/vlans', { method: 'POST', body: JSON.stringify(body) });
      }
      setModalOpen(false);
      onRefresh();
    } catch (err: any) {
      setError(err.message || 'Erro ao salvar VLAN');
    }
  };

  const handleDelete = async (vlan: VLAN) => {
    if (!confirm(`Deseja realmente excluir a VLAN ${vlan.vlan_number} (${vlan.name})?`)) return;

    try {
      await fetchApi(`/vlans/${vlan.id}`, { method: 'DELETE' });
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Erro ao excluir VLAN');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-white">Cadastro de VLANs</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Gerencie as Redes Virtuais (VLANs), escopo de subredes e gateways corporativos.
          </p>
        </div>
        <button
          onClick={openCreateModal}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold flex items-center space-x-2 transition shadow-md"
        >
          <Plus className="w-4 h-4" />
          <span>Cadastrar VLAN</span>
        </button>
      </div>

      {/* VLAN Table */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-700/50 border-b border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 uppercase font-semibold">
                <th className="p-4">ID VLAN</th>
                <th className="p-4">Nome</th>
                <th className="p-4">Subnet (CIDR)</th>
                <th className="p-4">Gateway</th>
                <th className="p-4">Descrição</th>
                <th className="p-4 text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700/60">
              {vlans.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-400">
                    Nenhuma VLAN cadastrada.
                  </td>
                </tr>
              ) : (
                vlans.map((v) => (
                  <tr key={v.id} className="hover:bg-slate-50/80 dark:hover:bg-slate-700/30 transition">
                    <td className="p-4 font-mono font-bold text-pink-600 dark:text-pink-400 text-sm">
                      VLAN {v.vlan_number}
                    </td>
                    <td className="p-4 font-bold text-slate-800 dark:text-white">{v.name}</td>
                    <td className="p-4 font-mono text-slate-600 dark:text-slate-300">{v.subnet || '-'}</td>
                    <td className="p-4 font-mono text-slate-600 dark:text-slate-300">{v.gateway || '-'}</td>
                    <td className="p-4 text-slate-500 dark:text-slate-400">{v.description || '-'}</td>
                    <td className="p-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => openEditModal(v)}
                          className="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 rounded-lg transition"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(v)}
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
          <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-2xl max-w-md w-full p-6 space-y-4">
            <h2 className="text-xl font-bold text-slate-800 dark:text-white">
              {editingVlan ? 'Editar VLAN' : 'Nova VLAN'}
            </h2>

            {error && (
              <div className="p-3 bg-rose-50 dark:bg-rose-950/40 text-rose-600 rounded-xl text-xs">{error}</div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                    Número ID da VLAN *
                  </label>
                  <input
                    type="number"
                    required
                    placeholder="Ex: 20"
                    value={vlanNumber}
                    onChange={(e) => setVlanNumber(e.target.value ? Number(e.target.value) : '')}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                    Nome da VLAN *
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Ex: Consultórios"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                    Subnet (Opcional)
                  </label>
                  <input
                    type="text"
                    placeholder="Ex: 10.10.20.0/24"
                    value={subnet}
                    onChange={(e) => setSubnet(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                    Gateway (Opcional)
                  </label>
                  <input
                    type="text"
                    placeholder="Ex: 10.10.20.1"
                    value={gateway}
                    onChange={(e) => setGateway(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">
                  Descrição
                </label>
                <textarea
                  placeholder="Finalidade da VLAN..."
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
