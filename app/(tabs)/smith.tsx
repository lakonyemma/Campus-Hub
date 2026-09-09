import { useState } from "react";
import { KeyboardAvoidingView, Platform, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { Screen } from "@/src/components/Screen";
import { colors } from "@/src/theme";
import { askSmith } from "@/src/services/assistant";

const modes = ["normal", "tutor", "exam", "planner", "focus"] as const;

export default function SmithScreen() {
  const [mode, setMode] = useState<(typeof modes)[number]>("normal");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Good evening. What do you want to work on?" }
  ]);
  const [busy, setBusy] = useState(false);

  async function send() {
    const message = input.trim();
    if (!message || busy) return;
    setMessages(prev => [...prev, { role: "user", text: message }]);
    setInput("");
    setBusy(true);
    try {
      const reply = await askSmith({ mode, message });
      setMessages(prev => [...prev, { role: "assistant", text: reply }]);
    } catch (e: any) {
      setMessages(prev => [...prev, { role: "assistant", text: e.message || "Something went wrong." }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Screen contentStyle={{ flexGrow: 1 }}>
      <Text style={styles.title}>Smith</Text>
      <Text style={styles.subtitle}>Your academic assistant.</Text>

      <View style={styles.modes}>
        {modes.map(m => (
          <Pressable key={m} onPress={() => setMode(m)} style={[styles.mode, mode === m && styles.modeActive]}>
            <Text style={[styles.modeText, mode === m && styles.modeTextActive]}>{m}</Text>
          </Pressable>
        ))}
      </View>

      <View style={styles.chat}>
        {messages.map((m, i) => (
          <View key={i} style={[styles.bubble, m.role === "user" ? styles.userBubble : styles.aiBubble]}>
            <Text style={m.role === "user" ? styles.userText : styles.aiText}>{m.text}</Text>
          </View>
        ))}
        {busy && <Text style={styles.thinking}>Smith is working…</Text>}
      </View>

      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined}>
        <View style={styles.inputRow}>
          <TextInput
            value={input}
            onChangeText={setInput}
            placeholder="Ask Smith..."
            placeholderTextColor={colors.muted}
            style={styles.input}
            onSubmitEditing={send}
          />
          <Pressable style={styles.send} onPress={send}><Text style={styles.sendText}>↑</Text></Pressable>
        </View>
      </KeyboardAvoidingView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { color: colors.text, fontSize: 28, fontWeight: "800" },
  subtitle: { color: colors.muted, marginTop: 4 },
  modes: { flexDirection: "row", flexWrap: "wrap", gap: 7, marginVertical: 16 },
  mode: { paddingHorizontal: 11, paddingVertical: 8, backgroundColor: colors.surface, borderRadius: 99 },
  modeActive: { backgroundColor: colors.primary },
  modeText: { color: colors.muted, textTransform: "capitalize", fontWeight: "700", fontSize: 12 },
  modeTextActive: { color: "#061426" },
  chat: { gap: 10, marginBottom: 14 },
  bubble: { padding: 13, borderRadius: 16, maxWidth: "88%" },
  aiBubble: { backgroundColor: colors.surface, alignSelf: "flex-start" },
  userBubble: { backgroundColor: colors.primary, alignSelf: "flex-end" },
  aiText: { color: colors.text, lineHeight: 20 },
  userText: { color: "#061426", lineHeight: 20, fontWeight: "600" },
  thinking: { color: colors.muted, fontSize: 12 },
  inputRow: { flexDirection: "row", gap: 9, alignItems: "center" },
  input: { flex: 1, backgroundColor: colors.surface, color: colors.text, padding: 14, borderRadius: 16, borderWidth: 1, borderColor: colors.border },
  send: { width: 48, height: 48, borderRadius: 16, backgroundColor: colors.primary, alignItems: "center", justifyContent: "center" },
  sendText: { color: "#061426", fontSize: 24, fontWeight: "900" }
});
