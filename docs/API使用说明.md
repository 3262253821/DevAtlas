# DevAtlas API 使用说明

本文档依据 `backend/app/routers/` 下的真实路由代码编写，描述当前实际可调用的接口。
所有接口均为**开发环境 MVP** 的现状，未实现的能力已在末尾「尚未提供的接口」中列出。

- 后端基础地址：`http://127.0.0.1:8000`
- 接口统一前缀：`/api/v1`
- 交互式文档（Swagger）：`http://127.0.0.1:8000/docs`
- 请求和响应均为 `application/json`，上传接口为 `multipart/form-data`

## 认证方式

除健康检查和注册、登录接口外，**所有接口都需要携带 JWT**：

```text
Authorization: Bearer <access_token>
```

Token 通过登录接口获取。服务端使用 `JWT_SECRET_KEY` 校验签名，并从 Token 中取出用户 ID，
再确认该用户仍然存在且 `is_active` 为真。校验失败统一返回 `401`。

数据隔离规则：知识库、文档和故障记录都按当前用户的 `owner_id` 过滤，**跨用户访问统一
返回 `404`**（而不是 `403`），以免泄露资源是否存在。

## 通用状态码

| 状态码 | 含义 |
| --- | --- |
| `200 OK` | 请求成功 |
| `201 Created` | 创建成功（注册、创建知识库、上传文档） |
| `204 No Content` | 删除成功，无响应体 |
| `401 Unauthorized` | 缺少 Token、Token 非法或已失效、登录凭据错误 |
| `403 Forbidden` | 用户已被停用 |
| `404 Not Found` | 资源不存在，或不属于当前用户 |
| `409 Conflict` | 用户名重复、知识库重名、无 `failed` 版本可重建索引 |
| `413 Payload Too Large` | 上传文件超过 10 MB |
| `415 Unsupported Media Type` | 上传扩展名不被允许 |
| `422 Unprocessable Entity` | 参数校验失败（含密码过短、空文件、非法文件名、空问题） |
| `500 Internal Server Error` | 服务端错误（如删除时文件清理失败） |
| `502 Bad Gateway` | 调用大模型失败 |
| `503 Service Unavailable` | 检索失败 |

---

## 一、健康检查

### `GET /health`

服务存活检查，不需要认证。

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
```

### `GET /health/db`

数据库连通性检查，不需要认证。用于区分「服务起来了但数据库连不上」的情况。

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health/db"
```

---

## 二、认证接口

前缀：`/api/v1/auth`

### 注册

```text
POST /api/v1/auth/register
```

请求体：

```json
{
  "username": "alice",
  "password": "password123"
}
```

约束：用户名长度 3-50，密码长度 8-128。密码经 Argon2id 哈希后写入 MySQL。

成功返回 `201`：

```json
{
  "id": 1,
  "username": "alice",
  "role": "user",
  "is_active": true,
  "created_at": "2026-01-01T10:00:00"
}
```

失败：用户名已存在返回 `409`；用户名或密码长度不合规返回 `422`。

### 登录

```text
POST /api/v1/auth/login
```

请求体：

```json
{
  "username": "alice",
  "password": "password123"
}
```

> 注意：登录接口使用 **JSON 请求体**，不是 OAuth2 Password Flow 的表单提交。
> 用表单方式调用会因为缺少字段返回 `422`。

成功返回 `200`：

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

失败：凭据错误返回 `401`（只返回统一错误信息，不区分用户名还是密码错误，避免用户名
枚举）；用户被停用返回 `403`；响应头会带 `WWW-Authenticate: Bearer`。

### 当前用户

