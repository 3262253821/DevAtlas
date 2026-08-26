import http from "./http";

export interface DocumentVersionSummary {
  id: number;
  version_number: number;
  file_sha256: string;
  file_size: number;
  status: string;
  error_message: string | null;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentListItem {
  id: number;
  knowledge_base_id: number;
  filename: string;
  file_type: string;
  current_version: DocumentVersionSummary | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  items: DocumentListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface DocumentUploadResponse {
  id: number;
  knowledge_base_id: number;
  filename: string;
  file_type: string;
  file_size: number;
  status: string;
  version_number: number;
  chunk_count: number;
  duplicate: boolean;
  error_message: string | null;
  created_at: string;
}

export interface DocumentReindexResponse {
  document_id: number;
  version_id: number;
  version_number: number;
  status: string;
  chunk_count: number;
  error_message: string | null;
}

export async function listDocuments(
  knowledgeBaseId: number,
): Promise<DocumentListResponse> {
  const response = await http.get<DocumentListResponse>(
    `/api/v1/knowledge-bases/${knowledgeBaseId}/documents`,
  );

  return response.data;
}

export async function uploadDocument(
  knowledgeBaseId: number,
  file: File,
): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await http.post<DocumentUploadResponse>(
    `/api/v1/knowledge-bases/${knowledgeBaseId}/documents`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    },
  );

  return response.data;
}

export async function deleteDocument(
  knowledgeBaseId: number,
  documentId: number,
): Promise<void> {
  await http.delete(
    `/api/v1/knowledge-bases/${knowledgeBaseId}/documents/${documentId}`,
  );
}

export async function reindexDocument(
  knowledgeBaseId: number,
  documentId: number,
): Promise<DocumentReindexResponse> {
  const response = await http.post<DocumentReindexResponse>(
    `/api/v1/knowledge-bases/${knowledgeBaseId}/documents/${documentId}/reindex`,
  );

  return response.data;
}
