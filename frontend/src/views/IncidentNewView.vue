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

async function submit(): Promise<void> {
  if (!title.value.trim() || !content.value.trim()) {
    ElMessage.warning("请填写故障标题和故障内容");
    return;
  }

  controller?.abort();
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
  padding: 40px;
  background: #f4f6f8;
  box-sizing: border-box;
}

.page-header,
.incident-form,
.result-card {
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

.incident-form {
  margin-top: 24px;
  padding: 24px;
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.result-card {
  margin-top: 20px;
}

.result-content {
  white-space: pre-wrap;
  line-height: 1.8;
}
</style>
