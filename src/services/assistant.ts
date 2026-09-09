const API_URL = process.env.EXPO_PUBLIC_API_URL;

export type AssistantContext = {
  mode: "normal" | "tutor" | "exam" | "planner" | "focus";
  message: string;
  documentId?: string;
};

export async function askSmith(input: AssistantContext): Promise<string> {
  if (!API_URL) {
    return localDemoReply(input.message);
  }

  const response = await fetch(`${API_URL}/assistant/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input)
  });

  if (!response.ok) throw new Error("Smith is unavailable right now.");
  const data = await response.json();
  return data.reply;
}

function localDemoReply(message: string) {
  const lower = message.toLowerCase();
  if (lower.includes("plan")) {
    return "You have one unfinished assignment and three classes today. I would reserve your first free evening block for the UWP assignment, then use a shorter block for revision.";
  }
  if (lower.includes("pdf") || lower.includes("summar")) {
    return "Open Study, choose a PDF, then ask me for a full summary, chapter summary, flashcards, definitions, or exam questions.";
  }
  return "I am ready. Ask about your timetable, assignments, revision plan, exams, or lecture notes.";
}
