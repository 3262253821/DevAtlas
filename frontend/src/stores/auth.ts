import { computed, ref } from "vue";
import { defineStore } from "pinia";

const TOKEN_KEY = "dev_atlas_access_token";
const USER_KEY = "dev_atlas_user";

export interface UserPublic {
  id: number;
  username: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

function readStoredUser(): UserPublic | null {
  const rawUser = localStorage.getItem(USER_KEY);

  if (!rawUser) {
    return null;
  }

  try {
    return JSON.parse(rawUser) as UserPublic;
  } catch {
    localStorage.removeItem(USER_KEY);
    return null;
  }
}

export const useAuthStore = defineStore("auth", () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY));

  const user = ref<UserPublic | null>(readStoredUser());

  const isAuthenticated = computed(() => {
    return Boolean(token.value);
  });

  function setSession(accessToken: string, userInfo: UserPublic): void {
    token.value = accessToken;
    user.value = userInfo;

    localStorage.setItem(TOKEN_KEY, accessToken);
    localStorage.setItem(USER_KEY, JSON.stringify(userInfo));
  }

  function clearSession(): void {
    token.value = null;
    user.value = null;

    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  function restoreSession(): void {
    token.value = localStorage.getItem(TOKEN_KEY);
    user.value = readStoredUser();
  }

  return {
    token,
    user,
    isAuthenticated,
    setSession,
    clearSession,
    restoreSession,
  };
});
