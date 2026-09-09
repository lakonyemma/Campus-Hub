import { useState } from "react";
import { Pressable, StyleSheet, Text } from "react-native";
import { Screen } from "@/src/components/Screen";
import { Card } from "@/src/components/Card";
import { colors } from "@/src/theme";
import { applyDownloadedUpdate, checkForAppUpdate } from "@/src/services/updates";

export default function ProfileScreen() {
  const [message, setMessage] = useState("");
  const [ready, setReady] = useState(false);

  async function checkUpdate() {
    try {
      const result = await checkForAppUpdate();
      setReady(result.updated);
      setMessage(result.message);
    } catch {
      setMessage("Update check failed. Try again when connected to the internet.");
    }
  }

  return (
    <Screen>
      <Text style={styles.title}>Profile</Text>
      <Text style={styles.subtitle}>Account, preferences and Campus Hub updates.</Text>

      <Card>
        <Text style={styles.name}>Lakony Emmanuel</Text>
        <Text style={styles.meta}>Student profile</Text>
      </Card>

      <Card style={{ marginTop: 12 }}>
        <Text style={styles.cardTitle}>App updates</Text>
        <Text style={styles.meta}>Campus Hub checks for compatible updates when it opens.</Text>
        <Pressable style={styles.button} onPress={checkUpdate}>
          <Text style={styles.buttonText}>Check for updates</Text>
        </Pressable>
        {!!message && <Text style={styles.message}>{message}</Text>}
        {ready && (
          <Pressable style={styles.secondary} onPress={applyDownloadedUpdate}>
            <Text style={styles.secondaryText}>Restart and update</Text>
          </Pressable>
        )}
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { color: colors.text, fontSize: 28, fontWeight: "800" },
  subtitle: { color: colors.muted, marginTop: 5, marginBottom: 18 },
  name: { color: colors.text, fontSize: 18, fontWeight: "800" },
  meta: { color: colors.muted, marginTop: 5, lineHeight: 20 },
  cardTitle: { color: colors.text, fontSize: 17, fontWeight: "800" },
  button: { backgroundColor: colors.primary, padding: 14, borderRadius: 13, alignItems: "center", marginTop: 15 },
  buttonText: { color: "#061426", fontWeight: "900" },
  message: { color: colors.text, marginTop: 12 },
  secondary: { padding: 14, borderRadius: 13, borderWidth: 1, borderColor: colors.primary, alignItems: "center", marginTop: 10 },
  secondaryText: { color: colors.primary, fontWeight: "800" }
});
