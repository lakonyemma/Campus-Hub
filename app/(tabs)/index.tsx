import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { Screen } from "@/src/components/Screen";
import { Card } from "@/src/components/Card";
import { colors } from "@/src/theme";
import { router } from "expo-router";
import { apiFetch } from "@/src/services/api";
import { useAuth } from "@/src/context/AuthContext";

export default function HomeScreen(){
  const {user}=useAuth(); const [data,setData]=useState<any>({classes:[],assignments:[],exams:[],gpa:null});
  async function load(){try{setData(await apiFetch("/dashboard"))}catch{}}
  useEffect(()=>{load()},[]);
  const next=data.classes?.[0];
  return <Screen>
    <Text style={styles.eyebrow}>CAMPUS HUB</Text><Text style={styles.title}>Hello, {user?.name?.split(" ")[0]||"Student"}.</Text><Text style={styles.subtitle}>Your academic picture for today.</Text>
    <Card style={styles.hero}><Text style={styles.cardLabel}>NEXT CLASS</Text><Text style={styles.heroTitle}>{next?.course||"No class scheduled"}</Text>{next&&<Text style={styles.info}>{next.start_time}–{next.end_time}{next.room?` · ${next.room}`:""}</Text>}</Card>
    <View style={styles.metrics}><Card style={styles.metric}><Text style={styles.metricValue}>{data.gpa??"—"}</Text><Text style={styles.info}>GPA</Text></Card><Card style={styles.metric}><Text style={styles.metricValue}>{data.assignments?.length||0}</Text><Text style={styles.info}>Open tasks</Text></Card><Card style={styles.metric}><Text style={styles.metricValue}>{data.exams?.length||0}</Text><Text style={styles.info}>Exams</Text></Card></View>
    <Text style={styles.section}>Today</Text>{(data.classes||[]).map((item:any)=><Card key={item.id} style={styles.item}><View style={styles.row}><Text style={styles.time}>{item.start_time}</Text><View style={{flex:1}}><Text style={styles.itemTitle}>{item.course}</Text><Text style={styles.info}>{item.room||"Room not set"}</Text></View></View></Card>)}{!data.classes?.length&&<Card style={styles.item}><Text style={styles.info}>No classes saved for today.</Text></Card>}
    <View style={styles.sectionRow}><Text style={styles.section}>Assignments</Text><Pressable onPress={()=>router.push("/assignments")}><Text style={styles.link}>Manage</Text></Pressable></View>
    {(data.assignments||[]).slice(0,3).map((item:any)=><Card key={item.id} style={styles.item}><Text style={styles.itemTitle}>{item.title}</Text><Text style={styles.info}>{item.course}{item.due_at?` · ${new Date(item.due_at).toLocaleDateString()}`:""}</Text><View style={styles.progressTrack}><View style={[styles.progress,{width:`${Math.max(0,Math.min(100,item.progress||0))}%`}]} /></View><Text style={styles.progressText}>{item.progress||0}% complete</Text></Card>)}
    <Pressable style={styles.academicButton} onPress={()=>router.push("/academic")}><Text style={styles.academicTitle}>Academic records</Text><Text style={styles.academicSub}>Attendance, GPA, exams and profile details.</Text></Pressable>
    <Pressable style={styles.smithButton} onPress={()=>router.push("/(tabs)/smith")}><Text style={styles.smithTitle}>Ask Smith</Text><Text style={styles.smithSub}>Plan my evening, quiz me, or summarize my notes.</Text></Pressable>
  </Screen>
}
const styles=StyleSheet.create({eyebrow:{color:colors.primary,fontWeight:"800",letterSpacing:2,fontSize:12},title:{color:colors.text,fontSize:28,fontWeight:"800",marginTop:8},subtitle:{color:colors.muted,marginTop:6,marginBottom:18,fontSize:15},hero:{backgroundColor:colors.surface2,marginBottom:14},cardLabel:{color:colors.primary,fontSize:11,fontWeight:"800",letterSpacing:1.5},heroTitle:{color:colors.text,fontSize:22,fontWeight:"800",marginTop:8},info:{color:colors.muted,marginTop:5},metrics:{flexDirection:"row",gap:8,marginBottom:8},metric:{flex:1},metricValue:{color:colors.text,fontSize:22,fontWeight:"900"},section:{color:colors.text,fontSize:18,fontWeight:"800",marginVertical:12},sectionRow:{flexDirection:"row",alignItems:"center",justifyContent:"space-between"},link:{color:colors.primary,fontWeight:"800"},item:{marginBottom:10},row:{flexDirection:"row",alignItems:"center",gap:16},time:{color:colors.primary,fontWeight:"800",width:54},itemTitle:{color:colors.text,fontWeight:"700",fontSize:16},progressTrack:{height:6,backgroundColor:colors.border,borderRadius:99,marginTop:14,overflow:"hidden"},progress:{height:"100%",backgroundColor:colors.primary,borderRadius:99},progressText:{color:colors.muted,fontSize:12,marginTop:7},academicButton:{marginTop:10,padding:17,borderWidth:1,borderColor:colors.primary,borderRadius:18},academicTitle:{fontSize:17,fontWeight:"900",color:colors.primary},academicSub:{color:colors.muted,marginTop:3},smithButton:{marginTop:10,padding:18,backgroundColor:colors.primary,borderRadius:18},smithTitle:{fontSize:18,fontWeight:"900",color:"#061426"},smithSub:{color:"#0B2E4F",marginTop:3}});
