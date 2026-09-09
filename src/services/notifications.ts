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

export async function cancelAcademicReminder(id: string) {
  await Notifications.cancelScheduledNotificationAsync(id);
}
