import AsyncStorage from "@react-native-async-storage/async-storage";

export const API_URL = process.env.EXPO_PUBLIC_API_URL || "";
const TOKEN_KEY = "campus_hub_token";

export async function getToken() { return AsyncStorage.getItem(TOKEN_KEY); }
export async function setToken(token: string) { await AsyncStorage.setItem(TOKEN_KEY, token); }
export async function clearToken() { await AsyncStorage.removeItem(TOKEN_KEY); }

export async function apiFetch(path: string, init: RequestInit = {}) {
  if (!API_URL) throw new Error("Campus Hub server is not configured.");
  const token = await getToken();
  const headers: Record<string,string> = { ...(init.headers as Record<string,string> || {}) };
  if (!(init.body instanceof FormData)) headers["Content-Type"] = headers["Content-Type"] || "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${API_URL}${path}`, { ...init, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.message || "Request failed");
  return data;
}
