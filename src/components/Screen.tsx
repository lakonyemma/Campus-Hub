import React from "react";
import { SafeAreaView, ScrollView, StyleSheet, ViewStyle } from "react-native";
import { colors } from "@/src/theme";

export function Screen({
  children,
  scroll = true,
  contentStyle
}: {
  children: React.ReactNode;
  scroll?: boolean;
  contentStyle?: ViewStyle;
}) {
  if (!scroll) {
    return <SafeAreaView style={[styles.safe, contentStyle]}>{children}</SafeAreaView>;
  }
  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={[styles.content, contentStyle]}>{children}</ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.background },
  content: { padding: 18, paddingBottom: 40 }
});
