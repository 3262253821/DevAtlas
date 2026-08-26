<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "./stores/auth";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const showNavigation = computed(() => {
  return Boolean(route.meta.requiresAuth);
});

async function logout(): Promise<void> {
  authStore.clearSession();
  await router.replace("/login");
}
</script>

<template>
  <div class="app-shell">
    <header v-if="showNavigation" class="app-header">
      <RouterLink class="brand" to="/workspaces"> DevAtlas </RouterLink>

      <nav class="main-navigation">
        <RouterLink to="/workspaces"> 知识库 </RouterLink>

        <RouterLink to="/incidents"> 故障历史 </RouterLink>
      </nav>

      <div class="user-actions">
        <span>
          {{ authStore.user?.username }}
        </span>

        <el-button size="small" @click="logout"> 退出登录 </el-button>
      </div>
    </header>

    <RouterView />
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
}

.app-header {
  height: 60px;
  padding: 0 28px;
  display: flex;
  align-items: center;
  gap: 32px;
  background: #ffffff;
  border-bottom: 1px solid #e4e7ed;
  box-sizing: border-box;
}

.brand {
  color: #303133;
  font-size: 20px;
  font-weight: 700;
  text-decoration: none;
}

.main-navigation {
  display: flex;
  align-items: center;
  gap: 22px;
  flex: 1;
}

.main-navigation a {
  color: #606266;
  text-decoration: none;
}

.main-navigation a.router-link-active {
  color: #409eff;
  font-weight: 600;
}

.user-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #606266;
}

@media (max-width: 700px) {
  .app-header {
    height: auto;
    padding: 14px 16px;
    flex-wrap: wrap;
    gap: 16px;
  }

  .main-navigation {
    order: 3;
    width: 100%;
  }
}
</style>
