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
const agreed = ref(false);
const policyShaking = ref(false);

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
  if (!agreed.value) {
    showPolicyWarning();
    return;
  }

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

function showPolicyWarning(): void {
  policyShaking.value = true;
  ElMessage.warning("请先同意服务协议与隐私政策");

  window.setTimeout(() => {
    policyShaking.value = false;
  }, 420);
}

function guardSubmitClick(event: MouseEvent): void {
  if (agreed.value) {
    return;
  }

  event.preventDefault();
  event.stopPropagation();
  showPolicyWarning();
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
      <div class="auth-form-wrap auth-panel">
        <div class="form-heading">
          <p class="eyebrow">WELCOME BACK</p>
          <h2>欢迎使用 DevAtlas</h2>
          <p>进入你的研发知识工作区。</p>
        </div>

        <el-form
          class="auth-form"
          :model="form"
          @submit.prevent="submit"
          @keydown.enter.prevent="submit"
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

          <div
            class="policy-row"
            :class="{ 'policy-row--shake': policyShaking }"
          >
            <el-checkbox v-model="agreed">
              我同意
              <RouterLink
                class="policy-link"
                to="/legal/terms"
                @click.stop
              >
                《服务协议》
              </RouterLink>
              与
              <RouterLink
                class="policy-link"
                to="/legal/privacy"
                @click.stop
              >
                《隐私政策》
              </RouterLink>
            </el-checkbox>
          </div>

          <div
            class="auth-submit-wrap"
            :class="{ 'auth-submit-wrap--disabled': !agreed }"
            @click.capture="guardSubmitClick"
          >
            <el-button
              class="auth-submit"
              type="primary"
              native-type="submit"
              :loading="loading"
              :disabled="!agreed"
            >
              进入工作区 <span aria-hidden="true">↗</span>
            </el-button>
          </div>
        </el-form>

        <p class="auth-footer">
          还没有账号？
          <RouterLink to="/register">创建一个</RouterLink>
        </p>
      </div>
    </section>
  </main>
</template>
