<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { isAxiosError } from "axios";
import { ElMessage, ElMessageBox } from "element-plus";
import { useRouter } from "vue-router";
import {
  createKnowledgeBase,
  deleteKnowledgeBase,
  listKnowledgeBases,
  type KnowledgeBaseCreate,
  type KnowledgeBasePublic,
} from "../api/knowledgeBase";

const router = useRouter();

const workspaces = ref<KnowledgeBasePublic[]>([]);
const loading = ref(false);
const dialogVisible = ref(false);
const creating = ref(false);

const form = reactive<KnowledgeBaseCreate>({
  name: "",
  description: "",
});

const workspaceCount = computed(() => workspaces.value.length);

const latestWorkspace = computed(() => {
  return [...workspaces.value].sort(
    (left, right) =>
      new Date(right.updated_at).getTime() -
      new Date(left.updated_at).getTime(),
  )[0];
});

const latestWorkspaceDate = computed(() => {
  return latestWorkspace.value
    ? formatDate(latestWorkspace.value.updated_at)
    : "暂无活动";
});

function errorMessage(error: unknown): string {
  if (isAxiosError<{ detail?: string }>(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }
  }

  return "操作失败，请稍后重试";
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString("zh-CN");
}

async function loadWorkspaces(): Promise<void> {
  loading.value = true;

  try {
    workspaces.value = await listKnowledgeBases();
  } catch (error) {
    ElMessage.error(errorMessage(error));
  } finally {
    loading.value = false;
  }
}

function openCreateDialog(): void {
  form.name = "";
  form.description = "";
  dialogVisible.value = true;
}

async function submitCreate(): Promise<void> {
  if (!form.name.trim()) {
    ElMessage.warning("请输入知识库名称");
    return;
  }

  creating.value = true;

  try {
    const created = await createKnowledgeBase({
      name: form.name.trim(),
      description: form.description?.trim() || undefined,
    });

    workspaces.value.unshift(created);
    dialogVisible.value = false;
    ElMessage.success("知识库创建成功");
  } catch (error) {
    ElMessage.error(errorMessage(error));
  } finally {
    creating.value = false;
  }
}

async function removeWorkspace(workspace: KnowledgeBasePublic): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `确定删除知识库“${workspace.name}”吗？`,
      "删除确认",
      {
        type: "warning",
        confirmButtonText: "删除",
        cancelButtonText: "取消",
      },
    );

    await deleteKnowledgeBase(workspace.id);

    workspaces.value = workspaces.value.filter(
      (item) => item.id !== workspace.id,
    );

    ElMessage.success("知识库已删除");
  } catch (error) {
    if (isAxiosError(error)) {
      ElMessage.error(errorMessage(error));
    }
  }
}

function openWorkspace(workspace: KnowledgeBasePublic): void {
  router.push({
    name: "knowledge",
    params: {
      id: workspace.id,
    },
  });
}

onMounted(loadWorkspaces);
</script>

