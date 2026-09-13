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
      <div>
        <p class="eyebrow">DEVATLAS / INCIDENT ARCHIVE</p>
        <h1>故障分析历史</h1>
        <p>查看已经完成或失败的故障分析记录。</p>
      </div>
    </header>

    <section class="incident-history-workspace">
      <el-card class="incidents-card">
        <template #header>
          <div class="panel-heading">
            <div>
              <span class="panel-kicker">RECENT INCIDENTS</span>
              <strong>分析记录</strong>
            </div>
            <span class="panel-count">{{ incidents.length }} 条</span>
          </div>
        </template>

        <el-empty
          v-if="!loading && incidents.length === 0"
          description="暂无故障分析记录"
        />

        <div v-else class="incident-list">
          <article
            v-for="incident in incidents"
            :key="incident.id"
            class="incident-list-item"
            :class="{ 'incident-list-item--active': selected?.id === incident.id }"
          >
            <button
              class="incident-list-main"
              type="button"
              @click="showDetail(incident)"
            >
              <strong>{{ incident.title }}</strong>
              <span>{{ formatDate(incident.created_at) }}</span>
            </button>

            <div class="incident-list-footer">
              <span class="incident-status" :data-status="incident.status">
                {{ incident.status }}
              </span>

              <div class="incident-row-actions">
                <el-button
                  class="incident-view-button"
                  type="primary"
                  plain
                  @click="showDetail(incident)"
                >
                  查看
                </el-button>

                <el-button
                  class="incident-delete-button"
                  type="danger"
                  plain
                  @click="removeIncident(incident)"
                >
                  删除
                </el-button>
              </div>
            </div>
          </article>
        </div>
      </el-card>

      <el-card v-if="selected" class="detail-card">
        <template #header>
          <div class="detail-heading">
            <div>
              <span class="panel-kicker">INCIDENT DETAIL</span>
              <strong>{{ selected.title }}</strong>
            </div>
            <span class="incident-status" :data-status="selected.status">
              {{ selected.status }}
            </span>
          </div>
        </template>

        <div class="detail-scroll-area">
          <section class="detail-section">
            <h3>输入内容</h3>
            <pre>{{ selected.input_content }}</pre>
          </section>

          <section class="detail-section">
            <h3>分析结果</h3>
            <div class="result-content">
              {{ selected.result || "暂无结果" }}
            </div>
          </section>
        </div>
      </el-card>

      <aside v-else class="detail-placeholder">
        <span class="placeholder-mark" aria-hidden="true">↗</span>
        <strong>选择一条记录查看详情</strong>
        <p>故障输入、分析结果和引用内容会在这里展示。</p>
      </aside>
    </section>
  </main>
</template>

<style scoped>
.incidents-page {
  min-height: 100vh;
  padding: 58px 44px 84px;
  background: var(--paper);
  box-sizing: border-box;
}

.page-header,
.incident-history-workspace {
  max-width: 1160px;
  margin-left: auto;
  margin-right: auto;
}

.page-header {
  margin-bottom: 26px;
}

.eyebrow,
.panel-kicker {
  color: var(--teal-dark);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.14em;
}

.eyebrow {
  margin: 0 0 8px;
}

.page-header h1 {
  margin: 0 0 8px;
  color: var(--ink-950);
  font-size: clamp(30px, 3.5vw, 44px);
  letter-spacing: -0.035em;
}

.page-header p {
  margin: 0;
  color: var(--ink-500);
  font-size: 14px;
}

.incident-history-workspace {
  display: grid;
  grid-template-columns: minmax(390px, 0.92fr) minmax(0, 1.28fr);
  align-items: stretch;
  gap: 18px;
}

.incidents-card {
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow-card);
}

.incidents-card :deep(.el-card__body) {
  padding: 0;
}

.incidents-card :deep(.el-card__header) {
  padding: 17px 20px;
  border-bottom-color: var(--line);
  background: #f5f1e8;
}

.panel-heading,
.detail-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.panel-heading > div,
.detail-heading > div {
  min-width: 0;
}

.panel-kicker {
  display: block;
  margin-bottom: 6px;
  color: var(--ink-500);
  font-size: 9px;
}

