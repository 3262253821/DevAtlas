<script setup lang="ts">
import { reactive, ref } from "vue";
import { isAxiosError } from "axios";
import { ElMessage } from "element-plus";
import { useRouter } from "vue-router";
import { register } from "../api/auth";

const router = useRouter();

const form = reactive({
  username: "",
  password: "",
  confirmPassword: "",
});

const loading = ref(false);

function getErrorMessage(error: unknown): string {
  if (isAxiosError<{ detail?: string }>(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }
  }

  return "注册失败，请稍后重试";
}

async function submit(): Promise<void> {
  if (form.username.trim().length < 3) {
    ElMessage.warning("用户名至少需要 3 个字符");
    return;
  }

  if (form.password.length < 8) {
    ElMessage.warning("密码至少需要 8 个字符");
    return;
  }

  if (form.password !== form.confirmPassword) {
    ElMessage.warning("两次输入的密码不一致");
    return;
  }

  loading.value = true;

  try {
    await register({
      username: form.username.trim(),
      password: form.password,
    });

    ElMessage.success("注册成功，请登录");
    await router.replace("/login");
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
          <span>DEVATLAS / 00</span>
        </div>
        <p class="story-kicker">建立你的第一个工作区</p>
        <h1>让经验<br /><em>留下路径。</em></h1>
        <p class="story-copy">
          从一份文档开始，把团队的知识、上下文与排障经验组织起来。
        </p>
        <div class="story-footnote">
          <span class="story-line"></span>
          <span>KNOWLEDGE THAT MOVES WITH THE TEAM</span>
        </div>
      </div>
    </section>

    <section class="auth-form-area">
      <div class="auth-form-wrap">
        <div class="form-heading">
          <p class="eyebrow">CREATE ACCOUNT</p>
          <h2>创建账号</h2>
          <p>注册后即可建立你的第一个研发知识库。</p>
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
              placeholder="3-50 个字符"
            />
          </el-form-item>

          <el-form-item label="密码">
            <el-input
              v-model="form.password"
              type="password"
              show-password
              autocomplete="new-password"
              placeholder="至少 8 个字符"
            />
          </el-form-item>

          <el-form-item label="确认密码">
            <el-input
              v-model="form.confirmPassword"
              type="password"
              show-password
              autocomplete="new-password"
              placeholder="再次输入密码"
            />
          </el-form-item>

          <el-button
            class="auth-submit"
            type="primary"
            native-type="submit"
            :loading="loading"
          >
            创建账号 <span aria-hidden="true">↗</span>
          </el-button>
        </el-form>

        <p class="auth-footer">
          已有账号？
          <RouterLink to="/login">返回登录</RouterLink>
        </p>
      </div>
    </section>
  </main>
</template>
