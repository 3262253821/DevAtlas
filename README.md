# DevAtlas

研发知识协同平台。

DevAtlas 面向研发和运维团队，集中管理版本化技术知识，并通过 RAG 和大模型辅助故障分析。第一版的核心目标是让用户能够上传团队文档，在权限范围内检索知识，并获得带来源引用的 AI 分析结果。

## 当前技术栈

- 前端：Vue 3、TypeScript、Vite、Element Plus、Pinia、Axios
- 后端：Python 3.13、FastAPI、Uvicorn、Pydantic
- 数据库：MySQL 8、SQLAlchemy 2、PyMySQL、Alembic
- 向量库：Chroma Persistent Client
- Embedding：本地 `BAAI/bge-small-zh-v1.5`
- LLM：DeepSeek（目标模型：`deepseek-v4-flash`）
- 认证：JWT、HTTP Bearer
- 密码安全：Argon2id 哈希
- 流式输出：SSE

## 当前开发状态

当前处于阶段 7 的正式开发阶段，已完成：

- T01：项目基础初始化、FastAPI 健康检查、Vue 项目初始化；
- T02：`.env` 配置管理和配置缺失检查；
- T03：SQLAlchemy、MySQL、Alembic 和 `users` 表迁移；
- T04：用户注册、登录、密码哈希、JWT 签发与当前用户鉴权。
- T05：知识库 CRUD、`owner_id` 所有者绑定和跨用户权限校验。
- T06：文件上传安全校验、原始文件保存和 SHA-256 指纹计算。
- T07：TXT/Markdown/PDF 文档解析、文本切分、逻辑文档与版本管理、重复内容幂等和失败状态保留；优化阶段已补充版本切换和失败回退保障。
- T08：本地 BGE Embedding、Chroma 向量入库、chunk metadata、稳定 `vector_id` 和失败补偿。
- T09：文档列表、详情、版本历史、单版本查询、文档删除和失败版本重新索引。
- T10：问题 Embedding、当前知识库 indexed 版本过滤、Chroma Top-K 检索、上下文组装和来源 metadata 返回。
- T11：DeepSeek 普通调用、RAG Prompt、统一 LLM 错误转换和带来源的普通问答接口。
- T12：知识库问答 SSE 流式输出、token/citation/done/error 事件和 DeepSeek 流式调用。
- T13：故障分析 SSE、incidents/incident_citations 持久化、状态流转、历史查询、详情和删除。
- T14：Vue 前端基础设施、登录注册、知识库工作台、文档管理、普通问答 SSE、故障分析 SSE 和浏览器端完整联调。

下一步：

- T15：测试、修复和交付材料（MVP 已完成）。
- 优化阶段 P0：已完成文档版本切换时机修复、当前 indexed 版本过滤、重复上传幂等、解析/Embedding/Chroma 失败回退和文件边界测试。
- 优化阶段 P1：已完成文档状态常量、处理阶段日志、前端状态中文映射，以及 Top-K、无答案和引用 metadata 的可复现检索测试。
- 优化阶段下一步：P2 评估 LangChain 编排层适配；Redis、MCP、多 Agent 等仍不主动加入。

## 项目结构

```text
E:\RagKnowledgeSystem
├── backend
│   ├── app
│   │   ├── core          # 配置、安全工具、认证依赖
│   │   ├── db            # SQLAlchemy Base、Engine、Session
│   │   ├── models        # ORM 模型
│   │   ├── routers       # HTTP 路由
│   │   ├── schemas       # 请求和响应模型
│   │   └── services      # 业务逻辑
│   ├── alembic           # 数据库迁移配置和版本
│   └── requirements.txt
├── frontend              # Vue + TypeScript 前端
│   └── src
│       ├── api           # Axios、SSE 和业务接口封装
│       ├── router        # 页面路由和登录守卫
│       ├── stores        # Pinia 登录状态
│       └── views         # 登录、知识库、文档、问答和故障页面
├── docs                  # PRD、技术方案、API 和阶段总结
├── tests                 # 自动化测试
└── others                # 本地生成文件，不放业务源码
```

