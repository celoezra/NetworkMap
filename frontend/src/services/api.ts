const API_BASE = '/api';

let activeToken: string | null = null;
let activeUnitId: number | null = null;

export const setAuthToken = (token: string | null) => {
  activeToken = token;
};

export const setActiveUnit = (unitId: number | null) => {
  activeUnitId = unitId;
};

export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };

  if (activeToken) {
    headers['Authorization'] = `Bearer ${activeToken}`;
  }
  
  if (activeUnitId) {
    headers['X-Unit-ID'] = activeUnitId.toString();
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Erro desconhecido na requisição' }));
    throw new Error(errorData.detail || `Erro HTTP ${response.status}`);
  }

  return response.json();
}
