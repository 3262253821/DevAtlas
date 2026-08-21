# 阶段 5：API 接口文档

## 文档状态

- 版本：v0.1（阶段 5 已确认）
- 项目：DevAtlas｜研发知识协同平台
- 前置文档：`02-产品需求文档-PRD.md`、`03-页面和业务流程设计.md`、`04-技术方案设计.md`
- API 前缀：`/api/v1`
- 当前状态：已由用户确认，未进入代码开发

## 1. 通用约定

### 1.1 请求格式

- 普通接口使用 `application/json`；
- 文件上传使用 `multipart/form-data`；
- SSE 接口返回 `text/event-stream`；
- 时间统一使用 ISO 8601 格式，服务端按 UTC 保存；
- ID 第一版使用整数类型，前端不依赖 ID 连续性。

### 1.2 鉴权

受保护接口请求头：

```http
Authorization: Bearer <access_token>
```

未标记“公开”的接口都需要 JWT。

### 1.3 分页

列表接口统一支持：

- `page`：从 1 开始，默认 1；
- `page_size`：默认 20，最大 100。

返回结构：

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

### 1.4 错误结构

除 FastAPI 参数校验错误外，业务错误统一返回：

```json
{
  "code": "KNOWLEDGE_BASE_NOT_FOUND",
  "message": "知识库不存在",
  "details": null
}
```

常见错误码：

| HTTP 状态 | code | 含义 |
| --- | --- | --- |
| 400 | `INVALID_REQUEST` | 请求业务规则不合法 |
| 401 | `UNAUTHORIZED` | 未登录或 Token 无效 |
| 403 | `FORBIDDEN` | 已登录但无权限 |
| 404 | `RESOURCE_NOT_FOUND` | 资源不存在 |
| 409 | `DUPLICATE_RESOURCE` | 资源重复 |
| 413 | `FILE_TOO_LARGE` | 文件超过大小限制 |
| 415 | `UNSUPPORTED_FILE_TYPE` | 文件格式不支持 |
| 422 | `VALIDATION_ERROR` | 请求参数校验失败 |
| 500 | `INTERNAL_ERROR` | 未预期服务端错误 |
| 502 | `LLM_SERVICE_ERROR` | LLM 或外部 AI 服务失败 |

## 2. 健康检查

### GET `/api/v1/health`

公开接口，用于确认 FastAPI 是否运行。

响应 `200`：

```json
{
  "status": "ok",
  "service": "dev-atlas-api"
}
```

## 3. 认证接口

### POST `/api/v1/auth/register`

公开接口，创建用户。

请求：

```json
{
  "username": "alice",
  "password": "password123"
}
```

规则：

- `username` 必填，长度 3-50；
- `password` 必填，最小长度 8；
- 用户名唯一；
- 服务端只保存密码哈希。

成功 `201`：

```json
{
  "id": 1,
  "username": "alice",
  "role": "user",
  "created_at": "2026-08-20T12:00:00Z"
}
```

失败：`409 DUPLICATE_RESOURCE`、`422 VALIDATION_ERROR`。

### POST `/api/v1/auth/login`

公开接口，验证用户并签发 JWT。

请求：

```json
{
  "username": "alice",
  "password": "password123"
}
```

