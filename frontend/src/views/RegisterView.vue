<script setup lang="ts">
import { computed, reactive, ref } from "vue";
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

// 这些计算属性会随着输入实时更新，用于把后端的长度约束提前反馈给用户。
const usernameError = computed(() => {
  const length = form.username.trim().length;

  if (length > 0 && length < 3) {
    return "用户名至少需要 3 个字符";
  }

  if (length > 50) {
    return "用户名不能超过 50 个字符";
  }

  return "";
});

const passwordError = computed(() => {
  if (form.password.length > 0 && form.password.length < 8) {
    return "密码至少需要 8 个字符";
  }

  if (form.password.length > 128) {
    return "密码不能超过 128 个字符";
  }

  return "";
});

const confirmPasswordError = computed(() => {
  if (
    form.confirmPassword.length > 0 &&
    form.password !== form.confirmPassword
  ) {
    return "两次输入的密码不一致";
  }

  return "";
});

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
  if (!form.username.trim()) {
    ElMessage.warning("请输入用户名");
    return;
  }

  if (usernameError.value) {
    ElMessage.warning(usernameError.value);
    return;
  }

  if (!form.password) {
    ElMessage.warning("请输入密码");
    return;
  }

  if (passwordError.value) {
    ElMessage.warning(passwordError.value);
    return;
  }

  if (!form.confirmPassword) {
    ElMessage.warning("请确认密码");
    return;
  }

  if (confirmPasswordError.value) {
    ElMessage.warning(confirmPasswordError.value);
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
    <section class="auth-visual" aria-label="DevAtlas 视觉标识">
      <div class="visual-grid" aria-hidden="true"></div>
      <div class="visual-topbar">
        <div class="visual-brand">
          <span class="visual-mark">D</span>
          <span>DevAtlas <small>研发知识协同平台</small></span>
        </div>
      </div>

      <div class="visual-stage" aria-hidden="true">
        <div class="stage-shadow"></div>
        <div class="stage-platform"></div>
        <div class="stage-rail"></div>
        <div class="stage-orbit"></div>
        <div class="stage-core"></div>
      </div>
    </section>

    <section class="auth-form-area">
      <div class="auth-form-wrap">
        <div class="form-heading">
          <p class="eyebrow">CREATE ACCOUNT</p>
          <h2>创建 DevAtlas 账号</h2>
          <p>注册后即可建立你的研发知识工作区。</p>
        </div>

        <el-form
          class="auth-form auth-form--register"
          :model="form"
          @submit.prevent="submit"
        >
          <el-form-item
            label="用户名"
            :error="usernameError || undefined"
            :validate-status="usernameError ? 'error' : ''"
          >
            <el-input
              v-model="form.username"
              autocomplete="username"
              placeholder="3-50 个字符"
            />
          </el-form-item>

          <el-form-item
            label="密码"
            :error="passwordError || undefined"
            :validate-status="passwordError ? 'error' : ''"
          >
            <el-input
              v-model="form.password"
              type="password"
              show-password
              autocomplete="new-password"
              placeholder="至少 8 个字符"
            />
          </el-form-item>

          <el-form-item
            label="确认密码"
            :error="confirmPasswordError || undefined"
            :validate-status="confirmPasswordError ? 'error' : ''"
          >
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
