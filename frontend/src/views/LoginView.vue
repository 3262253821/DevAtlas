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
    <section class="auth-story">
      <div class="story-grid" aria-hidden="true"></div>
      <div class="story-content">
        <div class="story-brand">
          <span class="brand-mark">D</span>
          <span>DEVATLAS / 01</span>
        </div>
        <p class="story-kicker">研发知识协同平台</p>
        <h1>把团队经验，<br /><em>变成可检索的答案。</em></h1>
        <p class="story-copy">
          文档、故障日志与排查经验汇聚在同一个工作区，
          让每一次定位都有来源可追溯。
        </p>
        <div class="story-footnote">
          <span class="story-line"></span>
          <span>SECURE KNOWLEDGE WORKSPACE</span>
        </div>
      </div>
    </section>

    <section class="auth-form-area">
      <div class="auth-form-wrap">
        <div class="form-heading">
          <p class="eyebrow">WELCOME BACK</p>
          <h2>登录工作区</h2>
          <p>使用你的 DevAtlas 账号继续工作。</p>
        </div>

        <el-form
          class="auth-form"
          :model="form"
          @submit.prevent="submit"
        >
          <el-form-item label="用户名">
            <el-input
              v-model="form.username"
              autocomplete="username"
              placeholder="输入用户名"
            />
          </el-form-item>

          <el-form-item label="密码">
            <el-input
              v-model="form.password"
              type="password"
              show-password
              autocomplete="current-password"
              placeholder="输入密码"
            />
          </el-form-item>

          <el-button
            class="auth-submit"
            type="primary"
            native-type="submit"
            :loading="loading"
          >
            进入工作区 <span aria-hidden="true">↗</span>
          </el-button>
        </el-form>

        <p class="auth-footer">
          还没有账号？
          <RouterLink to="/register">创建一个</RouterLink>
        </p>
      </div>
    </section>
  </main>
</template>