## 环境配置

复制配置模板：

```powershell
Copy-Item .env.example .env
```

然后在 `.env` 中配置本机 MySQL、JWT 和 DeepSeek 参数。真实密码、JWT 密钥和 API Key 只保存在 `.env`，不要提交到 Git。

当前数据库配置约定：

```text
MySQL: 127.0.0.1:3306
Database: dev_atlas
User: root
```

## 启动后端

在项目根目录执行：

```powershell
python -m uvicorn app.main:app --reload --app-dir backend --host 127.0.0.1 --port 8000
```

健康检查：

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/health/db
```

Swagger：

```text
http://127.0.0.1:8000/docs
```

## 启动前端

```powershell
Set-Location frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

前端地址：

```text
http://127.0.0.1:5173
```

前端通过 `frontend/.env.local` 中的 `VITE_API_BASE_URL` 请求后端，默认后端端口为 `8000`。该文件只保存本地地址，不提交到 Git。

## 当前前端联调功能（T14）

已完成浏览器主链路：

```text
注册 → 登录 → 创建知识库 → 上传文档 → indexed
→ RAG 问答 SSE → 故障分析 SSE → 查看历史 → 删除记录 → 退出登录
```

主要页面：

- `/login`、`/register`：登录和注册；
- `/workspaces`：当前用户知识库列表、创建和删除；
- `/knowledge/:id`：知识库工作台；
- `/knowledge/:id/documents`：文档上传、状态、删除和重新索引；
- `/knowledge/:id/qa`：普通问答 SSE 和引用展示；
- `/knowledge/:id/incidents/new`：故障分析 SSE；
- `/incidents`：故障分析历史、详情和删除。

前端使用 Axios 统一携带 JWT，使用 `fetch + ReadableStream` 解析 SSE 的 `token`、`citation`、`done` 和 `error` 事件。后端通过 CORS 允许本地 `5173` 前端访问 `8000` API。

## 数据库迁移

在项目根目录执行：

```powershell
alembic upgrade head
```

查看当前迁移版本：

```powershell
alembic current
```

数据库结构变更必须通过 Alembic，不直接手动修改生产表结构。

## 当前认证接口

接口前缀：`/api/v1/auth`

### 注册

```text
POST /api/v1/auth/register
```

请求：

```json
{
  "username": "alice",
  "password": "password123"
}
```

用户名长度为 3-50，密码长度为 8-128。密码经过 Argon2id 哈希后才保存到 MySQL。

### 登录

```text
POST /api/v1/auth/login
```

登录成功后返回 JWT `access_token`。登录接口使用 JSON 请求体，不是 OAuth2 Password Flow 的表单请求。

### 当前用户

