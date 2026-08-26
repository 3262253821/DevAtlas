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
  padding: 40px;
  background: #f4f6f8;
  box-sizing: border-box;
}

.page-header,
.qa-panel,
.answer-card,
.citation-card {
  max-width: 1000px;
  margin-left: auto;
  margin-right: auto;
}

.page-header h1 {
  margin: 28px 0 8px;
  font-size: 32px;
}

.page-header p {
  color: #606266;
}

.qa-panel {
  margin-top: 24px;
  padding: 24px;
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.qa-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
}

.answer-card,
.citation-card {
  margin-top: 20px;
}

.answer-content {
  white-space: pre-wrap;
  line-height: 1.8;
}
</style>
