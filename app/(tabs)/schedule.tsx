import { StyleSheet, Text, View } from "react-native";
import { Screen } from "@/src/components/Screen";
import { Card } from "@/src/components/Card";
import { colors } from "@/src/theme";
import { todayClasses } from "@/src/data/mock";

export default function ScheduleScreen() {
  return (
    <Screen>
      <Text style={styles.title}>Schedule</Text>
      <Text style={styles.subtitle}>Classes, exams and study sessions.</Text>

      <View style={styles.days}>
        {["MON","TUE","WED","THU","FRI"].map((day, i) => (
          <View key={day} style={[styles.day, i === 2 && styles.activeDay]}>
            <Text style={[styles.dayText, i === 2 && styles.activeText]}>{day}</Text>
          </View>
        ))}
      </View>

      {todayClasses.map(c => (
        <Card key={c.time+c.unit} style={styles.card}>
          <Text style={styles.time}>{c.time}</Text>
          <Text style={styles.unit}>{c.unit}</Text>
          <Text style={styles.room}>{c.room}</Text>
        </Card>
      ))}
    </Screen>
  );
}
const styles = StyleSheet.create({
  title: { color: colors.text, fontSize: 28, fontWeight: "800" },
  subtitle: { color: colors.muted, marginTop: 5, marginBottom: 18 },
  days: { flexDirection: "row", gap: 8, marginBottom: 18 },
  day: { flex: 1, paddingVertical: 10, borderRadius: 12, backgroundColor: colors.surface, alignItems: "center" },
  activeDay: { backgroundColor: colors.primary },
  dayText: { color: colors.muted, fontSize: 11, fontWeight: "800" },
  activeText: { color: "#061426" },
  card: { marginBottom: 10 },
  time: { color: colors.primary, fontWeight: "800" },
  unit: { color: colors.text, fontWeight: "800", fontSize: 17, marginTop: 5 },
  room: { color: colors.muted, marginTop: 4 }
});
