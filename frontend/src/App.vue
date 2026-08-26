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
    <header
      v-if="showNavigation"
      class="app-header"
    >
      <RouterLink
        class="brand-lockup"
        to="/workspaces"
      >
        <span class="brand-mark">D</span>
        <span>
          <strong>DevAtlas</strong>
          <small>研发知识协同平台</small>
        </span>
      </RouterLink>

      <nav class="main-navigation" aria-label="主导航">
        <RouterLink to="/workspaces">
          <span class="nav-index">01</span>
          知识库
        </RouterLink>

        <RouterLink to="/incidents">
          <span class="nav-index">02</span>
          故障历史
        </RouterLink>
      </nav>

      <div class="user-actions">
        <span class="user-presence" aria-hidden="true"></span>
        <span class="user-name">
          {{ authStore.user?.username || "当前用户" }}
        </span>
        <el-button
          class="logout-button"
          text
          @click="logout"
        >
          退出
        </el-button>
      </div>
    </header>

    <RouterView />
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: var(--paper);
}

.app-header {
  min-height: 72px;
  padding: 0 44px;
  display: flex;
  align-items: center;
  gap: 46px;
  color: #f5f1e8;
  background: var(--ink-950);
  border-bottom: 1px solid rgba(255, 255, 255, 0.09);
}

.brand-lockup {
  display: inline-flex;
  align-items: center;
  gap: 11px;
  color: inherit;
  text-decoration: none;
  white-space: nowrap;
}

.brand-lockup strong,
.brand-lockup small {
  display: block;
}

.brand-lockup strong {
  font-size: 17px;
  letter-spacing: 0.02em;
}

.brand-lockup small {
  margin-top: 2px;
  color: #8592a5;
  font-size: 10px;
  letter-spacing: 0.08em;
}

.brand-mark {
  width: 34px;
  height: 34px;
  display: grid;
  place-items: center;
  color: var(--ink-950);
  background: var(--teal);
  border-radius: 9px;
  font-size: 17px;
  font-weight: 800;
}

.main-navigation {
  display: flex;
  align-items: stretch;
  align-self: stretch;
  gap: 28px;
  flex: 1;
}

.main-navigation a {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 9px;
  color: #aeb8c7;
  font-size: 13px;
  text-decoration: none;
}

.main-navigation a::after {
  content: "";
  position: absolute;
  right: 0;
  bottom: 0;
  left: 0;
  height: 3px;
  background: transparent;
}

.main-navigation a.router-link-active {
  color: #f8f4eb;
}

.main-navigation a.router-link-active::after {
  background: var(--teal);
}

.nav-index {
  color: #68768a;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 10px;
}

.user-actions {
  display: flex;
  align-items: center;
  gap: 9px;
  color: #d8dee8;
  font-size: 12px;
}

.user-presence {
  width: 7px;
  height: 7px;
  background: var(--teal);
  border-radius: 50%;
  box-shadow: 0 0 0 4px rgba(31, 157, 135, 0.14);
}

.logout-button {
  margin-left: 8px;
  color: #aeb8c7 !important;
  font-size: 12px;
}

.logout-button:hover {
  color: #f8f4eb !important;
  background: rgba(255, 255, 255, 0.08) !important;
}

@media (max-width: 760px) {
  .app-header {
    min-height: auto;
    padding: 14px 18px;
    flex-wrap: wrap;
    gap: 14px 22px;
  }

  .main-navigation {
    order: 3;
    width: 100%;
    min-height: 34px;
  }

  .user-actions {
    margin-left: auto;
  }
}
</style>
