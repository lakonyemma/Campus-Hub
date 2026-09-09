import * as Notifications from "expo-notifications";
import { Platform } from "react-native";

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldPlaySound: true,
    shouldSetBadge: false,
    shouldShowBanner: true,
    shouldShowList: true
  })
});

export async function prepareNotifications() {
  const permissions = await Notifications.requestPermissionsAsync();
  if (permissions.status !== "granted") return false;
  if (Platform.OS === "android") {
    await Notifications.setNotificationChannelAsync("academic", {
      name: "Academic reminders",
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 150, 250],
      sound: "default"
    });
  }
  return true;
}

export async function scheduleAcademicReminder(title: string, body: string, when: Date, data: Record<string, any> = {}) {
  if (when.getTime() <= Date.now()) return null;
  return Notifications.scheduleNotificationAsync({
    content: { title, body, sound: "default", data },
    trigger: { type: Notifications.SchedulableTriggerInputTypes.DATE, date: when, channelId: Platform.OS === "android" ? "academic" : undefined }
  });
}

function nextClassDate(weekday:number,time:string){
  const now=new Date(); const [hour,minute]=time.split(":").map(Number); const jsTarget=(weekday+1)%7;
  const result=new Date(now); let delta=(jsTarget-now.getDay()+7)%7; result.setDate(now.getDate()+delta); result.setHours(hour,minute,0,0);
  if(result.getTime()<=now.getTime()){result.setDate(result.getDate()+7)}
  return result;
}

export async function scheduleAcademicReminders(timetable:any[],assignments:any[],exams:any[]){
  const allowed=await prepareNotifications(); if(!allowed)return;
  await Notifications.cancelAllScheduledNotificationsAsync();
  for(const c of timetable.slice(0,30)){
    const classTime=nextClassDate(c.weekday,c.start_time); const remindAt=new Date(classTime.getTime()-15*60*1000);
    await scheduleAcademicReminder("Class in 15 minutes",`${c.course}${c.room?` · ${c.room}`:""}`,remindAt,{type:"class",id:c.id});
  }
  for(const a of assignments.filter((x:any)=>x.due_at&&x.status!=="completed").slice(0,20)){
    const due=new Date(a.due_at); const remindAt=new Date(due.getTime()-24*60*60*1000);
    await scheduleAcademicReminder("Assignment due tomorrow",`${a.title} · ${a.course}`,remindAt,{type:"assignment",id:a.id});
  }
  for(const e of exams.filter((x:any)=>x.exam_at).slice(0,20)){
    const exam=new Date(e.exam_at); const remindAt=new Date(exam.getTime()-24*60*60*1000);
    await scheduleAcademicReminder("Exam tomorrow",`${e.course}${e.room?` · ${e.room}`:""}`,remindAt,{type:"exam",id:e.id});
  }
}

export async function cancelAcademicReminder(id: string) {
  await Notifications.cancelScheduledNotificationAsync(id);
}
