# DevAtlas

研发知识协同平台。

面向研发和运维团队，集中管理版本化技术知识，并通过 RAG 和大模型辅助故障分析。

## 当前技术栈

- 前端：Vue 3、TypeScript、Vite、Element Plus、Pinia
- 后端：Python、FastAPI、Uvicorn
- 数据库：MySQL
- 向量库：Chroma
- Embedding：BAAI/bge-small-zh-v1.5
- LLM：DeepSeek
- 认证：JWT
- 流式输出：SSE

## 当前开发状态

当前正在完成阶段 7 的 T01：项目基础初始化。

## 启动后端

```powershell
python -m uvicorn app.main:app --reload --app-dir backend --host 127.0.0.1 --port 8000
```
