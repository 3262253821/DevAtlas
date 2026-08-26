<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { isAxiosError } from "axios";
import { ElMessage, ElMessageBox } from "element-plus";
import { useRoute, useRouter } from "vue-router";
import {
  deleteDocument,
  listDocuments,
  reindexDocument,
  uploadDocument,
  type DocumentListItem,
} from "../api/documents";

const route = useRoute();
const router = useRouter();

const documents = ref<DocumentListItem[]>([]);
const loading = ref(false);
const uploading = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);

const knowledgeBaseId = computed(() => {
  return Number(route.params.id);
});

function getErrorMessage(error: unknown): string {
  if (isAxiosError<{ detail?: string }>(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }
  }

  return "操作失败，请稍后重试";
}

function statusType(status: string): "success" | "warning" | "danger" | "info" {
  if (status === "indexed") {
    return "success";
  }

  if (status === "failed") {
    return "danger";
  }

  if (status === "pending") {
    return "warning";
  }

  return "info";
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString("zh-CN");
}

async function loadDocuments(): Promise<void> {
  if (!Number.isInteger(knowledgeBaseId.value)) {
    await router.replace("/workspaces");
    return;
  }

  loading.value = true;

  try {
    const result = await listDocuments(knowledgeBaseId.value);

    documents.value = result.items;
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    loading.value = false;
  }
}

function chooseFile(): void {
  fileInput.value?.click();
}

async function handleFileChange(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];

  if (!file) {
    return;
  }

  uploading.value = true;

  try {
    const result = await uploadDocument(knowledgeBaseId.value, file);

    if (result.duplicate) {
      ElMessage.info("文件内容未变化，未创建新版本");
    } else {
      ElMessage.success("文档上传并处理完成");
    }

    await loadDocuments();
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    uploading.value = false;
    input.value = "";
  }
}

async function removeDocument(document: DocumentListItem): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `确定删除“${document.filename}”吗？`,
      "删除确认",
      {
        type: "warning",
        confirmButtonText: "删除",
        cancelButtonText: "取消",
      },
    );

    await deleteDocument(knowledgeBaseId.value, document.id);

    documents.value = documents.value.filter((item) => item.id !== document.id);

    ElMessage.success("文档已删除");
  } catch (error) {
    if (isAxiosError(error)) {
      ElMessage.error(getErrorMessage(error));
    }
  }
}

async function reindex(document: DocumentListItem): Promise<void> {
  try {
    await reindexDocument(knowledgeBaseId.value, document.id);

    ElMessage.success("重新索引完成");
    await loadDocuments();
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

onMounted(loadDocuments);
</script>

<template>
  <main v-loading="loading" class="documents-page">
    <header class="page-header">
      <div>
        <el-button
          class="page-back-button"
          @click="
            router.push({
              name: 'knowledge',
              params: { id: knowledgeBaseId },
            })
          "
        >
          ← 返回工作台
        </el-button>

        <h1>文档管理</h1>
        <p>支持 TXT、Markdown 和 PDF 文件。</p>
      </div>

      <div>
        <input
          ref="fileInput"
          type="file"
          accept=".txt,.md,.pdf"
          hidden
          @change="handleFileChange"
        />

        <el-button type="primary" :loading="uploading" @click="chooseFile">
          上传文档
        </el-button>
      </div>
    </header>

    <el-card class="documents-card">
      <el-empty
        v-if="!loading && documents.length === 0"
        description="当前知识库还没有文档"
      />

      <el-table v-else :data="documents" row-key="id">
        <el-table-column prop="filename" label="文件名" min-width="260" />

        <el-table-column label="当前版本" width="110">
          <template #default="{ row }">
            {{
              row.current_version
                ? `v${row.current_version.version_number}`
                : "-"
            }}
          </template>
        </el-table-column>

        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag
              :type="statusType(row.current_version?.status || 'unknown')"
            >
              {{ row.current_version?.status || "unknown" }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="切片数" width="100">
          <template #default="{ row }">
            {{ row.current_version?.chunk_count ?? 0 }}
          </template>
        </el-table-column>

        <el-table-column label="更新时间" width="190">
          <template #default="{ row }">
            {{ formatDate(row.updated_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.current_version?.status === 'failed'"
              link
              type="warning"
              @click="reindex(row)"
            >
              重新索引
            </el-button>

            <el-button link type="danger" @click="removeDocument(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </main>
</template>

<style scoped>
.documents-page {
  min-height: 100vh;
  padding: 46px 44px 84px;
  background: var(--paper);
  box-sizing: border-box;
}

.page-header {
  max-width: 1160px;
  margin: 0 auto 26px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.page-header h1 {
  margin: 22px 0 8px;
  color: var(--ink-950);
  font-size: clamp(30px, 4vw, 46px);
  letter-spacing: -0.04em;
}

.page-header p {
  color: var(--ink-500);
  font-size: 14px;
}

.documents-card {
  max-width: 1160px;
  margin: 0 auto;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow-card);
}

.documents-card :deep(.el-card__body) {
  padding: 0;
}

.documents-card :deep(.el-table) {
  --el-table-header-bg-color: #f5f1e8;
  --el-table-row-hover-bg-color: #f1f8f5;
  --el-table-border-color: var(--line);
  color: var(--ink-700);
}

.documents-card :deep(.el-table th.el-table__cell) {
  color: var(--ink-500);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.documents-card :deep(.el-table td.el-table__cell),
.documents-card :deep(.el-table th.el-table__cell) {
  padding: 17px 14px;
}

.documents-card :deep(.el-empty) {
  padding: 88px 24px;
}

.documents-page :deep(.el-button--primary) {
  min-height: 42px;
  padding: 0 20px;
  border: 0;
  border-radius: 8px;
  color: var(--ink-950);
  background: var(--teal);
  font-weight: 700;
}

.documents-page :deep(.el-button--primary:hover) {
  background: #2aaf99;
}

.documents-page :deep(.el-button.is-link) {
  padding: 0;
  color: var(--ink-500);
}

@media (max-width: 760px) {
  .documents-page {
    padding: 34px 16px 60px;
  }

  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .page-header > div:last-child,
  .page-header > div:last-child :deep(.el-button) {
    width: 100%;
  }
}
</style>
