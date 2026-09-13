import React, { useState, useEffect } from 'react';
import { Database, Download, RefreshCw, ShieldCheck, AlertTriangle } from 'lucide-react';
import { fetchApi } from '../services/api';

interface BackupItem {
  id: number;
  filename: string;
  created_at: string;
  size_kb: number;
}

export const BackupView: React.FC = () => {
  const [backups, setBackups] = useState<BackupItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const loadBackups = async () => {
    setLoading(true);
    try {
      const data = await fetchApi<BackupItem[]>('/system/backups');
      setBackups(data);
    } catch (err) {
      console.error('Erro ao carregar backups:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBackups();
  }, []);

  const handleCreateBackup = async () => {
    setMessage(null);
    try {
      const res: any = await fetchApi('/system/backups/create', { method: 'POST' });
      setMessage({ type: 'success', text: res.message || 'Backup criptografado criado com sucesso!' });
      loadBackups();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Erro ao criar backup' });
    }
  };

  const handleRestoreBackup = async (backupId: number, filename: string) => {
    if (
      !confirm(
        `ATENÇÃO: Restaurar o backup "${filename}" irá substituir a base de dados atual.\n\nUm backup de segurança pre-restore será gerado automaticamente. Deseja prosseguir?`
      )
    ) {
      return;
    }

    setMessage(null);
    try {
      const res: any = await fetchApi(`/system/backups/restore/${backupId}`, { method: 'POST' });
      setMessage({ type: 'success', text: res.message || 'Backup restaurado com sucesso!' });
      loadBackups();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || 'Erro ao restaurar backup' });
    }
  };

  const handleDownloadCsv = (type: string) => {
    window.open(`/api/system/export/${type}`, '_blank');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800 dark:text-white">Backup e Exportação de Dados</h1>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Gerencie backups criptografados do banco SQLCipher local e exporte relatórios em CSV.
        </p>
      </div>

      {message && (
        <div
          className={`p-4 rounded-xl text-xs font-semibold flex items-center space-x-2 ${
            message.type === 'success'
              ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900'
              : 'bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-900'
          }`}
        >
          {message.type === 'success' ? <ShieldCheck className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
          <span>{message.text}</span>
        </div>
      )}

      {/* Main Grid Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Backup Card */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-slate-200 dark:border-slate-700 shadow-sm space-y-4">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-blue-100 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 rounded-xl">
              <Database className="w-6 h-6" />
            </div>
            <div>
              <h2 className="font-bold text-lg text-slate-800 dark:text-white">Backups Criptografados</h2>
              <p className="text-xs text-slate-400">Armazenamento local seguro em data/networkmap.db</p>
            </div>
          </div>

          <p className="text-xs text-slate-600 dark:text-slate-300">
            Gere cópias de segurança ponto-a-ponto instantâneas. Os arquivos de backup permanecem criptografados com a mesma chave do sistema.
          </p>

          <button
            onClick={handleCreateBackup}
            className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold flex items-center justify-center space-x-2 transition shadow-md"
          >
            <Database className="w-4 h-4" />
            <span>Fazer Backup Criptografado Agora</span>
          </button>
        </div>

        {/* Export CSV Card */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-slate-200 dark:border-slate-700 shadow-sm space-y-4">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 rounded-xl">
              <Download className="w-6 h-6" />
            </div>
            <div>
              <h2 className="font-bold text-lg text-slate-800 dark:text-white">Exportação para CSV</h2>
              <p className="text-xs text-slate-400">Relatórios tabulares de infraestrutura</p>
            </div>
          </div>

          <p className="text-xs text-slate-600 dark:text-slate-300">
            Baixe inventários e mapeamento de portas em planilha para auditorias externas ou planilhas do Excel.
          </p>

          <div className="grid grid-cols-2 gap-2 pt-1">
            <button
              onClick={() => handleDownloadCsv('devices')}
              className="py-2 px-3 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-800 dark:text-white rounded-xl text-xs font-medium transition text-left"
            >
              Exportar Equipamentos
            </button>
            <button
              onClick={() => handleDownloadCsv('switches')}
              className="py-2 px-3 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-800 dark:text-white rounded-xl text-xs font-medium transition text-left"
            >
              Exportar Switches
            </button>
            <button
              onClick={() => handleDownloadCsv('ports')}
              className="py-2 px-3 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-800 dark:text-white rounded-xl text-xs font-medium transition text-left"
            >
              Exportar Portas
            </button>
            <button
              onClick={() => handleDownloadCsv('vlans')}
              className="py-2 px-3 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 text-slate-800 dark:text-white rounded-xl text-xs font-medium transition text-left"
            >
              Exportar VLANs
            </button>
          </div>
        </div>
      </div>

      {/* Backups List */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center">
          <h3 className="font-bold text-sm text-slate-800 dark:text-white">Arquivos de Backup Armazenados</h3>
          <button
            onClick={loadBackups}
            className="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 rounded-lg transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        <div className="divide-y divide-slate-100 dark:divide-slate-700/60">
          {backups.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-xs">
              Nenhum backup realizado ainda. Clique no botão acima para gerar o primeiro backup.
            </div>
          ) : (
            backups.map((b) => (
              <div key={b.id} className="p-4 flex items-center justify-between hover:bg-slate-50/80 dark:hover:bg-slate-700/30 transition text-xs">
                <div className="space-y-0.5">
                  <div className="font-mono font-bold text-slate-800 dark:text-white">{b.filename}</div>
                  <div className="text-[10px] text-slate-400">
                    Criado em: {new Date(b.created_at).toLocaleString('pt-BR')} | Tamanho: {b.size_kb} KB
                  </div>
                </div>

                <button
                  onClick={() => handleRestoreBackup(b.id, b.filename)}
                  className="px-3 py-1.5 bg-amber-50 dark:bg-amber-950/40 hover:bg-amber-100 dark:hover:bg-amber-900/60 text-amber-700 dark:text-amber-400 rounded-lg font-semibold transition"
                >
                  Restaurar Este Backup
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
