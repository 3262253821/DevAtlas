# T10 RAG 检索阶段总结

## 阶段目标

在 T08 的 Embedding/Chroma 入库和 T09 的文档管理基础上，完成知识库问答前的检索层：把用户问题转换成向量，在指定知识库的可检索版本中找到最相关的文档块，并返回上下文和来源信息。

## 产出

新增：

- `backend/app/schemas/retrieval.py`
- `backend/app/services/retrieval.py`
- `backend/app/routers/retrieval.py`

修改：

- `backend/app/main.py`

## 接口

```text
POST /api/v1/knowledge-bases/{knowledge_base_id}/search
```

请求示例：

```json
{
  "question": "忘记密码后应该怎么办？",
  "top_k": 3
}
```

## 完整调用链

```text
HTTP 请求
→ retrieval router
→ JWT 当前用户鉴权
→ 校验知识库 owner_id
→ retrieve_context()
→ MySQL 查询当前知识库的 indexed 版本
→ embed_texts() 将问题转换为向量
→ Chroma collection.query()
→ metadata 过滤并取得 Top-K 文档块
→ 组装 context 和 sources
→ 返回 RetrievalResponse
```

## 核心设计

- 只有 `document_versions.status == "indexed"` 的版本参与默认检索，避免把 `pending` 或 `failed` 数据交给后续模型。
- Chroma 查询同时过滤 `knowledge_base_id`、`document_version_id` 和 `is_searchable`，避免跨知识库检索或检索不可搜索 chunk。
- `top_k` 由请求控制，但限制在 1-10，避免一次取回过多上下文。
- `context` 是原文 chunk 的拼接结果，不是 LLM 生成的答案；T11 才会把问题和 context 发送给 DeepSeek。
- `sources` 保留文档、版本、chunk 和文件名，便于前端展示引用，也便于排查检索结果。
- Chroma 返回的是 cosine distance，数值越小通常表示向量越接近；检索结果不代表一定包含答案，知识库没有相关内容时也可能返回语义上较近但不相关的 chunk。

## 验证结果

- 合法 Token + 合法知识库：返回 `200`、`context` 和 `sources`；
- 查询结果包含 `document_id`、`version_id`、`version_number`、`chunk_index`、`filename` 和 `distance`；
- 无可检索版本：返回 `200`，但 `context` 和 `sources` 为空；
- 跨用户知识库：返回 `404`；
- 未鉴权：返回 `401`；
- `top_k` 不在 1-10：返回 `422`。

## 已知边界

T10 只完成检索，不负责判断检索内容是否足以回答问题，也不负责调用 DeepSeek。若上传文档没有相关答案，Top-K 仍可能返回相对接近但不相关的内容；T11 将通过 RAG Prompt 要求模型只依据上下文回答，找不到依据时明确说明。

## 阶段结论

T10 已完成。上传文档经过 T07/T08 处理后，能够在指定知识库范围内被向量检索，并返回可追溯的来源。下一阶段进入 T11：DeepSeek 普通调用和 RAG Prompt。
