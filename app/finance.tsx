import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput } from "react-native";
import { router } from "expo-router";
import { Screen } from "@/src/components/Screen";
import { Card } from "@/src/components/Card";
import { colors } from "@/src/theme";
import { apiFetch } from "@/src/services/api";

export default function FinanceScreen(){
  const [data,setData]=useState<any>({items:[],total_due:0,total_paid:0,balance:0});
  const [title,setTitle]=useState("Tuition"); const [due,setDue]=useState(""); const [paid,setPaid]=useState(""); const [semester,setSemester]=useState("Current"); const [message,setMessage]=useState("");
  async function load(){try{setData(await apiFetch("/fees"))}catch(e:any){setMessage(e.message||"Could not load fees")}}
  useEffect(()=>{load()},[]);
  async function add(){const amountDue=Number(due),amountPaid=Number(paid||0);if(!title.trim()||Number.isNaN(amountDue))return;try{await apiFetch("/fees",{method:"POST",body:JSON.stringify({title:title.trim(),amount_due:amountDue,amount_paid:amountPaid,semester})});setDue("");setPaid("");await load();}catch(e:any){setMessage(e.message||"Could not save fee")}}
  async function remove(id:number){await apiFetch(`/fees/${id}`,{method:"DELETE"});await load()}
  return <Screen><Pressable onPress={()=>router.back()}><Text style={styles.back}>‹ Back</Text></Pressable><Text style={styles.title}>Fees & Payments</Text><Text style={styles.subtitle}>Personal tracker for your ISBAT University financial obligations.</Text>
    <Card style={styles.summary}><Text style={styles.label}>OUTSTANDING BALANCE</Text><Text style={styles.balance}>UGX {Number(data.balance||0).toLocaleString()}</Text><Text style={styles.meta}>Due: UGX {Number(data.total_due||0).toLocaleString()} · Paid: UGX {Number(data.total_paid||0).toLocaleString()}</Text></Card>
    <Card><Text style={styles.cardTitle}>Add fee item</Text><TextInput style={styles.input} value={title} onChangeText={setTitle} placeholder="Fee title" placeholderTextColor={colors.muted}/><TextInput style={styles.input} value={due} onChangeText={setDue} keyboardType="numeric" placeholder="Amount due (UGX)" placeholderTextColor={colors.muted}/><TextInput style={styles.input} value={paid} onChangeText={setPaid} keyboardType="numeric" placeholder="Amount already paid" placeholderTextColor={colors.muted}/><TextInput style={styles.input} value={semester} onChangeText={setSemester} placeholder="Semester" placeholderTextColor={colors.muted}/><Pressable style={styles.button} onPress={add}><Text style={styles.buttonText}>Save fee item</Text></Pressable>{!!message&&<Text style={styles.message}>{message}</Text>}</Card>
    <Text style={styles.section}>Tracked items</Text>{data.items?.map((i:any)=><Card key={i.id} style={styles.item}><Text style={styles.cardTitle}>{i.title}</Text><Text style={styles.meta}>UGX {Number(i.amount_paid).toLocaleString()} paid of UGX {Number(i.amount_due).toLocaleString()}</Text><Text style={styles.remaining}>Balance: UGX {Number(i.balance).toLocaleString()}</Text><Pressable onPress={()=>remove(i.id)}><Text style={styles.delete}>Remove</Text></Pressable></Card>)}{!data.items?.length&&<Text style={styles.meta}>No fee items saved yet.</Text>}
  </Screen>
}
const styles=StyleSheet.create({back:{color:colors.primary,fontWeight:"800",marginBottom:12},title:{color:colors.text,fontSize:28,fontWeight:"900"},subtitle:{color:colors.muted,marginTop:5,marginBottom:18,lineHeight:20},summary:{backgroundColor:colors.surface2,marginBottom:12},label:{color:colors.primary,fontSize:11,fontWeight:"900",letterSpacing:1.3},balance:{color:colors.text,fontSize:27,fontWeight:"900",marginTop:7},meta:{color:colors.muted,marginTop:5,lineHeight:19},cardTitle:{color:colors.text,fontSize:17,fontWeight:"800"},input:{backgroundColor:colors.background,color:colors.text,borderWidth:1,borderColor:colors.border,borderRadius:12,padding:13,marginTop:10},button:{backgroundColor:colors.primary,padding:14,borderRadius:13,alignItems:"center",marginTop:12},buttonText:{color:"#061426",fontWeight:"900"},message:{color:colors.danger,marginTop:10},section:{color:colors.text,fontSize:18,fontWeight:"800",marginVertical:15},item:{marginBottom:10},remaining:{color:colors.text,fontWeight:"800",marginTop:8},delete:{color:colors.danger,fontWeight:"800",marginTop:12}});
