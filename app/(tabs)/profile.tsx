import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput } from "react-native";
import { router } from "expo-router";
import { Screen } from "@/src/components/Screen";
import { Card } from "@/src/components/Card";
import { colors } from "@/src/theme";
import { applyDownloadedUpdate, checkForAppUpdate } from "@/src/services/updates";
import { useAuth } from "@/src/context/AuthContext";
import { apiFetch } from "@/src/services/api";

export default function ProfileScreen(){
  const {user,logout,refreshUser}=useAuth();
  const [message,setMessage]=useState(""); const [ready,setReady]=useState(false); const [saving,setSaving]=useState(false);
  const [name,setName]=useState(""); const [programme,setProgramme]=useState(""); const [semester,setSemester]=useState(""); const [year,setYear]=useState(""); const [studentNumber,setStudentNumber]=useState(""); const [campus,setCampus]=useState("");
  useEffect(()=>{setName(user?.name||"");setProgramme(user?.programme||"");setSemester(user?.semester||"");setYear(user?.academic_year||"");setStudentNumber(user?.student_number||"");setCampus(user?.campus||"")},[user]);
  async function saveProfile(){setSaving(true);setMessage("");try{await apiFetch("/me",{method:"PATCH",body:JSON.stringify({name,university:"ISBAT University",programme,semester,academic_year:year,student_number:studentNumber,campus})});await refreshUser();setMessage("Profile saved.");}catch(e:any){setMessage(e.message||"Could not save profile")}finally{setSaving(false)}}
  async function checkUpdate(){try{const result=await checkForAppUpdate();setReady(result.updated);setMessage(result.message);}catch{setMessage("Update check failed. Try again when connected to the internet.")}}
  async function signOut(){await logout();router.replace("/login")}
  return <Screen>
    <Text style={styles.title}>Profile</Text><Text style={styles.subtitle}>ISBAT University academic profile and Campus Hub settings.</Text>
    <Card><Text style={styles.uni}>ISBAT UNIVERSITY</Text><Text style={styles.meta}>{user?.email||""}</Text><TextInput style={styles.input} value={name} onChangeText={setName} placeholder="Full name" placeholderTextColor={colors.muted}/><TextInput style={styles.input} value={programme} onChangeText={setProgramme} placeholder="Programme e.g. Diploma in Software Engineering" placeholderTextColor={colors.muted}/><TextInput style={styles.input} value={semester} onChangeText={setSemester} placeholder="Semester" placeholderTextColor={colors.muted}/><TextInput style={styles.input} value={year} onChangeText={setYear} placeholder="Academic year" placeholderTextColor={colors.muted}/><TextInput style={styles.input} value={studentNumber} onChangeText={setStudentNumber} placeholder="Student number" placeholderTextColor={colors.muted}/><TextInput style={styles.input} value={campus} onChangeText={setCampus} placeholder="Campus" placeholderTextColor={colors.muted}/><Pressable style={styles.button} onPress={saveProfile}><Text style={styles.buttonText}>{saving?"Saving…":"Save profile"}</Text></Pressable></Card>
    <Pressable style={styles.finance} onPress={()=>router.push("/finance")}><Text style={styles.financeTitle}>Fees & Payments</Text><Text style={styles.meta}>Track tuition, university charges, payments and balances.</Text></Pressable>
    <Card style={{marginTop:12}}><Text style={styles.cardTitle}>App updates</Text><Text style={styles.meta}>Campus Hub checks for compatible updates without reinstalling the app.</Text><Pressable style={styles.button} onPress={checkUpdate}><Text style={styles.buttonText}>Check for updates</Text></Pressable>{!!message&&<Text style={styles.message}>{message}</Text>}{ready&&<Pressable style={styles.secondary} onPress={applyDownloadedUpdate}><Text style={styles.secondaryText}>Restart and update</Text></Pressable>}</Card>
    <Pressable style={styles.logout} onPress={signOut}><Text style={styles.logoutText}>Sign out</Text></Pressable>
  </Screen>
}
const styles=StyleSheet.create({title:{color:colors.text,fontSize:28,fontWeight:"800"},subtitle:{color:colors.muted,marginTop:5,marginBottom:18},uni:{color:colors.primary,fontWeight:"900",letterSpacing:1.4,fontSize:13},meta:{color:colors.muted,marginTop:5,lineHeight:20},cardTitle:{color:colors.text,fontSize:17,fontWeight:"800"},input:{backgroundColor:colors.background,color:colors.text,borderWidth:1,borderColor:colors.border,borderRadius:12,padding:13,marginTop:10},button:{backgroundColor:colors.primary,padding:14,borderRadius:13,alignItems:"center",marginTop:15},buttonText:{color:"#061426",fontWeight:"900"},message:{color:colors.text,marginTop:12},secondary:{padding:14,borderRadius:13,borderWidth:1,borderColor:colors.primary,alignItems:"center",marginTop:10},secondaryText:{color:colors.primary,fontWeight:"800"},finance:{marginTop:12,padding:17,borderRadius:16,backgroundColor:colors.surface2,borderWidth:1,borderColor:colors.border},financeTitle:{color:colors.text,fontSize:17,fontWeight:"900"},logout:{padding:14,borderRadius:13,borderWidth:1,borderColor:colors.danger,alignItems:"center",marginTop:18},logoutText:{color:colors.danger,fontWeight:"800"}});