.panel-heading strong,
.detail-heading strong {
  display: block;
  overflow: hidden;
  color: var(--ink-950);
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.panel-count {
  flex: 0 0 auto;
  color: var(--ink-500);
  font-size: 12px;
}

.incident-list {
  max-height: calc(100vh - 280px);
  overflow: auto;
  padding: 8px;
}

.incident-list-item {
  padding: 14px;
  border: 1px solid transparent;
  border-radius: 9px;
  transition: border-color 160ms ease, background 160ms ease;
}

.incident-list-item + .incident-list-item {
  margin-top: 4px;
}

.incident-list-item:hover,
.incident-list-item--active {
  border-color: #c9dfd9;
  background: #f2f9f7;
}

.incident-list-item--active {
  box-shadow: inset 3px 0 0 var(--teal);
}

.incident-list-main {
  width: 100%;
  padding: 0;
  border: 0;
  color: inherit;
  text-align: left;
  background: transparent;
  cursor: pointer;
}

.incident-list-main strong,
.incident-list-main span {
  display: block;
}

.incident-list-main strong {
  overflow: hidden;
  color: var(--ink-900);
  font-size: 14px;
  line-height: 1.5;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.incident-list-main span {
  margin-top: 5px;
  color: var(--ink-500);
  font-size: 11px;
}

.incident-list-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 13px;
}

.detail-card {
  min-width: 0;
  min-height: 520px;
  overflow: hidden;
  border: 1px solid rgba(213, 138, 53, 0.34);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow-card);
}

.detail-card :deep(.el-card__header) {
  padding: 17px 22px;
  font-weight: 700;
  background: #fff5e5;
  border-bottom-color: rgba(213, 138, 53, 0.24);
}

.detail-heading strong {
  color: #8a551b;
}

.incident-status {
  flex: 0 0 auto;
  padding: 5px 9px;
  border: 1px solid #b9d8ce;
  border-radius: 999px;
  color: var(--teal-dark);
  background: #eff9f5;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 11px;
}

.incident-status[data-status="failed"] {
  border-color: #efc2bc;
  color: #b64b3e;
  background: #fff4f2;
}

.incident-status[data-status="cancelled"] {
  border-color: #d6dce5;
  color: var(--ink-500);
  background: #f6f8fb;
}

.detail-scroll-area {
  max-height: calc(100vh - 280px);
  overflow: auto;
  padding: 24px 22px 28px;
}

.detail-section + .detail-section {
  margin-top: 28px;
  padding-top: 24px;
  border-top: 1px solid var(--line);
}

.detail-section h3 {
  margin: 0 0 12px;
  color: var(--ink-950);
  font-size: 16px;
}

pre,
.result-content {
  margin: 0;
  padding: 15px 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  color: var(--ink-700);
  background: #fbfcfd;
  white-space: pre-wrap;
  line-height: 1.8;
}

.incident-row-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.incident-row-actions :deep(.el-button) {
  min-height: 32px;
  margin: 0;
  padding: 0 9px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 650;
}

.incident-row-actions :deep(.incident-view-button) {
  border-color: #8ccbbc;
  color: var(--teal-dark);
  background: #f1faf7;
}

.incident-row-actions :deep(.incident-delete-button) {
  border-color: #e08b82;
  color: #c54e42;
  background: #fff8f7;
}

.incident-row-actions :deep(.incident-delete-button:hover) {
  border-color: #c54e42;
  color: #ffffff;
  background: #d85c49;
}

.detail-placeholder {
  min-height: 520px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px;
  border: 1px dashed #d4dce6;
  border-radius: var(--radius);
  color: var(--ink-500);
  background: rgba(255, 255, 255, 0.56);
  text-align: center;
}

.placeholder-mark {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  margin-bottom: 16px;
  border-radius: 12px;
  color: #9a641e;
  background: #fff5e5;
  font-size: 22px;
}

.detail-placeholder strong {
  color: var(--ink-900);
  font-size: 15px;
}

.detail-placeholder p {
  max-width: 260px;
  margin: 8px 0 0;
  color: var(--ink-500);
  font-size: 12px;
  line-height: 1.6;
}

@media (max-width: 700px) {
  .incidents-page {
    padding: 34px 16px 60px;
  }

  .incident-history-workspace {
    grid-template-columns: 1fr;
  }

  .detail-card,
  .detail-placeholder {
    min-height: 420px;
  }

  .detail-scroll-area {
    max-height: none;
  }
}
</style>
