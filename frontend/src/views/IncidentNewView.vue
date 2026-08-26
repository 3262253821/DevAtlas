<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";
import { streamIncident } from "../api/incidents";

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

const title = ref("");
const content = ref("");
const result = ref("");
const citations = ref<Citation[]>([]);
const loading = ref(false);
const resultsRef = ref<HTMLElement | null>(null);

let controller: AbortController | null = null;

const knowledgeBaseId = computed(() => {
  return Number(route.params.id);
});

// 流式结果增长时跟随底部，但不打断用户主动查看旧内容。
watch(result, async () => {
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
  if (!title.value.trim() || !content.value.trim()) {
    ElMessage.warning("请填写故障标题和故障内容");
    return;
  }

  stop();
  controller = new AbortController();

  result.value = "";
  citations.value = [];
  loading.value = true;

  try {
    await streamIncident(
      knowledgeBaseId.value,
      {
        title: title.value.trim(),
        content: content.value.trim(),
      },
      (eventName, data) => {
        if (eventName === "token") {
          const text = data.text;

          if (typeof text === "string") {
            result.value += text;
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
          ElMessage.error(String(data.message ?? "故障分析失败"));
        }
      },
      controller.signal,
    );
  } catch (error) {
    if (!(error instanceof DOMException)) {
      ElMessage.error(error instanceof Error ? error.message : "故障分析失败");
    }
  } finally {
    loading.value = false;
    controller = null;
  }
}
</script>

<template>
  <main class="incident-page">
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

      <h1>故障分析</h1>
      <p>根据当前知识库中的研发文档生成排查建议。</p>
    </header>

    <section class="incident-workspace">
      <section class="incident-form">
        <div class="panel-kicker">ANALYZE AN INCIDENT</div>
        <h2 class="panel-title">描述一个故障</h2>
        <p class="panel-description">
          提供标题、日志和现象，系统会结合当前知识库生成排查建议。
        </p>

        <el-form class="incident-form-fields">
          <el-form-item label="故障标题">
            <el-input
              v-model="title"
              maxlength="200"
              placeholder="例如：订单服务返回 502"
            />
          </el-form-item>

          <el-form-item label="故障日志或现象">
            <el-input
              v-model="content"
              type="textarea"
              :rows="12"
              maxlength="20000"
              show-word-limit
              placeholder="粘贴错误日志、现象和已知信息"
            />
          </el-form-item>

          <div class="incident-actions">
            <el-button type="primary" :loading="loading" @click="submit">
              {{ loading ? "分析中" : "开始分析" }}
            </el-button>

            <el-button v-if="loading" @click="stop">停止分析</el-button>
          </div>
        </el-form>
      </section>

      <section ref="resultsRef" class="incident-results" aria-live="polite">
        <div v-if="!result" class="result-empty">
          <span class="empty-mark" aria-hidden="true">✦</span>
          <strong>{{ loading ? "正在生成分析" : "分析结果会出现在这里" }}</strong>
          <p>
            {{
              loading
                ? "正在检索相关文档并组织排查建议，请稍候。"
                : "提交故障信息后，原因、步骤和引用来源会在此区域展示。"
            }}
          </p>
        </div>

        <el-card v-if="result" class="result-card">
          <template #header>
            <div class="result-heading">
              <span>分析结果</span>
              <span v-if="loading" class="result-status">实时生成中</span>
            </div>
          </template>

          <div class="result-content">
            {{ result }}
          </div>
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
.incident-page {
  height: 100vh;
  min-height: 620px;
  padding: 34px 44px 38px;
  background: var(--paper);
  box-sizing: border-box;
  overflow: hidden;
}

.page-header,
.incident-workspace {
  width: min(100%, 1240px);
  margin-left: auto;
  margin-right: auto;
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

.incident-workspace {
  display: grid;
  grid-template-columns: minmax(330px, 0.42fr) minmax(0, 0.58fr);
  gap: 22px;
  height: calc(100% - 122px);
  min-height: 0;
  margin-top: 26px;
}

.incident-form {
  min-height: 0;
  padding: 24px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--surface);
  box-shadow: var(--shadow-card);
}

.panel-kicker {
  color: var(--amber);
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

.incident-form-fields :deep(.el-form-item) {
  margin-bottom: 18px;
}

.incident-form-fields :deep(.el-form-item__label) {
  flex: 0 0 82px;
  width: 82px;
  justify-content: flex-start;
  color: var(--ink-700);
  font-size: 12px;
  font-weight: 650;
  white-space: nowrap;
}

.incident-form-fields :deep(.el-form-item__content) {
  margin-left: 12px !important;
}

.incident-form :deep(.el-input__wrapper),
.incident-form :deep(.el-textarea__inner) {
  border: 1px solid var(--line);
  border-radius: 8px;
  box-shadow: none;
}

.incident-form :deep(.el-textarea__inner) {
  min-height: 260px !important;
  padding: 14px;
  line-height: 1.7;
  background: #fbfaf5;
}

.incident-form :deep(.el-button--primary) {
  flex: 1;
  min-height: 42px;
  border: 0;
  border-radius: 8px;
  color: #ffffff;
  background: var(--amber);
  font-weight: 700;
}

.incident-actions {
  display: flex;
  gap: 10px;
  margin-top: 6px;
}

.incident-actions :deep(.el-button:not(.el-button--primary)) {
  min-height: 42px;
  border-radius: 8px;
}

.incident-results {
  min-width: 0;
  min-height: 0;
  padding-right: 4px;
  overflow-y: auto;
  scrollbar-color: #c7d1dc transparent;
  scrollbar-width: thin;
}

.result-empty {
  min-height: 270px;
  display: grid;
  place-items: center;
  align-content: center;
  padding: 40px 24px;
  border: 1px dashed #d7c6a9;
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
  background: var(--amber);
  font-size: 18px;
}

.result-empty strong {
  color: var(--ink-900);
  font-size: 16px;
}

.result-empty p {
  max-width: 320px;
  margin: 8px 0 0;
  color: var(--ink-500);
  font-size: 13px;
  line-height: 1.7;
}

.result-card,
.citation-card {
  margin: 0 0 18px;
  border: 1px solid rgba(213, 138, 53, 0.34);
  border-radius: 14px;
  background: var(--surface);
  box-shadow: var(--shadow-card);
}

.result-content {
  white-space: pre-wrap;
  color: var(--ink-700);
  line-height: 1.8;
}

.result-card :deep(.el-card__header) {
  color: #8a551b;
  font-weight: 700;
  background: #fff5e5;
  border-bottom-color: rgba(213, 138, 53, 0.24);
}

.citation-card {
  border-color: var(--line);
}

.citation-card :deep(.el-card__header) {
  color: var(--ink-950);
  background: #f4f7f9;
  border-bottom-color: var(--line);
}

.citation-card :deep(.el-table) {
  --el-table-header-bg-color: #fbfcfd;
  --el-table-border-color: var(--line);
}

.result-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.result-status,
.result-count {
  color: #a76b20;
  font-size: 11px;
  font-weight: 500;
}

.incident-page :deep(.el-button.is-link) {
  padding: 0;
  color: var(--ink-500);
}

@media (max-width: 700px) {
  .incident-page {
    height: auto;
    min-height: 100vh;
    padding: 34px 16px 60px;
    overflow: visible;
  }

  .incident-workspace {
    display: block;
    height: auto;
    margin-top: 22px;
  }

  .incident-form {
    margin-bottom: 18px;
  }

  .incident-form-fields :deep(.el-form-item__label) {
    flex-basis: 82px;
    width: 82px;
  }

  .incident-actions {
    align-items: stretch;
    flex-direction: column;
  }

  .incident-actions :deep(.el-button) {
    width: 100%;
  }

  .incident-results {
    overflow: visible;
  }
}
</style>
