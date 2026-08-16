import type { MissionData } from '../types/api';

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';

export async function fetchMissionData(): Promise<MissionData> {
  const response = await fetch(`${API_BASE}/mission`);
  if (!response.ok) {
    throw new Error('Failed to fetch mission data');
  }
  return response.json();
}

export function getAssetUrl(assetPath: string): string {
  return `${API_BASE}/assets/${assetPath}`;
}
