import { apiFetch } from "@/src/services/api";
export type AssistantContext={mode:"normal"|"tutor"|"exam"|"planner"|"focus";message:string;documentId?:string};
export async function askSmith(input:AssistantContext):Promise<string>{const data=await apiFetch("/assistant/chat",{method:"POST",body:JSON.stringify(input)});return data.reply;}