成功 `200`：

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "username": "alice",
    "role": "user"
  }
}
```

失败：统一返回 `401 UNAUTHORIZED`，不区分用户名不存在和密码错误。

### GET `/api/v1/auth/me`

需要鉴权，返回当前用户。

成功 `200`：返回用户公开信息，不返回密码哈希。

## 4. 知识库接口

### POST `/api/v1/knowledge-bases`

创建知识库。

请求：

```json
{
  "name": "订单服务知识库",
  "description": "订单服务 API、部署和故障资料"
}
```

成功 `201`：

```json
{
  "id": 1,
  "name": "订单服务知识库",
  "description": "订单服务 API、部署和故障资料",
  "owner_id": 1,
  "created_at": "2026-08-20T12:00:00Z",
  "updated_at": "2026-08-20T12:00:00Z"
}
```

失败：`409 DUPLICATE_RESOURCE`（同一用户下名称重复）、`422 VALIDATION_ERROR`。

### GET `/api/v1/knowledge-bases`

返回当前用户有权限访问的知识库列表。MVP 只有所有者模型。

查询参数：`page`、`page_size`。

### GET `/api/v1/knowledge-bases/{knowledge_base_id}`

返回一个知识库详情。资源不存在或当前用户无权访问时不泄露其他用户数据。

### DELETE `/api/v1/knowledge-bases/{knowledge_base_id}`

删除知识库及其文档、版本、文档块、向量和故障记录。

成功 `204 No Content`。

服务端顺序：先清理 Chroma 和文件，再删除 MySQL 业务数据。

## 5. 文档接口

### POST `/api/v1/knowledge-bases/{knowledge_base_id}/documents`

上传并索引文档。

请求类型：`multipart/form-data`。

字段：

- `file`：必填，支持 `.md`、`.txt`、`.pdf`；
- 单文件最大 10 MB。

处理流程：创建版本 `pending` → 解析/切分/Embedding/写入 Chroma → `indexed` 或 `failed`。

新文档成功 `201`，重复内容 `200`，响应：

```json
{
  "id": 10,
  "knowledge_base_id": 1,
  "filename": "部署手册.md",
  "file_type": "md",
  "file_size": 18320,
  "status": "indexed",
  "version_number": 1,
  "chunk_count": 12,
  "duplicate": false,
  "error_message": null,
  "created_at": "2026-08-20T12:00:00Z"
}
```

重复上传时 `duplicate=true`，不创建新的版本。

失败时保留可查询的文档/版本状态 `failed` 和 `error_message`，不把半成品标记为 `indexed`。

失败：`401`、`403`、`413`、`415`、`422`。

### GET `/api/v1/knowledge-bases/{knowledge_base_id}/documents`

返回当前知识库文档列表。

查询参数：`page`、`page_size`、可选 `status`。

列表项至少包含：文档 ID、文件名、文件类型、当前版本、索引状态、分块数量、失败原因和更新时间。

### GET `/api/v1/knowledge-bases/{knowledge_base_id}/documents/{document_id}`

返回文档详情和当前版本摘要。必须同时校验路径中的知识库和文档归属关系。

### DELETE `/api/v1/knowledge-bases/{knowledge_base_id}/documents/{document_id}`

删除文档、所有版本、文档块、原始文件和 Chroma 向量。

成功 `204 No Content`。

### POST `/api/v1/knowledge-bases/{knowledge_base_id}/documents/{document_id}/reindex`

重新处理当前文档版本，主要用于 `failed` 状态恢复。

成功 `200`：返回最新文档状态和分块数量。

## 6. 文档版本接口（P1）

### GET `/api/v1/knowledge-bases/{knowledge_base_id}/documents/{document_id}/versions`

返回文档版本列表，按版本号倒序。

### GET `/api/v1/knowledge-bases/{knowledge_base_id}/documents/{document_id}/versions/{version_id}`

返回某个版本的元数据、状态、失败原因和分块数量。不默认返回整份大文件内容。

## 7. 知识库问答接口

### POST `/api/v1/knowledge-bases/{knowledge_base_id}/qa/stream`

需要鉴权，返回 SSE 流。

请求：

```json
{
  "question": "订单服务返回 502 时应该先检查什么？",
  "conversation_id": null
}
```

前置错误在建立 SSE 响应前返回：`400`、`401`、`403`、`404`、`422`。

响应头：

```http
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

事件格式：

```text
event: token
data: {"text":"可能先检查数据库连接池"}

event: citation
data: {"index":1,"document_id":10,"version_id":21,"chunk_id":88,"filename":"部署手册.md","version_number":2}

event: done
data: {"conversation_id":3,"message_id":9}
```

失败事件：

```text
event: error
data: {"code":"LLM_SERVICE_ERROR","message":"大模型服务暂时不可用"}
```

MVP 可先不保存问答历史；如果启用会话历史，`done` 事件返回会话和消息 ID。

## 8. 故障分析接口

### POST `/api/v1/knowledge-bases/{knowledge_base_id}/incidents/stream`

需要鉴权，返回 SSE 流。

请求：

```json
{
  "title": "订单服务 502",
  "content": "网关返回 502，订单服务无法连接数据库"
}
```

事件类型同问答：`token`、`citation`、`done`、`error`。

完成事件示例：

```text
event: done
data: {"incident_id":12,"status":"completed"}
```

只有生成成功后才将记录标记为 `completed`；中断为 `cancelled`，外部服务失败为 `failed`。

### GET `/api/v1/incidents`

返回当前用户的故障分析历史。

查询参数：`page`、`page_size`、可选 `status`。

### GET `/api/v1/incidents/{incident_id}`

返回故障标题、输入日志、分析结果、状态、引用来源和时间。

### DELETE `/api/v1/incidents/{incident_id}`

删除当前用户自己的故障分析记录。

成功 `204 No Content`。

## 9. 不在当前 API 范围内的接口

- GitLab/Jira/监控平台集成；
- 自动执行修复命令；
- 多 Agent 工具调用；
- 复杂团队成员邀请和审批；
- 管理员用户管理；
- BM25、RRF、Reranker 调试接口。

## 10. 接口实现顺序

1. `health`；
2. `auth/register`、`auth/login`、`auth/me`；
3. 知识库 CRUD；
4. 文档上传、列表、详情和删除；
5. RAG 问答 SSE；
6. 故障分析 SSE 和记录；
7. 版本历史、问答历史和页面增强。

## 11. 阶段 5 API 评审确认项

阶段 5 已确认以下决策：

1. 统一 `/api/v1` 前缀和错误响应结构；
2. 登录使用 JSON 请求；
3. 接受知识库、文档、版本、问答和故障分析的路径设计；
4. 问答和故障分析使用 POST SSE，并使用 `token/citation/done/error` 事件；
5. 文档上传响应允许 `indexed` 或 `failed`，重复内容返回 `duplicate=true`；
6. 问答历史和完整版本页面属于 P1，但数据库设计预留关联。

确认结果：以上六项全部接受。结合 `05-数据库设计.md` 进入阶段 6：拆分开发任务。
