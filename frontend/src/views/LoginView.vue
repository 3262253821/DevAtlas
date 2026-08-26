<script setup lang="ts">
import { reactive, ref } from "vue";
import { isAxiosError } from "axios";
import { ElMessage } from "element-plus";
import { useRoute, useRouter } from "vue-router";
import { login } from "../api/auth";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const form = reactive({
  username: "",
  password: "",
});

const loading = ref(false);

function getErrorMessage(error: unknown): string {
  if (isAxiosError<{ detail?: string }>(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }
  }

  return "登录失败，请稍后重试";
}

async function submit(): Promise<void> {
  if (!form.username.trim() || !form.password) {
    ElMessage.warning("请输入用户名和密码");
    return;
  }

  loading.value = true;

  try {
    const result = await login({
      username: form.username.trim(),
      password: form.password,
    });

    authStore.setSession(result.access_token, result.user);

    const redirect =
      typeof route.query.redirect === "string"
        ? route.query.redirect
        : "/workspaces";

    await router.replace(redirect);
    ElMessage.success("登录成功");
  } catch (error) {
    ElMessage.error(getErrorMessage(error));
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <main class="auth-page">
    <section class="auth-panel">
      <p class="auth-brand">DevAtlas</p>
      <h1>登录</h1>
      <p class="auth-description">登录后进入你的研发知识工作区</p>

      <el-form :model="form" @submit.prevent="submit">
        <el-form-item label="用户名">
          <el-input
            v-model="form.username"
            autocomplete="username"
            placeholder="请输入用户名"
          />
        </el-form-item>

        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            autocomplete="current-password"
            placeholder="请输入密码"
          />
        </el-form-item>

        <el-button
          class="auth-submit"
          type="primary"
          native-type="submit"
          :loading="loading"
        >
          登录
        </el-button>
      </el-form>

      <p class="auth-footer">
        还没有账号？
        <RouterLink to="/register"> 去注册 </RouterLink>
      </p>
    </section>
  </main>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background: #f4f6f8;
}

.auth-panel {
  width: min(100%, 420px);
  padding: 36px;
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  box-sizing: border-box;
}

.auth-brand {
  margin-bottom: 12px;
  color: #409eff;
  font-weight: 700;
}

.auth-panel h1 {
  margin: 0 0 8px;
  font-size: 30px;
}

.auth-description {
  margin-bottom: 28px;
  color: #606266;
}

.auth-submit {
  width: 100%;
}

.auth-footer {
  margin-top: 20px;
  text-align: center;
  color: #606266;
}
</style>
