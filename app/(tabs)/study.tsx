import { useState } from "react";
import { Pressable, StyleSheet, Text } from "react-native";
import * as DocumentPicker from "expo-document-picker";
import { Screen } from "@/src/components/Screen";
import { Card } from "@/src/components/Card";
import { colors } from "@/src/theme";

export default function StudyScreen() {
  const [fileName, setFileName] = useState<string | null>(null);

  async function pickPdf() {
    const result = await DocumentPicker.getDocumentAsync({
      type: "application/pdf",
      copyToCacheDirectory: true
    });
    if (!result.canceled && result.assets[0]) {
      setFileName(result.assets[0].name);
    }
  }

  return (
    <Screen>
      <Text style={styles.title}>Study</Text>
      <Text style={styles.subtitle}>Your notes, PDFs and revision workspace.</Text>

      <Card>
        <Text style={styles.cardTitle}>PDF Notes</Text>
        <Text style={styles.body}>
          Upload lecture notes. Smith will summarize them, extract key concepts and build quizzes.
        </Text>
        <Pressable style={styles.button} onPress={pickPdf}>
          <Text style={styles.buttonText}>Choose PDF</Text>
        </Pressable>
        {fileName && <Text style={styles.selected}>Selected: {fileName}</Text>}
      </Card>

      <Card style={{ marginTop: 12 }}>
        <Text style={styles.cardTitle}>Revision tools</Text>
        <Text style={styles.body}>Summary · Flashcards · Quiz · Key definitions · Exam questions</Text>
      </Card>
    </Screen>
  );
}
const styles = StyleSheet.create({
  title: { color: colors.text, fontSize: 28, fontWeight: "800" },
  subtitle: { color: colors.muted, marginTop: 5, marginBottom: 18 },
  cardTitle: { color: colors.text, fontSize: 18, fontWeight: "800" },
  body: { color: colors.muted, lineHeight: 21, marginTop: 7 },
  button: { backgroundColor: colors.primary, padding: 14, borderRadius: 13, marginTop: 16, alignItems: "center" },
  buttonText: { color: "#061426", fontWeight: "900" },
  selected: { color: colors.success, marginTop: 12 }
});
