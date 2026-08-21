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

下一步：

- T05：知识库 CRUD 和所有者权限；
- T06-T09：文件上传、文档解析、版本管理、Embedding 和 Chroma 入库；
- T10-T13：RAG 检索、DeepSeek 调用、问答 SSE 和故障分析；
- T14-T15：Vue 联调、测试和交付材料。

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

## Git 提交约定

每完成一个可验证功能再提交：

```powershell
git status
git add <本次修改的文件>
git commit -m "<type>: <description>"
git log -1 --oneline
```

`.env`、`node_modules`、上传文件和本地向量数据不会提交到仓库。
