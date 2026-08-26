<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();

const isPrivacy = computed(() => route.name === "privacy");
const title = computed(() => {
  return isPrivacy.value ? "隐私政策" : "服务协议";
});
</script>

<template>
  <main class="legal-page">
    <article class="legal-sheet">
      <button
        class="legal-back"
        type="button"
        @click="router.back()"
      >
        ← 返回
      </button>

      <p class="legal-kicker">DEVATLAS / POLICY</p>
      <h1>{{ title }}</h1>
      <p class="legal-updated">最后更新：2026 年 8 月 26 日</p>

      <template v-if="!isPrivacy">
        <h2>1. 服务范围</h2>
        <p>
          DevAtlas 用于整理团队研发文档、检索知识内容和辅助故障分析。你可以在自己的知识库中上传资料、发起问答并查看分析记录。
        </p>

        <h2>2. 内容责任</h2>
        <p>
          你应当确保上传内容属于你或已获得合法授权。AI 返回的内容是基于知识库检索结果生成的辅助建议，不能替代人工判断和生产变更审批。
        </p>

        <h2>3. 使用规范</h2>
        <p>
          不得上传法律禁止传播的内容，不得利用平台尝试越权访问其他用户的知识库，也不得将平台生成的建议直接用于未经验证的高风险操作。
        </p>
      </template>

      <template v-else>
        <h2>1. 我们保存什么</h2>
        <p>
          平台会保存你的用户名、知识库资料、文档版本、检索片段和故障分析记录，用于提供登录、检索、问答和历史查询功能。
        </p>

        <h2>2. 数据使用</h2>
        <p>
          你的数据仅用于当前账号的产品功能。知识库和分析记录按用户权限隔离，不会向其他账号展示。调用大模型时，只发送完成当前问题所需的上下文。
        </p>

        <h2>3. 数据安全</h2>
        <p>
          密码以不可逆哈希保存，接口使用身份令牌进行鉴权。请妥善保管账号信息，不要在截图或聊天中公开访问令牌、API Key 和敏感日志。
        </p>
      </template>
    </article>
  </main>
</template>

<style scoped>
.legal-page {
  min-height: 100vh;
  padding: 56px 20px;
  background: var(--paper);
}

.legal-sheet {
  width: min(100%, 760px);
  margin: 0 auto;
  padding: 44px 48px 52px;
  border: 1px solid var(--line);
  border-radius: 16px;
  background: var(--surface);
  box-shadow: var(--shadow-card);
}

.legal-back {
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid #c9d9df;
  border-radius: 7px;
  color: #23796f;
  background: #eaf6f3;
  box-shadow: 0 2px 6px rgba(37, 54, 78, 0.06);
  cursor: pointer;
  font-size: 13px;
  font-weight: 650;
  transition: color 160ms ease, background 160ms ease, border-color 160ms ease,
    transform 160ms ease;
}

.legal-back:hover,
.legal-back:focus-visible {
  border-color: #8fcabd;
  color: #125f56;
  background: #d8f0ea;
  transform: translateY(-1px);
}

.legal-kicker {
  margin: 46px 0 12px;
  color: var(--teal-dark);
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 10px;
  letter-spacing: 0.16em;
}

.legal-sheet h1 {
  margin: 0 0 8px;
  color: var(--ink-950);
  font-size: 38px;
  letter-spacing: -0.04em;
}

.legal-updated {
  margin-bottom: 38px;
  color: var(--ink-500);
  font-size: 12px;
}

.legal-sheet h2 {
  margin: 28px 0 8px;
  color: var(--ink-900);
  font-size: 17px;
}

.legal-sheet p:not(.legal-kicker):not(.legal-updated) {
  margin: 0;
  color: var(--ink-700);
  font-size: 14px;
  line-height: 1.85;
}

@media (max-width: 600px) {
  .legal-page {
    padding: 24px 16px;
  }

  .legal-sheet {
    padding: 28px 22px 34px;
  }
}
</style>