```text
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

成功返回 `200`，结构与注册返回一致。无 Token 或 Token 非法返回 `401`。

---

## 三、知识库接口

前缀：`/api/v1/knowledge-bases`

### 创建知识库

```text
POST /api/v1/knowledge-bases
```

请求体：

```json
{
  "name": "订单服务知识库",
  "description": "订单服务的排障手册与架构说明"
}
```

`owner_id` 由服务端从 Token 推导，客户端传了也会被忽略。同一用户下知识库名称唯一，
重名返回 `409`。成功返回 `201`。

### 查询知识库列表

```text
GET /api/v1/knowledge-bases
```

只返回当前用户自己的知识库。

### 查询知识库详情

```text
GET /api/v1/knowledge-bases/{knowledge_base_id}
```

### 删除知识库

```text
DELETE /api/v1/knowledge-bases/{knowledge_base_id}
```

成功返回 `204`。级联删除关联的文档与版本。非本人知识库返回 `404`。

---

## 四、文档接口

前缀：`/api/v1/knowledge-bases`

### 上传文档

```text
POST /api/v1/knowledge-bases/{knowledge_base_id}/documents
Content-Type: multipart/form-data
```

表单字段：`file`（必填）

安全约束：

- 允许扩展名：`.md`、`.txt`、`.pdf`；
- 单文件最大 10 MB；
- 拒绝空文件；
- 规范化文件名并清理控制字符；
- 使用随机存储名，避免同名覆盖；
- 校验最终路径必须位于 `others/uploads` 内，防止路径穿越。

成功返回 `201`：

```json
{
  "id": 3,
  "knowledge_base_id": 1,
  "filename": "订单服务故障排查手册.md",
  "file_type": "md",
  "file_size": 4201,
  "status": "indexed",
  "version_number": 1,
  "chunk_count": 12,
  "duplicate": false,
  "error_message": null,
  "created_at": "2026-01-01T10:05:00"
}
```

**重复内容返回 `200`**，且 `duplicate` 为 `true`，表示复用了已有版本，没有创建新版本
（去重依据是 `(document_id, file_sha256)` 唯一约束）。

处理失败时不会抛错，而是在响应中返回 `status: "failed"` 并带上 `error_message`，
旧的 `indexed` 版本继续可用。

失败情况：扩展名不允许 `415`；超过 10 MB `413`；空文件 `422`；文件名非法 `422`；
知识库不存在或不属于当前用户 `404`。

### 查询文档列表

```text
GET /api/v1/knowledge-bases/{knowledge_base_id}/documents?page=1&page_size=20&status=indexed
```

| 查询参数 | 说明 |
| --- | --- |
| `page` | 页码，最小 1，默认 1 |
| `page_size` | 每页条数，1-100，默认 20 |
| `status` | 可选，取值 `pending` / `indexed` / `failed`，非法值返回 `422` |

返回分页结构：

```json
{
  "items": [
    {
      "id": 3,
      "knowledge_base_id": 1,
      "filename": "订单服务故障排查手册.md",
      "file_type": "md",
      "current_version": {
        "id": 3,
        "version_number": 1,
        "file_sha256": "...",
        "file_size": 4201,
        "status": "indexed",
        "error_message": null,
        "chunk_count": 12,
        "created_at": "2026-01-01T10:05:00",
        "updated_at": "2026-01-01T10:05:02"
      },
      "created_at": "2026-01-01T10:05:00",
      "updated_at": "2026-01-01T10:05:02"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

### 查询文档详情

```text
GET /api/v1/knowledge-bases/{knowledge_base_id}/documents/{document_id}
```

返回该逻辑文档以及当前生效版本（`current_version`）。

### 查询版本历史

```text
GET /api/v1/knowledge-bases/{knowledge_base_id}/documents/{document_id}/versions
```

返回版本列表，按版本序号排列，可看到每个版本的状态、错误原因和切片数量。

### 查询指定版本

```text
GET /api/v1/knowledge-bases/{knowledge_base_id}/documents/{document_id}/versions/{version_id}
```

ID 含义务必区分：

- `knowledge_base_id`：知识库 ID；
- `document_id`：**逻辑文档** ID（`documents.id`）；
- `version_id`：**版本记录主键**（`document_versions.id`）；
- `version_number`：同一逻辑文档内的版本序号，**不能**替代 `version_id`。

### 删除文档

```text
DELETE /api/v1/knowledge-bases/{knowledge_base_id}/documents/{document_id}
```

成功返回 `204`。删除顺序为：先清理 Chroma 向量 → 再删除原始文件 → 最后删除 MySQL
业务记录。这个顺序是为了避免先删 MySQL 后丢失清理向量所需的 `vector_id`。
文件清理失败返回 `500`。

### 重新索引

```text
POST /api/v1/knowledge-bases/{knowledge_base_id}/documents/{document_id}/reindex
```

重新处理该文档**最新的 `failed` 版本**。成功返回 `200`：

```json
{
  "document_id": 3,
  "version_id": 5,
  "version_number": 2,
  "status": "indexed",
  "chunk_count": 12,
  "error_message": null
}
```

当前没有 `failed` 版本时返回 `409 Conflict`，这属于正常业务结果，不是故障。

---

## 五、检索接口

### 直接检索

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

`top_k` 取值范围 1-10，默认 5，表示最多召回多少个最相似的切片，**不限制**回答长度。
`question` 长度 1-2000。

成功返回 `200`：

```json
{
  "question": "忘记密码后应该怎么办？",
  "context": "拼接后的检索原文……",
  "sources": [
    {
      "document_id": 2,
      "version_id": 2,
      "version_number": 1,
      "chunk_index": 29,
      "filename": "DevAtlas团队入门手册.txt",
      "content": "原始切片内容……",
      "distance": 0.55,
      "page_number": null
    }
  ]
}
```

该接口**只做检索，不调用大模型**。没有可检索版本时 `context` 为空字符串、
`sources` 为空数组。

失败情况：空字符串或纯空格问题返回 `422`；`top_k` 超出范围返回 `422`；
检索失败返回 `503`；无 Token `401`；跨用户知识库 `404`。

---

## 六、问答接口

### 普通问答（一次性返回）

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

字段约束：`question` 长度 1-2000；`top_k` 取值范围 1-10，默认 5。

成功返回 `200`：

```json
{
  "question": "你的文档中写的主要内容是什么？",
  "answer": "根据知识库内容……",
  "sources": [
    {
      "document_id": 2,
      "version_id": 2,
      "version_number": 1,
      "chunk_index": 29,
      "filename": "DevAtlas团队入门手册.txt",
      "content": "原始切片内容……",
      "distance": 0.55,
      "page_number": null
    }
  ]
}
```

关键行为：**如果没有检索到任何来源，接口不会调用大模型**，而是直接返回
`answer: "当前知识库中没有检索到与该问题相关的内容。"`，`sources` 为空数组。

失败情况：参数不合法 `422`；检索失败 `503`；DeepSeek 配置缺失、网络失败、超时或返回
异常统一返回 `502 Bad Gateway`。

### 流式问答（SSE）

```text
POST /api/v1/knowledge-bases/{knowledge_base_id}/qa/stream
Accept: text/event-stream
```

请求体：

```json
{
  "question": "你的文档中写的主要内容是什么？",
  "top_k": 3,
  "conversation_id": null
}
```

字段约束：`question` 长度 1-2000；`top_k` 取值范围 1-10，默认 5；
`conversation_id` 可选，当前会原样回显在 `done` 事件中。

响应为 `text/event-stream`，并带有 `Cache-Control: no-cache`、`Connection: keep-alive`、
`X-Accel-Buffering: no` 头。

事件顺序通常为：多个 `token` → 多个 `citation` → 一个 `done`。

```text
event: token
data: {"text":"根据知识库内容，"}

event: token
data: {"text":"忘记密码后可以联系管理员。"}

event: citation
data: {"index":1,"document_id":2,"version_id":2,"version_number":1,"chunk_index":29,"filename":"DevAtlas团队入门手册.txt","distance":0.55}

event: done
data: {"conversation_id":null,"message_id":null}
```

| 事件 | 数据字段 |
| --- | --- |
| `token` | `text`：本次生成的文本片段 |
| `citation` | `index`、`document_id`、`version_id`、`version_number`、`chunk_index`、`filename`、`distance` |
| `done` | `conversation_id`（原样回传请求值）、`message_id`（当前恒为 `null`） |
| `error` | `code`、`message` |

出错时发送：

```text
event: error
data: {"code":"LLM_SERVICE_ERROR","message":"大模型服务暂时不可用"}
```

没有召回来源时，服务端不调用大模型，直接发送一条提示 `token` 和 `done`。

> 当前阶段问答历史未持久化，`conversation_id` 和 `message_id` 只是保留接口结构，
> 值可以为 `null`。

前端使用 `fetch + ReadableStream` 解析该流（见 `frontend/src/api/sse.ts`）。

---

## 七、故障分析接口

前缀：`/api/v1`。故障分析使用独立的 `incidents` 记录，**不会**把分析结果写回知识库。

### 发起故障分析（SSE）

```text
POST /api/v1/knowledge-bases/{knowledge_base_id}/incidents/stream
Content-Type: application/json
```

请求体：

```json
{
  "title": "订单服务返回 502",
  "content": "网关返回 502，订单服务无法连接数据库，请根据知识库给出排查步骤。"
}
```

字段约束：`title` 长度 1-200；`content` 长度 1-20000。

处理流程：

1. 创建一条 `streaming` 状态的 incident；
2. 以「标题 + 换行 + 故障描述」作为查询做检索，**固定 `top_k = 5`**；
3. 使用故障专用 Prompt 调用 DeepSeek；
4. SSE 返回 `token` 与 `citation`；
5. 完成后写入 `result` 和引用记录，状态更新为 `completed`。

事件示例：

```text
event: token
data: {"text":"排查步骤如下："}

event: citation
data: {"index":1,"document_id":2,"version_id":2,"version_number":1,"chunk_index":29,"filename":"订单服务故障排查手册.md","distance":0.42}

event: done
data: {"incident_id":7,"status":"completed"}
```

状态流转：

| 情况 | 状态 | 说明 |
| --- | --- | --- |
| 正常完成 | `completed` | 已保存 `result` 和引用 |
| 大模型失败 | `failed` | 保存 `error_message`，并发送 `error` 事件 |
| 检索失败 | `failed` | 保存错误原因，接口返回 `503`（此时不是 SSE 事件，而是 HTTP 错误） |
| 客户端主动断开 | `cancelled` | 生成器被关闭时标记 |

没有召回来源时，服务端直接返回一条中文提示 token 和 `done`，并把记录标记为
`completed`。

### 查询故障历史

```text
GET /api/v1/incidents?page=1&page_size=20&status=completed
```

| 查询参数 | 说明 |
| --- | --- |
| `page` | 页码，最小 1，默认 1 |
| `page_size` | 每页条数，1-100，默认 20 |
| `status` | 可选，取值 `streaming` / `completed` / `failed` / `cancelled`，非法值 `422` |

只返回当前用户自己的记录（按 `owner_id` 过滤）。

### 查询故障详情

```text
GET /api/v1/incidents/{incident_id}
```

返回故障标题、输入内容、`result`、`error_message`、使用的模型名和引用列表：

```json
{
  "id": 7,
  "knowledge_base_id": 1,
  "title": "订单服务返回 502",
  "status": "completed",
  "model_name": "deepseek-v4-flash",
  "created_at": "2026-01-01T11:00:00",
  "completed_at": "2026-01-01T11:00:09",
  "owner_id": 1,
  "input_content": "网关返回 502……",
  "result": "排查步骤如下……",
  "error_message": null,
  "citations": [
    {
      "citation_index": 1,
      "document_chunk_id": 42
    }
  ]
}
```

非本人记录返回 `404`。

### 删除故障记录

```text
DELETE /api/v1/incidents/{incident_id}
```

成功返回 `204`，级联删除引用记录。

---

## 八、典型调用顺序

```powershell
$base = "http://127.0.0.1:8000/api/v1"

# 1. 注册
Invoke-RestMethod -Method Post -Uri "$base/auth/register" `
  -ContentType "application/json" `
  -Body '{"username":"alice","password":"password123"}'

# 2. 登录并保存 Token
$login = Invoke-RestMethod -Method Post -Uri "$base/auth/login" `
  -ContentType "application/json" `
  -Body '{"username":"alice","password":"password123"}'
$headers = @{ Authorization = "Bearer $($login.access_token)" }

# 3. 创建知识库
$kb = Invoke-RestMethod -Method Post -Uri "$base/knowledge-bases" `
  -Headers $headers -ContentType "application/json" `
  -Body '{"name":"订单服务知识库","description":"排障手册"}'

# 4. 上传文档
Invoke-RestMethod -Method Post `
  -Uri "$base/knowledge-bases/$($kb.id)/documents" `
  -Headers $headers `
  -Form @{ file = Get-Item ".\tests\订单服务故障排查手册.md" }

# 5. 直接检索
Invoke-RestMethod -Method Post `
  -Uri "$base/knowledge-bases/$($kb.id)/search" `
  -Headers $headers -ContentType "application/json" `
  -Body '{"question":"忘记密码怎么办？","top_k":3}'

# 6. 普通问答
Invoke-RestMethod -Method Post `
  -Uri "$base/knowledge-bases/$($kb.id)/qa" `
  -Headers $headers -ContentType "application/json" `
  -Body '{"question":"忘记密码怎么办？","top_k":3}'

# 7. 查询故障历史
Invoke-RestMethod -Uri "$base/incidents?page=1&page_size=20" -Headers $headers
```

SSE 接口（`qa/stream`、`incidents/stream`）建议用浏览器或前端页面验证，因为需要按事件流
逐步读取；PowerShell 的 `Invoke-RestMethod` 会缓冲整个响应，不适合观察流式效果。

---

## 九、SSE 事件格式约定

所有 SSE 事件都遵循标准格式：

```text
event: <事件名>
data: <单行 JSON>

```

- `data` 使用 `json.dumps(..., ensure_ascii=False)` 生成，因此中文不会被转义成 `\uXXXX`；
- 每个事件以空行结束；
- 当前实现中每个事件只包含一行 `data`；
- 客户端应按「遇到空行即认为一个事件结束」来解析，不要假设固定的事件顺序或数量。

---

## 十、尚未提供的接口

以下能力**当前没有实现**，调用会返回 `404`，文档中列出是为了避免误解：

- 知识库更新（只有创建、查询、删除）；
- 知识库共享与团队成员管理；
- 问答历史的持久化查询（`conversation_id` / `message_id` 目前无实际语义）；
- 登出、刷新 Token、找回密码；
- 批量上传与异步任务进度查询；
- 任何管理后台或统计报表接口。

---

## 十一、安全注意事项

- 除健康检查和注册登录外，所有接口都必须携带 Bearer Token；
- `.env` 中的 `JWT_SECRET_KEY` 与 `DEEPSEEK_API_KEY` 不要提交到仓库，也不要在
  前端代码中出现（前端只访问后端，不直连 DeepSeek）；
- 生产环境还需要补充 HTTPS、接口限流、审计日志和刷新 Token 机制，这些在 MVP 阶段
  均未实现。
