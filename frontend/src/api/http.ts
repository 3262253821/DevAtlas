import axios from "axios";

const TOKEN_KEY = "dev_atlas_access_token";

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

// 每次发送请求前，自动从浏览器本地存储读取 JWT
http.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);

  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

// 后端返回 401 时，清理失效 Token
http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem("dev_atlas_user");
    }

    return Promise.reject(error);
  },
);

export default http;
