<script setup lang="ts">
import { computed, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";
import { streamQuestion } from "../api/qa";

interface Citation {
  index: number;
  filename: string;
  document_id: number;
  version_id: number;
  chunk_index: number;
  distance: number;
}

const route = useRoute();
const router = useRouter();

const question = ref("");
const topK = ref(5);
const answer = ref("");
const citations = ref<Citation[]>([]);
const loading = ref(false);

let controller: AbortController | null = null;

const knowledgeBaseId = computed(() => {
  return Number(route.params.id);
});

function stop(): void {
  controller?.abort();
  controller = null;
  loading.value = false;
}

async function submit(): Promise<void> {
  if (!question.value.trim()) {
    ElMessage.warning("请输入问题");
    return;
  }

  stop();

  controller = new AbortController();
  answer.value = "";
  citations.value = [];
  loading.value = true;

  try {
    await streamQuestion(
      knowledgeBaseId.value,
      {
        question: question.value.trim(),
        top_k: topK.value,
        conversation_id: null,
      },
      (eventName, data) => {
        if (eventName === "token") {
          const text = data.text;

          if (typeof text === "string") {
            answer.value += text;
          }
        }

        if (eventName === "citation") {
          citations.value.push({
            index: Number(data.index),
            filename: String(data.filename ?? ""),
            document_id: Number(data.document_id),
            version_id: Number(data.version_id),
            chunk_index: Number(data.chunk_index),
            distance: Number(data.distance),
          });
        }

        if (eventName === "error") {
          ElMessage.error(String(data.message ?? "问答服务失败"));
        }
      },
      controller.signal,
    );
  } catch (error) {
    if (!(error instanceof DOMException)) {
      ElMessage.error(error instanceof Error ? error.message : "问答失败");
    }
  } finally {
    loading.value = false;
    controller = null;
  }
}
</script>

<template>
  <main class="qa-page">
    <header class="page-header">
      <el-button
        link
        @click="
          router.push({
            name: 'knowledge',
            params: { id: knowledgeBaseId },
          })
        "
      >
        返回工作台
      </el-button>

      <h1>知识库问答</h1>
      <p>回答只基于当前知识库中已索引的文档。</p>
    </header>

    <section class="qa-panel">
      <el-input
        v-model="question"
        type="textarea"
        :rows="5"
        maxlength="2000"
        show-word-limit
        placeholder="例如：忘记密码后应该怎么办？"
      />

      <div class="qa-actions">
        <el-input-number v-model="topK" :min="1" :max="10" label="Top-K" />

        <el-button type="primary" :loading="loading" @click="submit">
          开始提问
        </el-button>

        <el-button v-if="loading" @click="stop"> 停止 </el-button>
      </div>
    </section>

    <el-card v-if="answer" class="answer-card">
      <template #header>
        <span>回答</span>
      </template>

      <div class="answer-content">
        {{ answer }}
      </div>
    </el-card>

    <el-card v-if="citations.length" class="citation-card">
      <template #header>
        <span>引用来源</span>
      </template>

      <el-table :data="citations">
        <el-table-column prop="index" label="#" width="60" />
        <el-table-column prop="filename" label="文件" />
        <el-table-column prop="chunk_index" label="切片" width="80" />
        <el-table-column prop="distance" label="距离" width="100" />
      </el-table>
    </el-card>
  </main>
</template>

<style scoped>
.qa-page {
  min-height: 100vh;
  padding: 46px 44px 84px;
  background: var(--paper);
  box-sizing: border-box;
}

.page-header,
.qa-panel,
.answer-card,
.citation-card {
  max-width: 1060px;
  margin-left: auto;
  margin-right: auto;
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

.qa-panel {
  margin-top: 24px;
  padding: 24px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow-card);
}

.qa-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
}

.qa-panel :deep(.el-textarea__inner) {
  min-height: 150px !important;
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  box-shadow: none;
  color: var(--ink-900);
  background: #fbfaf5;
  line-height: 1.7;
}

.qa-panel :deep(.el-input-number) {
  width: 132px;
}

.qa-panel :deep(.el-button--primary) {
  min-height: 40px;
  border: 0;
  border-radius: 8px;
  color: var(--ink-950);
  background: var(--teal);
  font-weight: 700;
}

.answer-card,
.citation-card {
  margin-top: 20px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow-card);
}

.answer-content {
  min-height: 120px;
  white-space: pre-wrap;
  color: var(--ink-700);
  line-height: 1.8;
}

.answer-card :deep(.el-card__header),
.citation-card :deep(.el-card__header) {
  color: var(--ink-950);
  font-weight: 700;
  background: #f5f1e8;
  border-bottom-color: var(--line);
}

.citation-card :deep(.el-table) {
  --el-table-header-bg-color: #fbfaf5;
  --el-table-border-color: var(--line);
}

.qa-page :deep(.el-button.is-link) {
  padding: 0;
  color: var(--ink-500);
}

@media (max-width: 700px) {
  .qa-page {
    padding: 34px 16px 60px;
  }

  .qa-actions {
    align-items: stretch;
    flex-direction: column;
  }

  .qa-panel :deep(.el-input-number),
  .qa-actions :deep(.el-button) {
    width: 100%;
  }
}
</style>
