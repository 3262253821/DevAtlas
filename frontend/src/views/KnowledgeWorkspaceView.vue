<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { isAxiosError } from "axios";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";
import {
  getKnowledgeBase,
  type KnowledgeBasePublic,
} from "../api/knowledgeBase";

const route = useRoute();
const router = useRouter();

const workspace = ref<KnowledgeBasePublic | null>(null);
const loading = ref(false);

const knowledgeBaseId = computed(() => {
  return Number(route.params.id);
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

onMounted(loadWorkspace);
</script>

<template>
  <main v-loading="loading" class="workspace-detail-page">
    <header class="detail-header">
      <el-button link @click="router.push('/workspaces')">
        返回知识库列表
      </el-button>

      <div v-if="workspace">
        <p class="eyebrow">Knowledge Workspace</p>
        <h1>{{ workspace.name }}</h1>
        <p class="description">
          {{ workspace.description || "暂无描述" }}
        </p>
      </div>
    </header>

    <section v-if="workspace" class="feature-grid">
      <el-card class="feature-card">
        <h2>文档管理</h2>
        <p>上传、解析和查看知识库文档。</p>

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

      <el-card class="feature-card">
        <h2>知识库问答</h2>
        <p>基于 RAG 检索知识库内容并流式回答。</p>

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

      <el-card class="feature-card">
        <h2>故障分析</h2>
        <p>结合研发知识进行故障排查和分析。</p>

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
  margin: 0 auto 38px;
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
  color: #aeb8c7;
  font-size: 14px;
}

.feature-grid {
  max-width: 1160px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
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

.feature-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-soft);
}

.feature-card :deep(.el-card__body) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.feature-grid h2 {
  margin: 0 0 12px;
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
}
</style>
