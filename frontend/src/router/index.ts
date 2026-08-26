import {
  createRouter,
  createWebHistory,
  type RouteRecordRaw,
} from "vue-router";
import { useAuthStore } from "../stores/auth";
import LoginView from "../views/LoginView.vue";
import RegisterView from "../views/RegisterView.vue";
import WorkspacesView from "../views/WorkspacesView.vue";
import KnowledgeWorkspaceView from "../views/KnowledgeWorkspaceView.vue";
import DocumentsView from "../views/DocumentsView.vue";
import QaView from "../views/QaView.vue";
import IncidentNewView from "../views/IncidentNewView.vue";
import IncidentsView from "../views/IncidentsView.vue";
import LegalView from "../views/LegalView.vue";

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    redirect: "/workspaces",
  },
  {
    path: "/login",
    name: "login",
    component: LoginView,
  },
  {
    path: "/register",
    name: "register",
    component: RegisterView,
  },
  {
    path: "/legal/terms",
    name: "terms",
    component: LegalView,
  },
  {
    path: "/legal/privacy",
    name: "privacy",
    component: LegalView,
  },
  {
    path: "/workspaces",
    name: "workspaces",
    component: WorkspacesView,
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: "/knowledge/:id",
    name: "knowledge",
    component: KnowledgeWorkspaceView,
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: "/knowledge/:id/documents",
    name: "documents",
    component: DocumentsView,
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: "/knowledge/:id/qa",
    name: "qa",
    component: QaView,
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: "/knowledge/:id/incidents/new",
    name: "incident-new",
    component: IncidentNewView,
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: "/incidents",
    name: "incidents",
    component: IncidentsView,
    meta: {
      requiresAuth: true,
    },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// 进入受保护页面前，检查 Pinia 中是否存在 Token
router.beforeEach((to) => {
  const authStore = useAuthStore();

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return {
      name: "login",
      query: {
        redirect: to.fullPath,
      },
    };
  }

  if (
    (to.name === "login" || to.name === "register") &&
    authStore.isAuthenticated
  ) {
    return {
      name: "workspaces",
    };
  }

  return true;
});

export default router;
