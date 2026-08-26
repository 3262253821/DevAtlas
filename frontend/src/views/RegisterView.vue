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
    <section class="auth-panel">
      <p class="auth-brand">DevAtlas</p>
      <h1>注册</h1>
      <p class="auth-description">创建一个研发知识协同平台账号</p>

      <el-form :model="form" @submit.prevent="submit">
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
          注册
        </el-button>
      </el-form>

      <p class="auth-footer">
        已有账号？
        <RouterLink to="/login"> 返回登录 </RouterLink>
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