```text
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

服务端验证 JWT 后，根据 Token 中的用户 ID 查询当前用户，并检查用户是否仍然存在且处于启用状态。

## 已验证的认证场景

- 正常注册：`201 Created`；
- 重复用户名：`409 Conflict`；
- 注册密码过短：`422 Unprocessable Entity`；
- 正确登录：`200 OK`，返回 access token；
- 错误密码：`401 Unauthorized`；
- 无 Token 访问 `/me`：`401 Unauthorized`；
- 伪造或失效 Token：`401 Unauthorized`；
- 合法 Token 访问 `/me`：`200 OK`。

## 当前知识库接口

接口前缀：`/api/v1/knowledge-bases`

- `POST /api/v1/knowledge-bases`：创建知识库；
- `GET /api/v1/knowledge-bases`：查询当前用户自己的知识库；
- `GET /api/v1/knowledge-bases/{knowledge_base_id}`：查询当前用户有权访问的知识库；
- `DELETE /api/v1/knowledge-bases/{knowledge_base_id}`：删除当前用户自己的知识库。

知识库的 `owner_id` 由服务端根据 JWT 中的当前用户确定，不信任客户端传入的所有者 ID。详情和删除查询同时校验资源 ID 与 `owner_id`；其他用户访问时返回 `404`，避免泄露资源是否存在。同一用户下知识库名称不能重复，重复创建返回 `409`。

已验证用户 A、用户 B 的跨用户访问边界：用户 B 看不到、读取不了、删除不了用户 A 的知识库。

## 当前文件上传接口

```text
POST /api/v1/knowledge-bases/{knowledge_base_id}/documents
```

T06 当前已完成原始文件的安全保存：

- 允许 `.md`、`.txt`、`.pdf`；
- 单文件最大 10 MB；
- 规范化文件名并清理控制字符；
- 使用随机存储名，避免同名覆盖；
- 校验最终路径必须位于 `others/uploads` 内；
- 分块写入文件并计算 SHA-256；
- 拒绝空文件、非法格式和超大文件；
- 上传失败时清理半成品；
- 上传前校验当前用户是否拥有目标知识库。

上传接口会继续执行文档解析、文本切分、版本状态更新、Embedding 和 Chroma 入库；成功版本为 `indexed`，处理失败会保留 `failed` 版本和错误信息。

### 文档版本可靠性保障（优化阶段 P0）

新版本创建后先保持 `pending`，不会立即覆盖逻辑文档的 `current_version_id`。只有解析、切分、Embedding、Chroma 写入和 MySQL chunk 保存全部成功后，才将新版本切换为当前版本并标记为 `indexed`。任一步失败时，新版本记录为 `failed` 并保存错误原因，旧的 `indexed` 版本继续参与检索；如果 Chroma 已写入部分向量，还会执行补偿删除，避免 MySQL 与 Chroma 出现孤立数据。

优化阶段已通过以下自动化验证：

- 解析失败、Embedding 失败、Chroma 写入失败时旧版本仍可检索；
- 失败版本的错误原因会被保留；
- 重复内容通过 SHA-256 幂等处理，不创建新版本并清理临时文件；
- 路径穿越、非法扩展名、文件名规范化和空文本 PDF 等边界输入有明确失败结果。

测试命令：

```powershell
python -m pytest tests -q
```

当前结果：`18 passed`，仅有第三方依赖的 `DeprecationWarning`，不影响测试通过。

## 当前文档管理接口（T09）

所有接口都需要携带：

```text
Authorization: Bearer <access_token>
```

- `GET /api/v1/knowledge-bases/{knowledge_base_id}/documents`：分页查询知识库文档，可按 `status=pending|indexed|failed` 筛选；
- `GET /api/v1/knowledge-bases/{knowledge_base_id}/documents/{document_id}`：查询文档详情和当前版本；
- `GET /api/v1/knowledge-bases/{knowledge_base_id}/documents/{document_id}/versions`：查询版本历史；
- `GET /api/v1/knowledge-bases/{knowledge_base_id}/documents/{document_id}/versions/{version_id}`：查询指定版本；
- `DELETE /api/v1/knowledge-bases/{knowledge_base_id}/documents/{document_id}`：删除文档、版本、chunk、原始文件和向量；
- `POST /api/v1/knowledge-bases/{knowledge_base_id}/documents/{document_id}/reindex`：重新处理该文档最新的 `failed` 版本。

路径中的 ID 含义：`knowledge_base_id` 是知识库 ID，`document_id` 是逻辑文档 ID，`version_id` 是 `document_versions.id` 的版本记录主键；`version_number` 只是同一逻辑文档内的版本序号，不能替代 `version_id`。

T09 的删除顺序为先清理 Chroma 向量，再删除原始文件，最后删除 MySQL 业务记录，避免数据库删除后丢失向量清理所需的 `vector_id`。没有 `failed` 版本时调用重新索引接口返回 `409 Conflict` 属于正常业务结果。

## 当前 RAG 检索接口（T10）

```text
POST /api/v1/knowledge-bases/{knowledge_base_id}/search
```

请求体：

```json
{
  "question": "忘记密码后应该怎么办？",
  "top_k": 3
}
```

检索流程为：先校验当前用户是否拥有知识库，再从 MySQL 找出该知识库中状态为 `indexed` 的版本，将问题转换为 Embedding，使用知识库 ID、版本 ID 和 `is_searchable=true` 作为 Chroma metadata 过滤条件，最后返回距离最小的 Top-K 文档块。

接口返回 `context` 和 `sources`，其中 `context` 是检索到的原文拼接结果，`sources` 包含文档 ID、版本 ID、版本号、chunk 序号、文件名和距离。T10 只负责检索，不负责调用 DeepSeek 生成最终答案。

已验证：合法 Token 和知识库可以返回文档块及来源 metadata；没有可检索版本时返回空上下文；跨用户知识库返回 `404`；无 Token 返回 `401`；`top_k` 超出 1-10 范围返回 `422`。

## 当前普通问答接口（T11）

```text
POST /api/v1/knowledge-bases/{knowledge_base_id}/qa
```

请求体：

```json
{
  "question": "你的文档中写的主要内容是什么？",
  "top_k": 3
}
```

接口先复用 T10 检索当前知识库的相关文档块，再把问题和上下文组装成 RAG Prompt，调用 DeepSeek `deepseek-v4-flash`，最后返回普通 JSON。

返回结构包含：

- `question`：用户问题；
- `answer`：DeepSeek 根据上下文生成的回答；
- `sources`：T10 返回的文档、版本、chunk 和距离信息。

如果没有检索到来源，接口不会调用大模型，而是返回知识库没有相关内容的提示。DeepSeek 配置缺失、网络失败、超时或返回异常时统一返回 `502 Bad Gateway`。T11 只返回完整 JSON，流式输出留给 T12。

## 当前知识库问答 SSE 接口（T12）

```text
POST /api/v1/knowledge-bases/{knowledge_base_id}/qa/stream
```

请求体：

```json
{
  "question": "你的文档中写的主要内容是什么？",
  "top_k": 3,
  "conversation_id": null
}
```

接口复用 T10 的检索和 T11 的 RAG Prompt，通过 DeepSeek 流式调用逐段返回回答。事件顺序通常为：多个 `token`，随后多个 `citation`，最后是 `done`。流式调用中发生错误时发送 `error` 事件。

事件示例：

```text
event: token
data: {"text":"回答片段"}

