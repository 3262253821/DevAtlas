<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { isAxiosError } from "axios";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";
import {
  getKnowledgeBase,
  type KnowledgeBasePublic,
} from "../api/knowledgeBase";
import {
  listDocuments,
  type DocumentListItem,
} from "../api/documents";

const route = useRoute();
const router = useRouter();

const workspace = ref<KnowledgeBasePublic | null>(null);
const loading = ref(false);
const documents = ref<DocumentListItem[]>([]);
const documentsLoading = ref(false);

const knowledgeBaseId = computed(() => {
  return Number(route.params.id);
});

const documentCount = computed(() => documents.value.length);
const indexedCount = computed(
  () =>
    documents.value.filter(
      (document) => document.current_version?.status === "indexed",
    ).length,
);
const attentionCount = computed(
  () =>
    documents.value.filter((document) => {
      const status = document.current_version?.status;
      return status === "pending" || status === "failed";
    }).length,
);
const recentDocuments = computed(() => {
  return [...documents.value]
    .sort(
      (left, right) =>
        new Date(right.updated_at).getTime() -
        new Date(left.updated_at).getTime(),
    )
    .slice(0, 4);
});

function errorMessage(error: unknown): string {
  if (isAxiosError<{ detail?: string }>(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }
  }

  return "知识库加载失败";
}

async function loadWorkspace(): Promise<void> {
  if (!Number.isInteger(knowledgeBaseId.value)) {
    await router.replace("/workspaces");
    return;
  }

  loading.value = true;

  try {
    workspace.value = await getKnowledgeBase(knowledgeBaseId.value);
  } catch (error) {
    ElMessage.error(errorMessage(error));
    await router.replace("/workspaces");
  } finally {
    loading.value = false;
  }
}

async function loadDocuments(): Promise<void> {
  documentsLoading.value = true;

  try {
    const result = await listDocuments(knowledgeBaseId.value);
    documents.value = result.items;
  } catch (error) {
    ElMessage.warning(errorMessage(error));
  } finally {
    documentsLoading.value = false;
  }
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString("zh-CN");
}

function statusLabel(status: string | undefined): string {
  if (status === "indexed") {
    return "已索引";
  }

  if (status === "pending") {
    return "处理中";
  }

  if (status === "failed") {
    return "需处理";
  }

  return "未索引";
}

function statusType(
  status: string | undefined,
): "success" | "warning" | "danger" | "info" {
  if (status === "indexed") {
    return "success";
  }

  if (status === "pending") {
    return "warning";
  }

  if (status === "failed") {
    return "danger";
  }

  return "info";
}

async function initialize(): Promise<void> {
  await loadWorkspace();

  if (workspace.value) {
    await loadDocuments();
  }
}

onMounted(initialize);
</script>

