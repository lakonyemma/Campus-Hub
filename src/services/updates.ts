import * as Updates from "expo-updates";

export async function checkForAppUpdate() {
  if (__DEV__) {
    return { updated: false, message: "Update checks run in installed builds." };
  }

  const result = await Updates.checkForUpdateAsync();
  if (!result.isAvailable) {
    return { updated: false, message: "Campus Hub is up to date." };
  }

  await Updates.fetchUpdateAsync();
  return { updated: true, message: "Update downloaded. Restart Campus Hub to apply it." };
}

export async function applyDownloadedUpdate() {
  await Updates.reloadAsync();
}
