<script setup lang="ts">
import { computed, ref } from "vue";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";
import { streamIncident } from "../api/incidents";

const route = useRoute();
const router = useRouter();

const title = ref("");
const content = ref("");
const result = ref("");
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
  if (!title.value.trim() || !content.value.trim()) {
    ElMessage.warning("请填写故障标题和故障内容");
    return;
  }

  stop();
  controller = new AbortController();

  result.value = "";
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

      <h1>故障分析</h1>
      <p>根据当前知识库中的研发文档生成排查建议。</p>
    </header>

    <section class="incident-form">
      <el-form>
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
            :rows="10"
            maxlength="20000"
            show-word-limit
            placeholder="粘贴错误日志、现象和已知信息"
          />
        </el-form-item>

        <el-button type="primary" :loading="loading" @click="submit">
          开始分析
        </el-button>

        <el-button v-if="loading" @click="stop"> 停止 </el-button>
      </el-form>
    </section>

    <el-card v-if="result" class="result-card">
      <template #header>
        <span>分析结果</span>
      </template>

      <div class="result-content">
        {{ result }}
      </div>
    </el-card>
  </main>
</template>

<style scoped>
.incident-page {
  min-height: 100vh;
  padding: 46px 44px 84px;
  background: var(--paper);
  box-sizing: border-box;
}

.page-header,
.incident-form,
.result-card {
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

.incident-form {
  margin-top: 24px;
  padding: 24px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow-card);
}

.incident-form :deep(.el-input__wrapper),
.incident-form :deep(.el-textarea__inner) {
  border: 1px solid var(--line);
  border-radius: 8px;
  box-shadow: none;
}

.incident-form :deep(.el-textarea__inner) {
  min-height: 220px !important;
  line-height: 1.7;
}

.incident-form :deep(.el-button--primary) {
  min-height: 42px;
  border: 0;
  border-radius: 8px;
  color: var(--ink-950);
  background: var(--amber);
  font-weight: 700;
}

.result-card {
  margin-top: 20px;
  border: 1px solid rgba(213, 138, 53, 0.34);
  border-radius: var(--radius);
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

.incident-page :deep(.el-button.is-link) {
  padding: 0;
  color: var(--ink-500);
}

@media (max-width: 700px) {
  .incident-page {
    padding: 34px 16px 60px;
  }
}
</style>
