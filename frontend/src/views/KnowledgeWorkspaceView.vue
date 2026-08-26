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
      <el-card>
        <h2>文档管理</h2>
        <p>上传、解析和查看知识库文档。</p>
        <el-tag type="info">T14-D 开发</el-tag>
      </el-card>

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

      <el-card>
        <h2>知识库问答</h2>
        <p>基于 RAG 检索知识库内容并流式回答。</p>
        <el-tag type="info">T14-E 开发</el-tag>
      </el-card>

      <el-card>
        <h2>故障分析</h2>
        <p>结合研发知识进行故障排查和分析。</p>
        <el-tag type="info">T14-E 开发</el-tag>
      </el-card>
    </section>
  </main>
</template>

<style scoped>
.workspace-detail-page {
  min-height: 100vh;
  padding: 40px;
  background: #f4f6f8;
  box-sizing: border-box;
}

.detail-header {
  max-width: 1180px;
  margin: 0 auto 32px;
}

.eyebrow {
  margin: 32px 0 8px;
  color: #409eff;
  font-weight: 700;
}

.detail-header h1 {
  margin: 0 0 8px;
  font-size: 34px;
}

.description {
  color: #606266;
}

.feature-grid {
  max-width: 1180px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
}

.feature-grid h2 {
  margin-top: 0;
  font-size: 20px;
}

.feature-grid p {
  min-height: 48px;
  color: #606266;
}

@media (max-width: 800px) {
  .workspace-page,
  .workspace-detail-page {
    padding: 24px 16px;
  }

  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .feature-grid {
    grid-template-columns: 1fr;
  }
}
</style>
