import { consumeSse, type SseEventHandler } from "./sse";

export interface QaStreamPayload {
  question: string;
  top_k: number;
  conversation_id: number | null;
}

export function streamQuestion(
  knowledgeBaseId: number,
  payload: QaStreamPayload,
  onEvent: SseEventHandler,
  signal: AbortSignal,
): Promise<void> {
  return consumeSse(
    `/api/v1/knowledge-bases/${knowledgeBaseId}/qa/stream`,
    payload,
    onEvent,
    signal,
  );
}
