import React, { createContext, useContext, useEffect, useState } from "react";
import { apiFetch, clearToken, getToken, setToken } from "@/src/services/api";

type User = { id: number; name: string; email: string };
type AuthState = { user: User | null; loading: boolean; login: (email:string,password:string)=>Promise<void>; register:(name:string,email:string,password:string)=>Promise<void>; logout:()=>Promise<void> };
const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null); const [loading, setLoading] = useState(true);
  useEffect(() => { (async () => { try { if (await getToken()) setUser(await apiFetch("/me")); } catch { await clearToken(); } finally { setLoading(false); } })(); }, []);
  async function login(email:string,password:string){ const data=await apiFetch("/auth/login",{method:"POST",body:JSON.stringify({email,password})}); await setToken(data.token); setUser(data.user); }
  async function register(name:string,email:string,password:string){ const data=await apiFetch("/auth/register",{method:"POST",body:JSON.stringify({name,email,password})}); await setToken(data.token); setUser(data.user); }
  async function logout(){ await clearToken(); setUser(null); }
  return <AuthContext.Provider value={{user,loading,login,register,logout}}>{children}</AuthContext.Provider>;
}
export function useAuth(){ const value=useContext(AuthContext); if(!value) throw new Error("useAuth must be used inside AuthProvider"); return value; }
