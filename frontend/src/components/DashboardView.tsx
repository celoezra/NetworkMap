import React from 'react';
import { Server, HardDrive, Cpu, MapPin, Layers, CheckCircle2, AlertCircle, Radio } from 'lucide-react';
import type { DashboardStats } from '../types';

interface DashboardViewProps {
  stats: DashboardStats | null;
  onNavigate: (tab: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ stats, onNavigate }) => {
  if (!stats) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-400">
        Carregando estatísticas da infraestrutura...
      </div>
    );
  }

  const occupancyRate = stats.total_ports > 0 ? Math.round((stats.used_ports / stats.total_ports) * 100) : 0;

  const cards = [
    { label: 'Racks Cadastrados', value: stats.total_racks, icon: Server, color: 'text-indigo-600', bg: 'bg-indigo-50 dark:bg-indigo-950/40', border: 'border-indigo-100 dark:border-indigo-900', tab: 'racks' },
    { label: 'Switches', value: stats.total_switches, icon: HardDrive, color: 'text-blue-600', bg: 'bg-blue-50 dark:bg-blue-950/40', border: 'border-blue-100 dark:border-blue-900', tab: 'switches' },
    { label: 'Portas Totais', value: stats.total_ports, icon: Radio, color: 'text-sky-600', bg: 'bg-sky-50 dark:bg-sky-950/40', border: 'border-sky-100 dark:border-sky-900', tab: 'switches' },
    { label: 'Portas Utilizadas', value: stats.used_ports, icon: CheckCircle2, color: 'text-emerald-600', bg: 'bg-emerald-50 dark:bg-emerald-950/40', border: 'border-emerald-100 dark:border-emerald-900', tab: 'switches' },
    { label: 'Portas Livres', value: stats.free_ports, icon: AlertCircle, color: 'text-amber-600', bg: 'bg-amber-50 dark:bg-amber-950/40', border: 'border-amber-100 dark:border-amber-900', tab: 'switches' },
    { label: 'Equipamentos', value: stats.total_devices, icon: Cpu, color: 'text-purple-600', bg: 'bg-purple-50 dark:bg-purple-950/40', border: 'border-purple-100 dark:border-purple-900', tab: 'devices' },
    { label: 'VLANs Cadastradas', value: stats.total_vlans, icon: Layers, color: 'text-pink-600', bg: 'bg-pink-50 dark:bg-pink-950/40', border: 'border-pink-100 dark:border-pink-900', tab: 'vlans' },
    { label: 'Locais Cadastrados', value: stats.total_locations, icon: MapPin, color: 'text-teal-600', bg: 'bg-teal-50 dark:bg-teal-950/40', border: 'border-teal-100 dark:border-teal-900', tab: 'locations' },
  ];

  return (
    <div className="space-y-6">
      {/* Header Title Banner */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-2xl p-6 text-white shadow-lg flex flex-col md:flex-row justify-between items-start md:items-center">
        <div>
          <h1 className="text-2xl font-bold">Visão Geral da Infraestrutura</h1>
          <p className="text-blue-100 text-sm mt-1">
            Mapeamento físico e lógico em tempo real da rede corporativa
          </p>
        </div>
        <button
          onClick={() => onNavigate('network-map')}
          className="mt-4 md:mt-0 px-4 py-2 bg-white text-blue-700 hover:bg-blue-50 font-semibold rounded-xl text-sm transition shadow-sm"
        >
          Ver Mapa da Rede Interativo
        </button>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              onClick={() => onNavigate(card.tab)}
              className={`p-5 rounded-2xl bg-white dark:bg-slate-800 border ${card.border} shadow-sm hover:shadow-md transition cursor-pointer flex items-center justify-between group`}
            >
              <div>
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400 block">{card.label}</span>
                <span className="text-2xl font-bold text-slate-800 dark:text-white mt-1 block">{card.value}</span>
              </div>
              <div className={`p-3 rounded-xl ${card.bg} ${card.color} group-hover:scale-110 transition-transform`}>
                <Icon className="w-6 h-6" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Port Utilization Gauge & Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white dark:bg-slate-800 rounded-2xl p-6 border border-slate-200 dark:border-slate-700 shadow-sm">
          <h2 className="text-lg font-bold text-slate-800 dark:text-white mb-4">Taxa de Ocupação de Portas</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center text-sm font-medium">
              <span className="text-slate-600 dark:text-slate-300">Portas Ativas vs Livres</span>
              <span className="text-blue-600 dark:text-blue-400">{occupancyRate}% Ocupadas</span>
            </div>

            {/* Progress bar */}
            <div className="w-full bg-slate-100 dark:bg-slate-700 h-4 rounded-full overflow-hidden flex">
              <div
                className="bg-emerald-500 h-full transition-all duration-500"
                style={{ width: `${occupancyRate}%` }}
                title={`Ocupadas: ${stats.used_ports}`}
              />
              <div
                className="bg-slate-300 dark:bg-slate-600 h-full transition-all duration-500"
                style={{ width: `${100 - occupancyRate}%` }}
                title={`Livres: ${stats.free_ports}`}
              />
            </div>

            <div className="grid grid-cols-2 gap-4 pt-4 border-t border-slate-100 dark:border-slate-700/60">
              <div className="flex items-center space-x-3">
                <div className="w-3.5 h-3.5 bg-emerald-500 rounded-full" />
                <div>
                  <div className="text-xs text-slate-400">Portas Conectadas/Uplinks</div>
                  <div className="text-base font-bold text-slate-800 dark:text-white">{stats.used_ports}</div>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <div className="w-3.5 h-3.5 bg-slate-400 rounded-full" />
                <div>
                  <div className="text-xs text-slate-400">Portas Livres Disponíveis</div>
                  <div className="text-base font-bold text-slate-800 dark:text-white">{stats.free_ports}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Tips */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-800 dark:text-white mb-2">Acesso Rápido de TI</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-4">
              Consulte e edite portas diretamente abrindo o menu Switches ou utilize a barra de busca superior para localizar qualquer IP ou hostname.
            </p>
          </div>
          <div className="space-y-2">
            <button
              onClick={() => onNavigate('switches')}
              className="w-full py-2.5 px-4 bg-slate-100 dark:bg-slate-700/60 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-800 dark:text-white rounded-xl text-xs font-semibold transition text-left flex items-center justify-between"
            >
              <span>Visualizar Matriz de Portas</span>
              <span>→</span>
            </button>
            <button
              onClick={() => onNavigate('devices')}
              className="w-full py-2.5 px-4 bg-slate-100 dark:bg-slate-700/60 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-800 dark:text-white rounded-xl text-xs font-semibold transition text-left flex items-center justify-between"
            >
              <span>Gerenciar Equipamentos</span>
              <span>→</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
