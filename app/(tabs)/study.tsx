import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import * as DocumentPicker from "expo-document-picker";
import { Screen } from "@/src/components/Screen";
import { Card } from "@/src/components/Card";
import { colors } from "@/src/theme";
import { apiFetch } from "@/src/services/api";

export default function StudyScreen(){
  const[course,setCourse]=useState("General"),[status,setStatus]=useState(""),[notes,setNotes]=useState<any[]>([]),[result,setResult]=useState(""),[working,setWorking]=useState("");
  async function load(){try{setNotes(await apiFetch("/notes"));}catch{}}
  useEffect(()=>{load()},[]);
  async function pickPdf(){const r=await DocumentPicker.getDocumentAsync({type:"application/pdf",copyToCacheDirectory:true});if(r.canceled||!r.assets[0])return;const a=r.assets[0];setStatus("Uploading and summarizing…");const form=new FormData();form.append("file",{uri:a.uri,name:a.name,type:"application/pdf"} as any);try{const data=await apiFetch(`/notes/upload?course=${encodeURIComponent(course)}`,{method:"POST",body:form});setStatus(`${data.title} summarized successfully.`);await load();}catch(e:any){setStatus(e.message||"Upload failed")}}
  async function generate(note:any,type:"flashcards"|"quiz"|"exam"){
    setWorking(`${note.id}-${type}`);setResult("");
    const prompts={flashcards:"Create 12 concise question-and-answer flashcards from this selected note. Cover the most important definitions, concepts and examples.",quiz:"Create a 10-question revision quiz from this selected note. Mix short-answer and multiple-choice questions, then provide the answer key after the questions.",exam:"Generate likely exam questions from this selected note and give marking-friendly model answers. Prioritize the most testable concepts."};
    try{const data=await apiFetch("/assistant/chat",{method:"POST",body:JSON.stringify({message:prompts[type],mode:"exam",documentId:note.id})});setResult(data.reply);}catch(e:any){setResult(e.message||"Smith could not generate this revision set.")}finally{setWorking("")}
  }
  return <Screen>
    <Text style={styles.title}>Study</Text><Text style={styles.subtitle}>Upload notes and turn them into useful revision material.</Text>
    <Card><Text style={styles.cardTitle}>PDF Notes</Text><Text style={styles.body}>Smith reads the PDF, saves it to the course and creates an exam-ready summary.</Text><TextInput style={styles.input} value={course} onChangeText={setCourse} placeholder="Course unit" placeholderTextColor={colors.muted}/><Pressable style={styles.button} onPress={pickPdf}><Text style={styles.buttonText}>Upload PDF</Text></Pressable>{!!status&&<Text style={styles.status}>{status}</Text>}</Card>
    {!!result&&<Card style={styles.result}><Text style={styles.cardTitle}>Smith revision set</Text><Text style={styles.resultText}>{result}</Text></Card>}
    <Text style={styles.section}>Saved notes</Text>
    {notes.map(n=><Card key={n.id} style={styles.note}><Text style={styles.cardTitle}>{n.title}</Text><Text style={styles.course}>{n.course}</Text><Text style={styles.body} numberOfLines={7}>{n.summary}</Text><View style={styles.tools}><Pressable style={styles.tool} onPress={()=>generate(n,"flashcards")}><Text style={styles.toolText}>{working===`${n.id}-flashcards`?"…":"Flashcards"}</Text></Pressable><Pressable style={styles.tool} onPress={()=>generate(n,"quiz")}><Text style={styles.toolText}>{working===`${n.id}-quiz`?"…":"Quiz"}</Text></Pressable><Pressable style={styles.tool} onPress={()=>generate(n,"exam")}><Text style={styles.toolText}>{working===`${n.id}-exam`?"…":"Exam Qs"}</Text></Pressable></View></Card>)}
    {!notes.length&&<Text style={styles.empty}>No uploaded notes yet.</Text>}
  </Screen>
}
const styles=StyleSheet.create({title:{color:colors.text,fontSize:28,fontWeight:"800"},subtitle:{color:colors.muted,marginTop:5,marginBottom:18,lineHeight:20},cardTitle:{color:colors.text,fontSize:17,fontWeight:"800"},body:{color:colors.muted,lineHeight:20,marginTop:7},input:{backgroundColor:colors.surface2,color:colors.text,borderWidth:1,borderColor:colors.border,borderRadius:13,padding:13,marginTop:14},button:{backgroundColor:colors.primary,padding:14,borderRadius:13,alignItems:"center",marginTop:10},buttonText:{color:"#061426",fontWeight:"900"},status:{color:colors.success,marginTop:11},section:{color:colors.text,fontSize:18,fontWeight:"800",marginVertical:15},note:{marginBottom:10},course:{color:colors.primary,marginTop:4,fontSize:12,fontWeight:"700"},empty:{color:colors.muted},tools:{flexDirection:"row",gap:8,marginTop:12},tool:{flex:1,borderWidth:1,borderColor:colors.primary,borderRadius:11,paddingVertical:10,alignItems:"center"},toolText:{color:colors.primary,fontWeight:"800",fontSize:12},result:{marginTop:12,backgroundColor:colors.surface2},resultText:{color:colors.text,lineHeight:21,marginTop:10}});
