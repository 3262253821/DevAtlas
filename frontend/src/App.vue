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
  <div
    class="app-shell"
    :class="{ 'app-shell--sidebar': showNavigation }"
  >
    <aside
      v-if="showNavigation"
      class="app-sidebar"
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
    </aside>

    <div class="app-content">
      <RouterView />
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  background: var(--paper);
}

.app-shell--sidebar {
  padding-left: 248px;
}

.app-content {
  min-width: 0;
  min-height: 100vh;
}

.app-sidebar {
  position: fixed;
  z-index: 20;
  top: 0;
  bottom: 0;
  left: 0;
  width: 248px;
  display: flex;
  flex-direction: column;
  padding: 28px 20px 22px;
  color: #f5f1e8;
  background: var(--ink-950);
  border-right: 1px solid rgba(255, 255, 255, 0.09);
  box-shadow: 8px 0 28px rgba(10, 18, 32, 0.08);
}

.brand-lockup {
  display: inline-flex;
  align-items: center;
  gap: 11px;
  color: inherit;
  text-decoration: none;
  white-space: nowrap;
}

.app-sidebar .brand-lockup {
  width: 100%;
  padding: 2px 4px 28px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.09);
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
  flex-direction: column;
  gap: 8px;
  margin-top: 28px;
}

.main-navigation a {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 9px;
  min-height: 44px;
  padding: 0 13px;
  border-radius: 8px;
  color: #aeb8c7;
  font-size: 13px;
  text-decoration: none;
  transition: color 160ms ease, background 160ms ease;
}

.main-navigation a::after {
  content: "";
  position: absolute;
  top: 9px;
  bottom: 9px;
  left: 0;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: transparent;
}

.main-navigation a.router-link-active {
  color: #f8f4eb;
  background: rgba(255, 255, 255, 0.07);
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
  margin-top: auto;
  padding: 18px 4px 0;
  border-top: 1px solid rgba(255, 255, 255, 0.09);
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
  margin-left: auto;
  color: #aeb8c7 !important;
  font-size: 12px;
}

.logout-button:hover {
  color: #f8f4eb !important;
  background: rgba(255, 255, 255, 0.08) !important;
}

@media (max-width: 760px) {
  .app-shell--sidebar {
    padding-left: 0;
  }

  .app-sidebar {
    position: sticky;
    width: auto;
    min-height: 66px;
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    align-items: center;
    padding: 12px 18px;
    border-right: 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.09);
    box-shadow: 0 6px 18px rgba(10, 18, 32, 0.08);
  }

  .app-sidebar .brand-lockup {
    width: auto;
    padding: 0;
    border-bottom: 0;
  }

  .app-sidebar .brand-lockup small {
    display: none;
  }

  .main-navigation {
    flex-direction: row;
    justify-content: center;
    gap: 4px;
    margin: 0 12px;
  }

  .main-navigation a {
    min-height: 38px;
    padding: 0 10px;
  }

  .main-navigation a::after {
    top: auto;
    right: 10px;
    bottom: 0;
    left: 10px;
    width: auto;
    height: 2px;
    border-radius: 2px 2px 0 0;
  }

  .user-actions {
    margin-top: 0;
    padding: 0;
    border-top: 0;
  }

  .user-name {
    max-width: 70px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .logout-button {
    margin-left: 2px;
  }
}

@media (max-width: 480px) {
  .app-sidebar {
    grid-template-columns: auto auto;
    gap: 12px;
  }

  .main-navigation {
    order: 3;
    grid-column: 1 / -1;
    justify-content: flex-start;
    margin: 0;
  }

  .user-actions {
    margin-left: auto;
  }

  .user-name {
    display: none;
  }
}

/* Keep the right-hand application surface as the only scrolling region on desktop. */
@media (min-width: 761px) {
  .app-content {
    min-height: 100vh;
  }
}

/* Legacy header rule intentionally removed; navigation is now the fixed sidebar. */
@media (max-width: 760px) {
  .app-content {
    min-height: calc(100vh - 66px);
  }
}
</style>