<template>
  <main v-loading="loading" class="workspace-detail-page">
    <header class="detail-header">
      <el-button class="page-back-button" @click="router.push('/workspaces')">
        ← 返回知识库列表
      </el-button>

      <div v-if="workspace">
        <p class="eyebrow">Knowledge Workspace</p>
        <h1>{{ workspace.name }}</h1>
        <p class="description">
          {{ workspace.description || "暂无描述" }}
        </p>
      </div>
    </header>

    <section v-if="workspace" class="workspace-summary" aria-label="知识库概览">
      <article class="summary-stat">
        <span>文档总数</span>
        <strong>{{ documentCount }}</strong>
        <small>已纳入当前知识库</small>
      </article>

      <article class="summary-stat summary-stat--accent">
        <span>已完成索引</span>
        <strong>{{ indexedCount }}</strong>
        <small>可用于 RAG 检索</small>
      </article>

      <article class="summary-stat">
        <span>需要关注</span>
        <strong>{{ attentionCount }}</strong>
        <small>{{ attentionCount ? "存在待处理文档" : "当前状态正常" }}</small>
      </article>
    </section>

    <section v-if="workspace" class="workspace-content-grid">
      <section class="feature-section">
        <div class="section-heading">
          <div>
            <p class="section-kicker">WORKSPACE TOOLS</p>
            <h2>继续工作</h2>
          </div>
          <span class="section-note">选择一项操作开始</span>
        </div>

        <div class="feature-grid">
          <el-card class="feature-card">
            <span class="feature-index">01 / DOCUMENTS</span>
            <h3>文档管理</h3>
            <p>上传、解析和查看知识库文档状态。</p>

            <el-button
              type="primary"
              @click="
                router.push({
                  name: 'documents',
                  params: { id: workspace.id },
                })
              "
            >
              打开文档管理
            </el-button>
          </el-card>

          <el-card class="feature-card feature-card--primary">
            <span class="feature-index">02 / ASK</span>
            <h3>知识库问答</h3>
            <p>基于已索引文档进行 RAG 检索和流式回答。</p>

            <el-button
              type="primary"
              @click="
                router.push({
                  name: 'qa',
                  params: { id: workspace.id },
                })
              "
            >
              开始问答
            </el-button>
          </el-card>

          <el-card class="feature-card feature-card--warm">
            <span class="feature-index">03 / INCIDENTS</span>
            <h3>故障分析</h3>
            <p>结合研发知识生成原因和排查步骤。</p>

            <el-button
              type="primary"
              @click="
                router.push({
                  name: 'incident-new',
                  params: { id: workspace.id },
                })
              "
            >
              创建分析
            </el-button>
          </el-card>
        </div>
      </section>

      <aside v-loading="documentsLoading" class="recent-documents-panel">
        <div class="section-heading">
          <div>
            <p class="section-kicker">RECENT ACTIVITY</p>
            <h2>最近文档</h2>
          </div>
          <el-button
            link
            @click="router.push({ name: 'documents', params: { id: workspace.id } })"
          >
            查看全部
          </el-button>
        </div>

        <el-empty
          v-if="!documentsLoading && recentDocuments.length === 0"
          description="上传第一份研发文档"
        />

        <button
          v-for="document in recentDocuments"
          :key="document.id"
          class="recent-document"
          type="button"
          @click="router.push({ name: 'documents', params: { id: workspace?.id } })"
        >
          <span class="document-type">{{ document.file_type.toUpperCase() }}</span>
          <span class="document-copy">
            <strong>{{ document.filename }}</strong>
            <small>{{ formatDate(document.updated_at) }}</small>
          </span>
          <el-tag
            size="small"
            :type="statusType(document.current_version?.status)"
          >
            {{ statusLabel(document.current_version?.status) }}
          </el-tag>
        </button>
      </aside>
    </section>
  </main>
</template>

<style scoped>
.workspace-detail-page {
  min-height: 100vh;
  padding: 46px 44px 84px;
  background: var(--paper);
  box-sizing: border-box;
}

.detail-header {
  max-width: 1160px;
  margin: 0 auto 24px;
  padding: 28px 32px 32px;
  border-radius: var(--radius);
  color: #f7f3e9;
  background: var(--ink-900);
  box-shadow: var(--shadow-soft);
}

.eyebrow {
  margin: 32px 0 8px;
  color: #8ed8c9;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
}

.detail-header h1 {
  margin: 0 0 8px;
  color: #f7f3e9;
  font-size: clamp(32px, 4vw, 52px);
  letter-spacing: -0.04em;
}

.description {
  margin: 0;
  color: #aeb8c7;
  font-size: 14px;
}

.workspace-summary {
  max-width: 1160px;
  margin: 0 auto 28px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.summary-stat {
  min-height: 108px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 17px 20px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow-card);
}

.summary-stat--accent {
  border-color: rgba(31, 157, 135, 0.3);
  background: #eef8f5;
}

.summary-stat span,
.summary-stat small {
  color: var(--ink-500);
  font-size: 12px;
}

