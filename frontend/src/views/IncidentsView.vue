<script setup lang="ts">
import { onMounted, ref } from "vue";
import { isAxiosError } from "axios";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  deleteIncident,
  getIncident,
  listIncidents,
  type IncidentDetail,
  type IncidentSummary,
} from "../api/incidents";

const incidents = ref<IncidentSummary[]>([]);
const selected = ref<IncidentDetail | null>(null);
const loading = ref(false);

function getErrorMessage(error: unknown): string {
  if (isAxiosError<{ detail?: string }>(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }
  }

  return "操作失败";
}

function formatDate(value: string | null): string {
  return value ? new Date(value).toLocaleString("zh-CN") : "-";
}

async function loadIncidents(): Promise<void> {
  loading.value = true;

  try {
    const result = await listIncidents();
    incidents.value = result.items;
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    loading.value = false;
  }
}

async function showDetail(incident: IncidentSummary): Promise<void> {
  try {
    selected.value = await getIncident(incident.id);
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  }
}

async function removeIncident(incident: IncidentSummary): Promise<void> {
  try {
    await ElMessageBox.confirm(`确定删除“${incident.title}”吗？`, "删除确认", {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消",
    });

    await deleteIncident(incident.id);

    incidents.value = incidents.value.filter((item) => item.id !== incident.id);

    if (selected.value?.id === incident.id) {
      selected.value = null;
    }

    ElMessage.success("记录已删除");
  } catch (error) {
    if (isAxiosError(error)) {
      ElMessage.error(getErrorMessage(error));
    }
  }
}

onMounted(loadIncidents);
</script>

<template>
  <main v-loading="loading" class="incidents-page">
    <header class="page-header">
      <h1>故障分析历史</h1>
      <p>查看已经完成或失败的故障分析记录。</p>
    </header>

    <el-card class="incidents-card">
      <el-empty
        v-if="!loading && incidents.length === 0"
        description="暂无故障分析记录"
      />

      <el-table v-else :data="incidents" row-key="id">
        <el-table-column prop="title" label="标题" min-width="300" />

        <el-table-column prop="status" label="状态" width="120" />

        <el-table-column label="创建时间" width="190">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button link type="primary" @click="showDetail(row)">
              查看
            </el-button>

            <el-button link type="danger" @click="removeIncident(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-if="selected" class="detail-card">
      <template #header>
        <span>{{ selected.title }}</span>
      </template>

      <p>状态：{{ selected.status }}</p>

      <h3>输入内容</h3>
      <pre>{{ selected.input_content }}</pre>

      <h3>分析结果</h3>
      <div class="result-content">
        {{ selected.result || "暂无结果" }}
      </div>
    </el-card>
  </main>
</template>

<style scoped>
.incidents-page {
  min-height: 100vh;
  padding: 46px 44px 84px;
  background: var(--paper);
  box-sizing: border-box;
}

.page-header,
.incidents-card,
.detail-card {
  max-width: 1160px;
  margin-left: auto;
  margin-right: auto;
}

.page-header h1 {
  margin: 0 0 8px;
  color: var(--ink-950);
  font-size: clamp(30px, 4vw, 46px);
  letter-spacing: -0.04em;
}

.page-header p {
  color: var(--ink-500);
  font-size: 14px;
}

.incidents-card {
  margin-top: 24px;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow-card);
}

.incidents-card :deep(.el-card__body) {
  padding: 0;
}

.incidents-card :deep(.el-table) {
  --el-table-header-bg-color: #f5f1e8;
  --el-table-row-hover-bg-color: #fff7e9;
  --el-table-border-color: var(--line);
  color: var(--ink-700);
}

.incidents-card :deep(.el-table th.el-table__cell) {
  color: var(--ink-500);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.incidents-card :deep(.el-table td.el-table__cell),
.incidents-card :deep(.el-table th.el-table__cell) {
  padding: 18px 16px;
}

.detail-card {
  margin-top: 20px;
  border: 1px solid rgba(213, 138, 53, 0.34);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow-card);
}

.detail-card :deep(.el-card__header) {
  color: #8a551b;
  font-weight: 700;
  background: #fff5e5;
  border-bottom-color: rgba(213, 138, 53, 0.24);
}

pre,
.result-content {
  margin: 0;
  color: var(--ink-700);
  white-space: pre-wrap;
  line-height: 1.8;
}

.incidents-page :deep(.el-button.is-link) {
  padding: 0;
}

@media (max-width: 700px) {
  .incidents-page {
    padding: 34px 16px 60px;
  }
}
</style>