<template>
  <main class="workspace-page">
    <header class="page-header">
      <div>
        <p class="eyebrow">DEVATLAS / WORKSPACE HOME</p>
        <h1>我的知识库</h1>
        <p class="description">集中管理研发资料，从一个工作区开始协作。</p>
      </div>

      <el-button type="primary" @click="openCreateDialog">
        新建知识库
      </el-button>
    </header>

    <section class="workspace-overview" aria-label="工作区概览">
      <article class="overview-stat">
        <span class="overview-label">知识库总数</span>
        <strong>{{ workspaceCount }}</strong>
        <span class="overview-note">当前账号可访问</span>
      </article>

      <article class="overview-stat overview-stat--accent">
        <span class="overview-label">最近使用</span>
        <strong>{{ latestWorkspace?.name || "暂无" }}</strong>
        <span class="overview-note">{{ latestWorkspaceDate }}</span>
      </article>

      <article class="overview-stat">
        <span class="overview-label">下一步</span>
        <strong>{{ latestWorkspace ? "继续工作" : "建立工作区" }}</strong>
        <span class="overview-note">上传资料并开始问答</span>
      </article>
    </section>

    <section class="workspace-home-grid">
      <div class="workspace-list-column">
        <div class="section-heading">
          <div>
            <p class="section-kicker">YOUR KNOWLEDGE BASES</p>
            <h2>全部知识库</h2>
          </div>
          <span class="section-count">{{ workspaceCount }} 个</span>
        </div>

        <el-card v-loading="loading" class="workspace-card">
          <el-empty
            v-if="!loading && workspaces.length === 0"
            description="还没有知识库，先创建一个工作区"
          />

          <el-table v-else :data="workspaces" row-key="id">
            <el-table-column prop="name" label="名称" min-width="220" />

            <el-table-column prop="description" label="描述" min-width="300">
              <template #default="{ row }">
                {{ row.description || "暂无描述" }}
              </template>
            </el-table-column>

            <el-table-column label="最近更新" width="190">
              <template #default="{ row }">
                {{ formatDate(row.updated_at) }}
              </template>
            </el-table-column>

            <el-table-column label="操作" width="236" fixed="right">
              <template #default="{ row }">
                <div class="workspace-row-actions">
                  <el-button
                    class="workspace-enter-button"
                    type="primary"
                    @click="openWorkspace(row)"
                  >
                    进入工作台
                  </el-button>

                  <el-button
                    class="workspace-delete-button"
                    type="danger"
                    plain
                    @click="removeWorkspace(row)"
                  >
                    删除
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>

      <aside class="workspace-activity-panel">
        <div class="section-heading">
          <div>
            <p class="section-kicker">QUICK START</p>
            <h2>快捷开始</h2>
          </div>
        </div>

        <button
          v-if="latestWorkspace"
          class="quick-action quick-action--primary"
          type="button"
          @click="openWorkspace(latestWorkspace)"
        >
          <span class="quick-action-index">01</span>
          <span class="quick-action-copy">
            <strong>继续使用 {{ latestWorkspace.name }}</strong>
            <small>进入工作台，继续问答或管理文档</small>
          </span>
          <span class="quick-action-arrow" aria-hidden="true">↗</span>
        </button>

        <button class="quick-action" type="button" @click="openCreateDialog">
          <span class="quick-action-index">02</span>
          <span class="quick-action-copy">
            <strong>建立新的知识库</strong>
            <small>为新的服务或团队整理独立资料</small>
          </span>
          <span class="quick-action-arrow" aria-hidden="true">＋</span>
        </button>

        <div class="activity-note">
          <span class="activity-dot" aria-hidden="true"></span>
          <div>
            <strong>建议工作流</strong>
            <p>创建知识库 → 上传文档 → 开始问答</p>
          </div>
        </div>
      </aside>
    </section>

    <el-dialog v-model="dialogVisible" title="创建知识库" width="460px">
      <el-form :model="form">
        <el-form-item label="名称">
          <el-input
            v-model="form.name"
            maxlength="100"
            show-word-limit
            placeholder="例如：订单服务研发知识库"
          />
        </el-form-item>

        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            maxlength="500"
            show-word-limit
            :rows="4"
            placeholder="描述这个知识库的用途"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false"> 取消 </el-button>

        <el-button type="primary" :loading="creating" @click="submitCreate">
          创建
        </el-button>
      </template>
    </el-dialog>
  </main>
</template>

<style scoped>
.workspace-page {
  min-height: 100vh;
  padding: 58px 44px 84px;
  background: var(--paper);
  box-sizing: border-box;
}

.page-header {
  max-width: 1160px;
  margin: 0 auto 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.eyebrow {
  margin: 0 0 8px;
  color: var(--teal-dark);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
}

.page-header h1 {
  margin: 0 0 8px;
  color: var(--ink-950);
  font-size: clamp(30px, 4vw, 46px);
  letter-spacing: -0.04em;
}

.description {
  margin: 0;
  color: var(--ink-500);
  font-size: 14px;
}

.workspace-overview {
  max-width: 1160px;
  margin: 0 auto 28px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.overview-stat {
  min-height: 112px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 18px 20px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.78);
}

.overview-stat--accent {
  border-color: rgba(31, 157, 135, 0.32);
  background: #eef8f5;
}

.overview-label,
.overview-note {
  color: var(--ink-500);
  font-size: 12px;
}

.overview-stat strong {
  overflow: hidden;
  color: var(--ink-950);
  font-size: 22px;
  font-weight: 750;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workspace-home-grid {
  max-width: 1160px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
}

.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}

.section-kicker {
  margin: 0 0 5px;
  color: var(--teal-dark);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 10px;
  letter-spacing: 0.14em;
}

.section-heading h2 {
  margin: 0;
  color: var(--ink-950);
  font-size: 19px;
  letter-spacing: -0.02em;
}

.section-count {
  color: var(--ink-500);
  font-size: 12px;
}

.workspace-card {
  max-width: 1160px;
  margin: 0 auto;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow-card);
}

.workspace-card :deep(.el-card__body) {
  padding: 0;
}

.workspace-card :deep(.el-table) {
  --el-table-header-bg-color: #f5f1e8;
  --el-table-row-hover-bg-color: #f1f8f5;
  --el-table-border-color: var(--line);
  color: var(--ink-700);
}

