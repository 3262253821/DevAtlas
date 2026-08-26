import {
  createRouter,
  createWebHistory,
  type RouteRecordRaw,
} from "vue-router";
import { useAuthStore } from "../stores/auth";
import RoutePlaceholder from "../views/RoutePlaceholder.vue";

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    redirect: "/workspaces",
  },
  {
    path: "/login",
    name: "login",
    component: RoutePlaceholder,
    props: {
      title: "登录页（T14-B 实现）",
    },
  },
  {
    path: "/register",
    name: "register",
    component: RoutePlaceholder,
    props: {
      title: "注册页（T14-B 实现）",
    },
  },
  {
    path: "/workspaces",
    name: "workspaces",
    component: RoutePlaceholder,
    props: {
      title: "知识库列表（T14-C 实现）",
    },
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: "/knowledge/:id",
    name: "knowledge",
    component: RoutePlaceholder,
    props: {
      title: "知识库工作台（T14-C 实现）",
    },
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
