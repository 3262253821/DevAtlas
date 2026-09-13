<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";
import { streamQuestion } from "../api/qa";
import { renderMarkdown } from "../utils/markdown";

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
const resultsRef = ref<HTMLElement | null>(null);

let controller: AbortController | null = null;

const knowledgeBaseId = computed(() => {
  return Number(route.params.id);
});

const renderedAnswer = computed(() => {
  return renderMarkdown(answer.value);
});

// 流式回答增长时跟随底部，但尊重用户主动向上查看旧内容的操作。
watch(answer, async () => {
  const element = resultsRef.value;
  const nearBottom =
    !element ||
    element.scrollHeight - element.scrollTop - element.clientHeight < 120;

  await nextTick();

  if (nearBottom && resultsRef.value) {
    resultsRef.value.scrollTop = resultsRef.value.scrollHeight;
  }
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

      <h1>知识库问答</h1>
      <p>回答只基于当前知识库中已索引的文档。</p>
    </header>

    <section class="qa-workspace">
      <section class="qa-panel">
        <div class="panel-kicker">ASK THE KNOWLEDGE BASE</div>
        <h2 class="panel-title">提出一个问题</h2>
        <p class="panel-description">
          描述你遇到的研发问题，回答会严格基于当前知识库。
        </p>

        <el-input
          v-model="question"
          type="textarea"
          :rows="8"
          maxlength="2000"
          show-word-limit
          placeholder="例如：忘记密码后应该怎么办？"
        />

        <div class="qa-actions">
          <div class="top-k-control">
            <span class="control-label">检索片段</span>
            <el-input-number
              v-model="topK"
              :min="1"
              :max="10"
              label="Top-K"
            />
          </div>

          <div class="action-buttons">
            <el-button type="primary" :loading="loading" @click="submit">
              {{ loading ? "生成中" : "开始提问" }}
            </el-button>

            <el-button v-if="loading" @click="stop">停止生成</el-button>
          </div>
        </div>
      </section>

      <section ref="resultsRef" class="qa-results" aria-live="polite">
        <div v-if="!answer" class="qa-result-empty">
          <span class="empty-mark" aria-hidden="true">↗</span>
          <strong>{{ loading ? "正在生成回答" : "回答会出现在这里" }}</strong>
          <p>
            {{
              loading
                ? "正在检索相关文档并组织答案，请稍候。"
                : "提交问题后，回答和引用来源会在此区域展示。"
            }}
          </p>
        </div>

        <el-card v-if="answer" class="answer-card">
          <template #header>
            <div class="result-heading">
              <span>回答</span>
              <span v-if="loading" class="result-status">实时生成中</span>
            </div>
          </template>

          <div
            class="answer-content markdown-body"
            v-html="renderedAnswer"
          />
        </el-card>

        <el-card v-if="citations.length" class="citation-card">
          <template #header>
            <div class="result-heading">
              <span>引用来源</span>
              <span class="result-count">{{ citations.length }} 个片段</span>
            </div>
          </template>

          <el-table :data="citations">
            <el-table-column prop="index" label="#" width="60" />
            <el-table-column prop="filename" label="文件" min-width="180" />
            <el-table-column prop="chunk_index" label="切片" width="80" />
            <el-table-column prop="distance" label="距离" width="100" />
          </el-table>
        </el-card>
      </section>
    </section>
  </main>
</template>

<style scoped>
.qa-page {
  height: 100vh;
  min-height: 620px;
  padding: 34px 44px 38px;
  background: var(--paper);
  box-sizing: border-box;
  overflow: hidden;
}

.page-header,
.qa-workspace {
  width: min(100%, 1240px);
  margin-left: auto;
  margin-right: auto;
}

.page-header {
  flex: 0 0 auto;
}

.page-header h1 {
  margin: 18px 0 7px;
  color: var(--ink-950);
  font-size: clamp(30px, 3.6vw, 44px);
  letter-spacing: -0.04em;
}

.page-header p {
  margin: 0;
  color: var(--ink-500);
  font-size: 14px;
}

.qa-workspace {
  display: grid;
  grid-template-columns: minmax(300px, 0.38fr) minmax(0, 0.62fr);
  gap: 22px;
  height: calc(100% - 122px);
  min-height: 0;
  margin-top: 26px;
}

.qa-panel {
  min-height: 0;
  padding: 24px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--surface);
  box-shadow: var(--shadow-card);
}

.panel-kicker {
  color: var(--teal-dark);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 10px;
  letter-spacing: 0.14em;
}

.panel-title {
  margin: 12px 0 7px;
  color: var(--ink-950);
  font-size: 22px;
  letter-spacing: -0.02em;
}

.panel-description {
  margin: 0 0 22px;
  color: var(--ink-500);
  font-size: 13px;
  line-height: 1.6;
}

.qa-actions {
  display: grid;
  gap: 18px;
  margin-top: 18px;
}

.top-k-control {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.control-label {
  color: var(--ink-700);
  font-size: 12px;
  font-weight: 650;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.qa-panel :deep(.el-textarea__inner) {
  min-height: 190px !important;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  box-shadow: none;
  color: var(--ink-900);
  background: #fbfaf5;
  line-height: 1.7;
}

.qa-panel :deep(.el-input-number) {
  width: 122px;
}

.qa-panel :deep(.el-button--primary) {
  flex: 1;
  min-height: 42px;
  border: 0;
  border-radius: 8px;
  color: #ffffff;
  background: var(--teal);
  font-weight: 700;
}

.action-buttons :deep(.el-button:not(.el-button--primary)) {
  min-height: 42px;
  border-radius: 8px;
}

.qa-results {
  min-width: 0;
  min-height: 0;
  padding-right: 4px;
  overflow-y: auto;
  scrollbar-color: #c7d1dc transparent;
  scrollbar-width: thin;
}

.qa-result-empty {
  min-height: 260px;
  display: grid;
  place-items: center;
  align-content: center;
  padding: 40px 24px;
  border: 1px dashed #cbd6e1;
  border-radius: 14px;
  color: var(--ink-700);
  text-align: center;
  background: rgba(255, 255, 255, 0.58);
}

.empty-mark {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  margin-bottom: 14px;
  border-radius: 12px;
  color: #ffffff;
  background: var(--teal);
  font-size: 20px;
}

.qa-result-empty strong {
  color: var(--ink-900);
  font-size: 16px;
}

.qa-result-empty p {
  max-width: 310px;
  margin: 8px 0 0;
  color: var(--ink-500);
  font-size: 13px;
  line-height: 1.7;
}

.answer-card,
.citation-card {
  margin: 0 0 18px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--surface);
  box-shadow: var(--shadow-card);
}

.answer-content {
  min-height: 160px;
  color: var(--ink-700);
  line-height: 1.8;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  margin: 1.15em 0 0.55em;
  color: var(--ink-950);
  line-height: 1.35;
}

.markdown-body :deep(h1) {
  font-size: 1.45em;
}

.markdown-body :deep(h2) {
  font-size: 1.25em;
}

.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  font-size: 1.08em;
}

.markdown-body :deep(p) {
  margin: 0.7em 0;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 0.65em 0;
  padding-left: 1.55em;
}

.markdown-body :deep(li) {
  margin: 0.28em 0;
}

.markdown-body :deep(strong) {
  color: var(--ink-950);
  font-weight: 750;
}

.markdown-body :deep(code) {
  padding: 0.12em 0.38em;
  border-radius: 5px;
  color: #8a551b;
  background: #fff3df;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 0.9em;
}

.markdown-body :deep(pre) {
  margin: 1em 0;
  padding: 14px 16px;
  overflow-x: auto;
  border: 1px solid #e9dcc8;
  border-radius: 9px;
  color: #3e352b;
  background: #faf7f1;
}

.markdown-body :deep(pre code) {
  padding: 0;
  color: inherit;
  background: transparent;
  font-size: 0.86em;
  line-height: 1.65;
}

.markdown-body :deep(blockquote) {
  margin: 1em 0;
  padding: 0.55em 1em;
  border-left: 3px solid var(--teal);
  color: var(--ink-500);
  background: #f3f8f7;
}

.markdown-body :deep(blockquote p) {
  margin: 0;
}

.markdown-body :deep(table) {
  width: 100%;
  margin: 1em 0;
  border-collapse: collapse;
  font-size: 0.93em;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  padding: 9px 11px;
  border: 1px solid var(--line);
  text-align: left;
  vertical-align: top;
}

.markdown-body :deep(th) {
  color: var(--ink-950);
  background: #f4f7f9;
  font-weight: 700;
}

.markdown-body :deep(a) {
  color: var(--teal-dark);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.result-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.result-status,
.result-count {
  color: var(--teal-dark);
  font-size: 11px;
  font-weight: 500;
}

.answer-card :deep(.el-card__header),
.citation-card :deep(.el-card__header) {
  color: var(--ink-950);
  font-weight: 700;
  background: #f4f7f9;
  border-bottom-color: var(--line);
}

.citation-card :deep(.el-table) {
  --el-table-header-bg-color: #fbfcfd;
  --el-table-border-color: var(--line);
}

.qa-page :deep(.el-button.is-link) {
  padding: 0;
  color: var(--ink-500);
}

@media (max-width: 760px) {
  .qa-page {
    height: auto;
    min-height: 100vh;
    padding: 34px 16px 60px;
    overflow: visible;
  }

  .qa-workspace {
    display: block;
    height: auto;
    margin-top: 22px;
  }

  .qa-panel {
    margin-bottom: 18px;
  }

  .qa-panel :deep(.el-input-number) {
    width: 100%;
  }

  .top-k-control,
  .action-buttons {
    align-items: stretch;
    flex-direction: column;
  }

  .action-buttons :deep(.el-button) {
    width: 100%;
  }

  .qa-results {
    overflow: visible;
  }
}
</style>