.workspace-card :deep(.el-table th.el-table__cell) {
  color: var(--ink-500);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.workspace-card :deep(.el-table td.el-table__cell),
.workspace-card :deep(.el-table th.el-table__cell) {
  padding: 18px 16px;
}

.workspace-card :deep(.el-table .cell) {
  line-height: 1.5;
}

.workspace-card :deep(.el-empty) {
  padding: 88px 24px;
}

.workspace-row-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.workspace-row-actions :deep(.el-button) {
  min-height: 36px;
  margin: 0;
  padding: 0 12px;
  border-radius: 7px;
  font-size: 12px;
  font-weight: 650;
}

.workspace-row-actions :deep(.workspace-enter-button) {
  border-color: var(--teal);
  color: var(--ink-950);
  background: var(--teal);
}

.workspace-row-actions :deep(.workspace-enter-button:hover) {
  border-color: var(--teal-dark);
  background: var(--teal-dark);
}

.workspace-row-actions :deep(.workspace-delete-button) {
  border-color: #e08b82;
  color: #c54e42;
  background: #fff8f7;
}

.workspace-row-actions :deep(.workspace-delete-button:hover) {
  border-color: #c54e42;
  color: #ffffff;
  background: #d85c49;
}

.workspace-activity-panel {
  order: -1;
  margin-bottom: 24px;
  padding: 20px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.74);
  box-shadow: var(--shadow-card);
}

.workspace-activity-panel .section-heading {
  margin-bottom: 14px;
}

.quick-action {
  width: 100%;
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 14px 12px;
  border: 1px solid var(--line);
  border-radius: 9px;
  color: inherit;
  text-align: left;
  background: var(--surface);
  cursor: pointer;
  transition: border-color 160ms ease, background 160ms ease,
    transform 160ms ease;
}

.quick-action + .quick-action {
  margin-top: 0;
}

.quick-action:hover,
.quick-action:focus-visible {
  border-color: #9fcfc4;
  background: #f2faf7;
  outline: none;
  transform: translateY(-1px);
}

.quick-action--primary {
  border-color: rgba(31, 157, 135, 0.34);
  background: #eef8f5;
}

.quick-action-index {
  color: var(--teal-dark);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 10px;
}

.quick-action-copy {
  min-width: 0;
}

.quick-action-copy strong,
.quick-action-copy small {
  display: block;
}

.quick-action-copy strong {
  overflow: hidden;
  color: var(--ink-900);
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.quick-action-copy small {
  margin-top: 4px;
  overflow: hidden;
  color: var(--ink-500);
  font-size: 11px;
  line-height: 1.5;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.quick-action-arrow {
  color: var(--teal-dark);
  font-size: 17px;
  line-height: 1;
}

.activity-note {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-top: 22px;
  padding-top: 17px;
  border-top: 1px solid var(--line);
}

@media (min-width: 761px) {
  .workspace-activity-panel {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) minmax(250px, 0.85fr);
    align-items: stretch;
    gap: 12px;
  }

  .workspace-activity-panel .section-heading {
    grid-column: 1 / -1;
  }

  .activity-note {
    margin-top: 0;
    padding-top: 0;
    padding-left: 18px;
    border-top: 0;
    border-left: 1px solid var(--line);
  }
}

.activity-dot {
  width: 8px;
  height: 8px;
  flex: 0 0 auto;
  margin-top: 5px;
  border-radius: 50%;
  background: var(--teal);
  box-shadow: 0 0 0 4px rgba(31, 157, 135, 0.12);
}

.activity-note strong {
  color: var(--ink-900);
  font-size: 12px;
}

.activity-note p {
  margin: 5px 0 0;
  color: var(--ink-500);
  font-size: 12px;
  line-height: 1.6;
}

.workspace-page :deep(.el-button--primary) {
  min-height: 42px;
  padding: 0 20px;
  border: 0;
  border-radius: 8px;
  color: var(--ink-950);
  background: var(--teal);
  font-weight: 700;
}

.workspace-page :deep(.el-button--primary:hover) {
  background: #2aaf99;
}

.workspace-page :deep(.el-dialog) {
  border-radius: var(--radius);
  background: var(--surface);
}

.workspace-page :deep(.el-dialog__title) {
  color: var(--ink-950);
  font-weight: 700;
}

.workspace-page :deep(.el-input__wrapper),
.workspace-page :deep(.el-textarea__inner) {
  border: 1px solid var(--line);
  border-radius: 8px;
  box-shadow: none;
}

@media (max-width: 760px) {
  .workspace-page {
    padding: 36px 16px 60px;
  }

  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .page-header :deep(.el-button) {
    width: 100%;
  }

  .workspace-overview {
    grid-template-columns: 1fr;
  }

  .workspace-activity-panel {
    margin-bottom: 18px;
  }

  .quick-action + .quick-action {
    margin-top: 10px;
  }
}
</style>
