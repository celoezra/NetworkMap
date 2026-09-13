import React, { useState, useEffect } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
  Panel
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { RefreshCw, Server, HardDrive, Cpu } from 'lucide-react';
import { fetchApi } from '../services/api';

// Custom Nodes for React Flow
const CustomRackNode = ({ data }: any) => (
  <div className="bg-slate-900 border-2 border-indigo-500 text-white rounded-2xl p-4 shadow-2xl min-w-[200px]">
    <Handle type="source" position={Position.Right} className="!bg-indigo-500 !w-3 !h-3" />
    <div className="flex items-center space-x-2 border-b border-slate-700 pb-2 mb-2">
      <Server className="w-5 h-5 text-indigo-400" />
      <span className="font-bold text-sm tracking-wide">{data.label}</span>
    </div>
    <div className="text-[11px] text-slate-400">
      <div><strong>Local:</strong> {data.location}</div>
      {data.description && <div className="mt-1 text-slate-300 italic">{data.description}</div>}
    </div>
  </div>
);

const CustomSwitchNode = ({ data }: any) => (
  <div className="bg-slate-900 border-2 border-blue-500 text-white rounded-2xl p-4 shadow-2xl min-w-[220px]">
    <Handle type="target" position={Position.Left} className="!bg-blue-500 !w-3 !h-3" />
    <Handle type="source" position={Position.Right} className="!bg-blue-500 !w-3 !h-3" />
    <div className="flex items-center justify-between border-b border-slate-700 pb-2 mb-2">
      <div className="flex items-center space-x-2">
        <HardDrive className="w-5 h-5 text-blue-400" />
        <span className="font-bold text-sm">{data.label}</span>
      </div>
      <span className="text-[10px] bg-blue-900/60 text-blue-300 font-mono px-2 py-0.5 rounded">
        {data.ports}P
      </span>
    </div>
    <div className="text-[11px] text-slate-400 space-y-0.5 font-mono">
      <div><strong>Host:</strong> {data.hostname}</div>
      <div><strong>IP:</strong> {data.ip || 'Sem IP'}</div>
    </div>
  </div>
);

const CustomDeviceNode = ({ data }: any) => (
  <div className="bg-slate-900 border-2 border-purple-500 text-white rounded-2xl p-3.5 shadow-2xl min-w-[190px]">
    <Handle type="target" position={Position.Left} className="!bg-purple-500 !w-3 !h-3" />
    <div className="flex items-center space-x-2 border-b border-slate-700 pb-2 mb-2">
      <Cpu className="w-4 h-4 text-purple-400" />
      <span className="font-bold text-xs text-purple-200">{data.label}</span>
    </div>
    <div className="text-[11px] text-slate-400 space-y-0.5">
      <div><strong>IP:</strong> <span className="font-mono">{data.ip || 'N/A'}</span></div>
      <div><strong>Local:</strong> {data.location}</div>
      <div><strong>VLAN:</strong> {data.vlan}</div>
    </div>
  </div>
);

const nodeTypes = {
  rackNode: CustomRackNode,
  switchNode: CustomSwitchNode,
  deviceNode: CustomDeviceNode,
};

export const NetworkMapView: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState<any>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<any>([]);
  const [loading, setLoading] = useState(true);

  const loadGraph = async () => {
    setLoading(true);
    try {
      const data = await fetchApi<{ nodes: any[]; edges: any[] }>('/network-map');
      setNodes(data.nodes);
      setEdges(data.edges);
    } catch (err) {
      console.error('Erro ao carregar mapa da rede:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGraph();
  }, []);

  return (
    <div className="space-y-4 h-[calc(100vh-8rem)] flex flex-col">
      {/* Top Controls Bar */}
      <div className="flex justify-between items-center bg-white dark:bg-slate-800 p-4 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-white">Mapa Visual da Rede</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Diagrama interativo dos relacionamentos entre Racks, Switches, Uplinks e Equipamentos.
          </p>
        </div>

        <button
          onClick={loadGraph}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold flex items-center space-x-2 transition shadow-md"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Atualizar Mapa</span>
        </button>
      </div>

      {/* React Flow Container */}
      <div className="flex-1 bg-slate-950 rounded-2xl border border-slate-800 shadow-2xl relative overflow-hidden">
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center text-slate-400 text-sm z-50 bg-slate-950/80 backdrop-blur-sm">
            Gerando diagrama de infraestrutura em tempo real...
          </div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            colorMode="dark"
          >
            <Background color="#334155" gap={24} size={1} />
            <Controls className="!bg-slate-800 !border-slate-700 !text-white" />
            <Panel position="bottom-right" className="bg-slate-900/90 p-3 rounded-xl border border-slate-800 text-white text-[11px] space-y-1">
              <div className="font-bold border-b border-slate-700 pb-1 mb-1">Legenda do Grafo</div>
              <div className="flex items-center space-x-2">
                <div className="w-2.5 h-2.5 bg-indigo-500 rounded-full" />
                <span>Racks Físicos</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2.5 h-2.5 bg-blue-500 rounded-full" />
                <span>Switches</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2.5 h-2.5 bg-purple-500 rounded-full" />
                <span>Equipamentos Conectados</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2.5 h-2.5 bg-amber-500 rounded-full" />
                <span>Conexões Uplink entre Switches</span>
              </div>
            </Panel>
          </ReactFlow>
        )}
      </div>
    </div>
  );
};