.summary-stat strong {
  color: var(--ink-950);
  font-size: 25px;
  font-weight: 750;
}

.workspace-content-grid {
  max-width: 1160px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(280px, 0.7fr);
  align-items: stretch;
  gap: 22px;
}

.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}

.section-kicker {
  margin: 0 0 5px;
  color: var(--teal-dark);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 10px;
  letter-spacing: 0.14em;
}

.section-heading h2 {
  margin: 0;
  color: var(--ink-950);
  font-size: 19px;
  letter-spacing: -0.02em;
}

.section-note {
  color: var(--ink-500);
  font-size: 12px;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.feature-card {
  display: flex;
  flex-direction: column;
  min-height: 210px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  transition: transform 180ms ease, box-shadow 180ms ease;
}

.feature-card--primary {
  border-color: rgba(31, 157, 135, 0.34);
  background: #f2faf7;
}

.feature-card--warm {
  border-color: rgba(213, 138, 53, 0.3);
  background: #fffaf2;
}

.feature-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-soft);
}

.feature-card :deep(.el-card__body) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.feature-index {
  margin-bottom: 15px;
  color: var(--teal-dark);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 10px;
  letter-spacing: 0.12em;
}

.feature-grid h3 {
  margin: 0 0 10px;
  color: var(--ink-950);
  font-size: 20px;
}

.feature-grid p {
  min-height: 48px;
  margin-bottom: 20px;
  color: var(--ink-500);
  font-size: 14px;
  line-height: 1.7;
}

.feature-card :deep(.el-button) {
  align-self: flex-start;
  margin-top: auto;
  border: 0;
  border-radius: 8px;
  color: var(--ink-950);
  background: var(--teal);
  font-weight: 700;
}

.feature-card :deep(.el-button:hover) {
  background: #2aaf99;
}

.recent-documents-panel {
  min-width: 0;
  height: calc(100% - 54px);
  margin-top: 54px;
  box-sizing: border-box;
  padding: 20px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.76);
  box-shadow: var(--shadow-card);
}

.recent-documents-panel :deep(.el-button.is-link) {
  padding: 0;
  color: var(--teal-dark);
  font-size: 12px;
}

.recent-document {
  width: 100%;
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 12px 0;
  border: 0;
  border-top: 1px solid var(--line);
  color: inherit;
  text-align: left;
  background: transparent;
  cursor: pointer;
}

.recent-document:first-of-type {
  border-top: 0;
}

.recent-document:hover .document-copy strong,
.recent-document:focus-visible .document-copy strong {
  color: var(--teal-dark);
}

.recent-document:focus-visible {
  outline: 2px solid rgba(31, 157, 135, 0.35);
  outline-offset: 3px;
}

.document-type {
  color: var(--teal-dark);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 10px;
}

.document-copy {
  min-width: 0;
}

.document-copy strong,
.document-copy small {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.document-copy strong {
  color: var(--ink-900);
  font-size: 12px;
  font-weight: 650;
}

.document-copy small {
  margin-top: 4px;
  color: var(--ink-500);
  font-size: 11px;
}

.recent-document :deep(.el-tag) {
  border-radius: 999px;
  font-size: 10px;
}

.workspace-detail-page :deep(.el-button.is-link) {
  padding: 0;
  color: #aeb8c7;
}

.workspace-detail-page :deep(.el-button.is-link:hover) {
  color: #8ed8c9;
}

@media (max-width: 800px) {
  .workspace-detail-page {
    padding: 28px 16px 60px;
  }

  .detail-header {
    padding: 24px 20px 26px;
  }

  .feature-grid {
    grid-template-columns: 1fr;
  }

  .workspace-summary,
  .workspace-content-grid {
    grid-template-columns: 1fr;
  }

  .recent-documents-panel {
    height: auto;
    margin-top: 4px;
  }
}
</style>
