import React, { useState, useEffect } from 'react';
import { Search, RefreshCw } from 'lucide-react';
import type { AuditLog } from '../types';
import { fetchApi } from '../services/api';

export const AuditLogsView: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [filterQuery, setFilterQuery] = useState('');
  const [loading, setLoading] = useState(true);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const data = await fetchApi<AuditLog[]>('/system/audit-logs');
      setLogs(data);
    } catch (err) {
      console.error('Erro ao carregar histórico:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, []);

  const filteredLogs = logs.filter(
    (l) =>
      (l.entity_name && l.entity_name.toLowerCase().includes(filterQuery.toLowerCase())) ||
      l.entity_type.toLowerCase().includes(filterQuery.toLowerCase()) ||
      l.action.toLowerCase().includes(filterQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-white">Histórico de Alterações</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Registro de auditoria de criações, edições, exclusões e restaurações no sistema.
          </p>
        </div>
        <button
          onClick={loadLogs}
          className="px-4 py-2 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 rounded-xl text-xs font-semibold flex items-center space-x-2 transition"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Atualizar</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-white dark:bg-slate-800 p-4 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Filtrar eventos por objeto ou ação..."
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 bg-slate-50 dark:bg-slate-700/60 border border-slate-200 dark:border-slate-600 rounded-xl text-xs"
          />
        </div>
      </div>

      {/* Audit Logs Table */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-700/50 border-b border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 uppercase font-semibold">
                <th className="p-4">Data / Horário</th>
                <th className="p-4">Usuário</th>
                <th className="p-4">Ação</th>
                <th className="p-4">Objeto</th>
                <th className="p-4">Identificação</th>
                <th className="p-4">Detalhes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700/60">
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-400">
                    Nenhum registro no histórico de auditoria.
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => {
                  const dateFormatted = new Date(log.timestamp).toLocaleString('pt-BR');
                  return (
                    <tr key={log.id} className="hover:bg-slate-50/80 dark:hover:bg-slate-700/30 transition">
                      <td className="p-4 font-mono text-slate-600 dark:text-slate-300">{dateFormatted}</td>
                      <td className="p-4 font-semibold text-slate-800 dark:text-white">{log.user}</td>
                      <td className="p-4">
                        <span
                          className={`px-2 py-0.5 rounded font-bold text-[10px] uppercase ${
                            log.action === 'CREATE'
                              ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400'
                              : log.action === 'UPDATE'
                              ? 'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-400'
                              : 'bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-400'
                          }`}
                        >
                          {log.action}
                        </span>
                      </td>
                      <td className="p-4 font-semibold text-slate-700 dark:text-slate-200">{log.entity_type}</td>
                      <td className="p-4 font-mono text-slate-800 dark:text-slate-100">{log.entity_name || '-'}</td>
                      <td className="p-4 text-[11px] text-slate-500 max-w-xs truncate">
                        {log.new_values || log.previous_values || '-'}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
