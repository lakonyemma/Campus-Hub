import { useEffect } from "react";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { AuthProvider } from "@/src/context/AuthContext";
import { prepareNotifications } from "@/src/services/notifications";

export default function RootLayout(){
  useEffect(()=>{ prepareNotifications().catch(()=>{}); },[]);
  return <AuthProvider><StatusBar style="light"/><Stack screenOptions={{headerShown:false}}/></AuthProvider>;
}