event: citation
data: {"index":1,"document_id":2,"version_id":2,"chunk_index":29,"filename":"文档.txt","distance":0.55}

event: done
data: {"conversation_id":null,"message_id":null}
```

`top_k` 表示最多检索多少个最相似文档块，不限制最终回答长度。当前阶段暂不保存问答历史，因此 `conversation_id` 和 `message_id` 仅保留接口结构，值可以为 `null`。

T12 使用 OpenAI 兼容客户端处理 DeepSeek SSE 响应，避免手写解析空行和事件边界导致流式解析失败。已验证：合法请求能够返回 `token → citation → done`；无相关文档时返回提示 token 和 `done`；未登录返回 `401`；跨用户知识库返回 `404`；参数不合法返回 `422`。

## 当前故障分析接口（T13）

故障分析使用独立的 incident 业务记录，不会把分析结果写回知识库文档。

```text
POST /api/v1/knowledge-bases/{knowledge_base_id}/incidents/stream
GET /api/v1/incidents
GET /api/v1/incidents/{incident_id}
DELETE /api/v1/incidents/{incident_id}
```

故障分析请求：

```json
{
  "title": "订单服务返回 502",
  "content": "网关返回 502，订单服务无法连接数据库，请根据知识库给出排查步骤。"
}
```

处理流程：创建 `streaming` incident → 复用 T10 检索故障相关文档块 → 使用故障专用 Prompt 调用 DeepSeek → SSE 返回 `token` 和 `citation` → 完成后保存分析结果和引用并更新为 `completed`。LLM 失败时更新为 `failed`，客户端中断时更新为 `cancelled`。

T13 新增 P0 表 `incidents` 和 `incident_citations`。所有 incident 查询、详情和删除都按当前用户的 `owner_id` 过滤，其他用户访问统一返回 `404`。

## Git 提交约定

每完成一个可验证功能再提交：

```powershell
git status
git add <本次修改的文件>
git commit -m "<type>: <description>"
git log -1 --oneline
```

`.env`、`node_modules`、上传文件和本地向量数据不会提交到仓库。
