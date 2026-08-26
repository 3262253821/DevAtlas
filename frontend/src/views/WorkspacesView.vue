<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
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
        <p class="eyebrow">DevAtlas</p>
        <h1>我的知识库</h1>
        <p class="description">管理研发文档，并进入对应知识库工作台。</p>
      </div>

      <el-button type="primary" @click="openCreateDialog">
        创建知识库
      </el-button>
    </header>

    <el-card v-loading="loading" class="workspace-card">
      <el-empty
        v-if="!loading && workspaces.length === 0"
        description="还没有知识库"
      />

      <el-table v-else :data="workspaces" row-key="id">
        <el-table-column prop="name" label="名称" min-width="220" />

        <el-table-column prop="description" label="描述" min-width="300">
          <template #default="{ row }">
            {{ row.description || "暂无描述" }}
          </template>
        </el-table-column>

        <el-table-column label="创建时间" width="190">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openWorkspace(row)">
              进入
            </el-button>

            <el-button link type="danger" @click="removeWorkspace(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

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
  color: var(--ink-500);
  font-size: 14px;
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
}
</style>
