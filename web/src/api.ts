import type { User, DbLayer, MapState } from './types';

export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

// простое локальное хранилище токена (берём из /auth/login)
let token: string | null = localStorage.getItem('token');
export function getToken() { return token; }

export async function me(): Promise<User | null> {
  const r = await fetch(`${API_BASE}/auth/me`, { credentials: 'include' });
  if (r.status === 401) return null;
  if (!r.ok) throw new Error(`me failed: ${r.status}`);
  return r.json();
}

export async function login(email: string, password: string): Promise<void> {
  const r = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  if (!r.ok) throw new Error((await r.text().catch(()=>'')).trim() || `login failed: ${r.status}`);
  const body = await r.json().catch(() => ({} as any));
  if (body?.token) { token = body.token as string; localStorage.setItem('token', token); }
}

export async function logout(): Promise<void> {
  await fetch(`${API_BASE}/auth/logout`, { method: 'POST', credentials: 'include' });
  token = null; localStorage.removeItem('token');
}

export async function fetchLayers(): Promise<DbLayer[]> {
  const r = await fetch(`${API_BASE}/layers/`, { credentials: 'include' });
  if (!r.ok) throw new Error(`layers failed: ${r.status}`);
  return r.json();
}

export function mvtUrlFor(layerId: number) {
  // не добавляем ?token=... — авторизация идёт через Authorization заголовок
  return `${API_BASE}/tiles/layer/${layerId}/{z}/{x}/{y}.mvt`;
}

export async function saveMapState(state: MapState): Promise<void> {
  await fetch(`${API_BASE}/auth/me/map-state`, {
    method: 'PUT',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(state)
  });
}
