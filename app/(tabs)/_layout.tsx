import { Tabs } from "expo-router";
import { Text } from "react-native";
import { colors } from "@/src/theme";

const Icon = ({ children, color }: { children: string; color: string }) => (
  <Text style={{ fontSize: 17, color }}>{children}</Text>
);

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.border,
          height: 66,
          paddingBottom: 8
        },
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.muted
      }}
    >
      <Tabs.Screen
        name="index"
        options={{ title: "Home", tabBarIcon: ({ color }) => <Icon color={color}>⌂</Icon> }}
      />
      <Tabs.Screen
        name="schedule"
        options={{ title: "Schedule", tabBarIcon: ({ color }) => <Icon color={color}>▣</Icon> }}
      />
      <Tabs.Screen
        name="study"
        options={{ title: "Study", tabBarIcon: ({ color }) => <Icon color={color}>▤</Icon> }}
      />
      <Tabs.Screen
        name="smith"
        options={{ title: "Smith", tabBarIcon: ({ color }) => <Icon color={color}>✦</Icon> }}
      />
      <Tabs.Screen
        name="profile"
        options={{ title: "Profile", tabBarIcon: ({ color }) => <Icon color={color}>●</Icon> }}
      />
    </Tabs>
  );
}
