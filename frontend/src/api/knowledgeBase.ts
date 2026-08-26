import http from "./http";

export interface KnowledgeBasePublic {
  id: number;
  owner_id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeBaseCreate {
  name: string;
  description?: string;
}

export async function listKnowledgeBases(): Promise<KnowledgeBasePublic[]> {
  const response = await http.get<KnowledgeBasePublic[]>(
    "/api/v1/knowledge-bases",
  );

  return response.data;
}

export async function createKnowledgeBase(
  payload: KnowledgeBaseCreate,
): Promise<KnowledgeBasePublic> {
  const response = await http.post<KnowledgeBasePublic>(
    "/api/v1/knowledge-bases",
    payload,
  );

  return response.data;
}

export async function getKnowledgeBase(
  knowledgeBaseId: number,
): Promise<KnowledgeBasePublic> {
  const response = await http.get<KnowledgeBasePublic>(
    `/api/v1/knowledge-bases/${knowledgeBaseId}`,
  );

  return response.data;
}

export async function deleteKnowledgeBase(
  knowledgeBaseId: number,
): Promise<void> {
  await http.delete(`/api/v1/knowledge-bases/${knowledgeBaseId}`);
}
