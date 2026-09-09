import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { Screen } from "@/src/components/Screen";
import { Card } from "@/src/components/Card";
import { colors } from "@/src/theme";
import { apiFetch } from "@/src/services/api";

const days=["MON","TUE","WED","THU","FRI","SAT","SUN"];
export default function ScheduleScreen(){
  const [entries,setEntries]=useState<any[]>([]); const [exams,setExams]=useState<any[]>([]); const [day,setDay]=useState(new Date().getDay()===0?6:new Date().getDay()-1);
  const [course,setCourse]=useState(""); const [room,setRoom]=useState(""); const [start,setStart]=useState("09:00"); const [end,setEnd]=useState("10:00"); const [busy,setBusy]=useState(false);
  async function load(){ try{ const [t,e]=await Promise.all([apiFetch("/timetable"),apiFetch("/exams")]); setEntries(t);setExams(e);}catch{} }
  useEffect(()=>{load()},[]);
  async function addClass(){ if(!course.trim())return; setBusy(true); try{await apiFetch("/timetable",{method:"POST",body:JSON.stringify({course:course.trim(),room:room.trim()||null,weekday:day,start_time:start,end_time:end})});setCourse("");setRoom("");await load();}finally{setBusy(false)} }
  const filtered=entries.filter(e=>e.weekday===day);
  return <Screen>
    <Text style={styles.title}>Schedule</Text><Text style={styles.subtitle}>Classes and upcoming exams.</Text>
    <View style={styles.days}>{days.map((d,i)=><Pressable key={d} onPress={()=>setDay(i)} style={[styles.day,day===i&&styles.activeDay]}><Text style={[styles.dayText,day===i&&styles.activeText]}>{d}</Text></Pressable>)}</View>
    {filtered.map(c=><Card key={c.id} style={styles.card}><Text style={styles.time}>{c.start_time}–{c.end_time}</Text><Text style={styles.unit}>{c.course}</Text><Text style={styles.room}>{c.room||"Room not set"}{c.lecturer?` · ${c.lecturer}`:""}</Text></Card>)}
    {!filtered.length&&<Card style={styles.card}><Text style={styles.room}>No classes saved for {days[day]}.</Text></Card>}
    <Text style={styles.section}>Add class</Text>
    <Card><TextInput value={course} onChangeText={setCourse} placeholder="Course unit" placeholderTextColor={colors.muted} style={styles.input}/><TextInput value={room} onChangeText={setRoom} placeholder="Room" placeholderTextColor={colors.muted} style={styles.input}/><View style={styles.row}><TextInput value={start} onChangeText={setStart} placeholder="09:00" placeholderTextColor={colors.muted} style={[styles.input,{flex:1}]}/><TextInput value={end} onChangeText={setEnd} placeholder="10:00" placeholderTextColor={colors.muted} style={[styles.input,{flex:1}]}/></View><Pressable onPress={addClass} style={styles.button}><Text style={styles.buttonText}>{busy?"Saving…":"Save class"}</Text></Pressable></Card>
    <Text style={styles.section}>Upcoming exams</Text>
    {exams.slice(0,5).map(e=><Card key={e.id} style={styles.card}><Text style={styles.unit}>{e.course}</Text><Text style={styles.room}>{new Date(e.exam_at).toLocaleString()}{e.room?` · ${e.room}`:""}</Text></Card>)}
    {!exams.length&&<Card><Text style={styles.room}>No exams saved yet.</Text></Card>}
  </Screen>
}
const styles=StyleSheet.create({title:{color:colors.text,fontSize:28,fontWeight:"800"},subtitle:{color:colors.muted,marginTop:5,marginBottom:18},days:{flexDirection:"row",gap:6,marginBottom:18},day:{flex:1,paddingVertical:9,borderRadius:10,backgroundColor:colors.surface,alignItems:"center"},activeDay:{backgroundColor:colors.primary},dayText:{color:colors.muted,fontSize:9,fontWeight:"800"},activeText:{color:"#061426"},card:{marginBottom:10},time:{color:colors.primary,fontWeight:"800"},unit:{color:colors.text,fontWeight:"800",fontSize:17,marginTop:5},room:{color:colors.muted,marginTop:4},section:{color:colors.text,fontSize:18,fontWeight:"800",marginVertical:14},input:{backgroundColor:colors.background,borderWidth:1,borderColor:colors.border,color:colors.text,borderRadius:12,padding:13,marginBottom:10},row:{flexDirection:"row",gap:10},button:{backgroundColor:colors.primary,padding:14,borderRadius:13,alignItems:"center"},buttonText:{color:"#061426",fontWeight:"900"}});
