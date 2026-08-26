import http from "./http";
import { consumeSse, type SseEventHandler } from "./sse";

export interface IncidentStreamPayload {
  title: string;
  content: string;
}

export interface IncidentSummary {
  id: number;
  knowledge_base_id: number;
  title: string;
  status: string;
  model_name: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface IncidentCitation {
  citation_index: number;
  document_chunk_id: number;
}

export interface IncidentDetail extends IncidentSummary {
  owner_id: number;
  input_content: string;
  result: string | null;
  error_message: string | null;
  citations: IncidentCitation[];
}

export interface IncidentListResponse {
  items: IncidentSummary[];
  total: number;
  page: number;
  page_size: number;
}

export function streamIncident(
  knowledgeBaseId: number,
  payload: IncidentStreamPayload,
  onEvent: SseEventHandler,
  signal: AbortSignal,
): Promise<void> {
  return consumeSse(
    `/api/v1/knowledge-bases/${knowledgeBaseId}/incidents/stream`,
    payload,
    onEvent,
    signal,
  );
}

export async function listIncidents(): Promise<IncidentListResponse> {
  const response = await http.get<IncidentListResponse>("/api/v1/incidents");

  return response.data;
}

export async function getIncident(incidentId: number): Promise<IncidentDetail> {
  const response = await http.get<IncidentDetail>(
    `/api/v1/incidents/${incidentId}`,
  );

  return response.data;
}

export async function deleteIncident(incidentId: number): Promise<void> {
  await http.delete(`/api/v1/incidents/${incidentId}`);
}
