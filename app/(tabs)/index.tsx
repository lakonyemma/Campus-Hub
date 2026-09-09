import { Pressable, StyleSheet, Text, View } from "react-native";
import { Screen } from "@/src/components/Screen";
import { Card } from "@/src/components/Card";
import { colors } from "@/src/theme";
import { assignments, todayClasses } from "@/src/data/mock";
import { router } from "expo-router";

export default function HomeScreen() {
  return (
    <Screen>
      <Text style={styles.eyebrow}>CAMPUS HUB</Text>
      <Text style={styles.title}>Good evening, Lakony.</Text>
      <Text style={styles.subtitle}>Here is your academic picture for today.</Text>

      <Card style={styles.hero}>
        <Text style={styles.cardLabel}>NEXT CLASS</Text>
        <Text style={styles.heroTitle}>{todayClasses[0].unit}</Text>
        <Text style={styles.info}>{todayClasses[0].time} · {todayClasses[0].room}</Text>
      </Card>

      <Text style={styles.section}>Today</Text>
      {todayClasses.map((item) => (
        <Card key={item.time + item.unit} style={styles.item}>
          <View style={styles.row}>
            <Text style={styles.time}>{item.time}</Text>
            <View style={{ flex: 1 }}>
              <Text style={styles.itemTitle}>{item.unit}</Text>
              <Text style={styles.info}>{item.room}</Text>
            </View>
          </View>
        </Card>
      ))}

      <Text style={styles.section}>Assignments</Text>
      {assignments.map((item) => (
        <Card key={item.title} style={styles.item}>
          <Text style={styles.itemTitle}>{item.title}</Text>
          <Text style={styles.info}>{item.course} · Due {item.due}</Text>
          <View style={styles.progressTrack}>
            <View style={[styles.progress, { width: `${item.progress}%` }]} />
          </View>
          <Text style={styles.progressText}>{item.progress}% complete</Text>
        </Card>
      ))}

      <Pressable style={styles.smithButton} onPress={() => router.push("/(tabs)/smith")}>
        <Text style={styles.smithTitle}>Ask Smith</Text>
        <Text style={styles.smithSub}>Plan my evening, quiz me, or summarize my notes.</Text>
      </Pressable>
    </Screen>
  );
}

const styles = StyleSheet.create({
  eyebrow: { color: colors.primary, fontWeight: "800", letterSpacing: 2, fontSize: 12 },
  title: { color: colors.text, fontSize: 28, fontWeight: "800", marginTop: 8 },
  subtitle: { color: colors.muted, marginTop: 6, marginBottom: 18, fontSize: 15 },
  hero: { backgroundColor: colors.surface2, marginBottom: 20 },
  cardLabel: { color: colors.primary, fontSize: 11, fontWeight: "800", letterSpacing: 1.5 },
  heroTitle: { color: colors.text, fontSize: 22, fontWeight: "800", marginTop: 8 },
  info: { color: colors.muted, marginTop: 5 },
  section: { color: colors.text, fontSize: 18, fontWeight: "800", marginVertical: 12 },
  item: { marginBottom: 10 },
  row: { flexDirection: "row", alignItems: "center", gap: 16 },
  time: { color: colors.primary, fontWeight: "800", width: 54 },
  itemTitle: { color: colors.text, fontWeight: "700", fontSize: 16 },
  progressTrack: { height: 6, backgroundColor: colors.border, borderRadius: 99, marginTop: 14, overflow: "hidden" },
  progress: { height: "100%", backgroundColor: colors.primary, borderRadius: 99 },
  progressText: { color: colors.muted, fontSize: 12, marginTop: 7 },
  smithButton: { marginTop: 12, padding: 18, backgroundColor: colors.primary, borderRadius: 18 },
  smithTitle: { fontSize: 18, fontWeight: "900", color: "#061426" },
  smithSub: { color: "#0B2E4F", marginTop: 3 }
});
