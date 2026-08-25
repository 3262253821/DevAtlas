# T11 DeepSeek 普通调用和 RAG Prompt 阶段总结

## 阶段目标

在 T10 向量检索基础上接入 DeepSeek，完成一次带知识库上下文的普通问答。此阶段不做 SSE，先验证问题、检索上下文、Prompt 和 LLM 响应之间的完整关系。

## 产出

新增：

- `backend/app/schemas/qa.py`
- `backend/app/services/llm.py`
- `backend/app/routers/qa.py`

修改：

- `backend/app/main.py`
- `backend/requirements.txt`（加入 `requests`）

## 接口

```text
POST /api/v1/knowledge-bases/{knowledge_base_id}/qa
```

请求示例：

```json
{
  "question": "你的文档中写的主要内容是什么？",
  "top_k": 3
}
```

## 完整调用链

```text
HTTP 请求
→ qa router
→ JWT 当前用户鉴权
→ 校验知识库 owner_id
→ 调用 T10 retrieve_context()
→ 找到 indexed 文档块和 context
→ build_rag_messages() 组装 system/user Prompt
→ chat_with_llm() 调用 DeepSeek OpenAI 兼容接口
→ 解析 choices[0].message.content
→ 返回 answer + sources
```

## 核心设计

- LLM 调用集中在 `services/llm.py`，路由不直接拼接 URL、Header 或解析第三方响应。
- API Key 只从 `.env` 加载，通过 `Authorization: Bearer` 发送，不写入日志、响应或文档。
- Prompt 明确要求模型只依据知识库上下文回答；上下文中的内容被视为参考资料，不能当作额外指令执行。
- 上下文限制为最多 12000 个字符，避免一次请求携带过大的 Prompt。
- 没有检索来源时直接返回“没有找到相关内容”，避免无依据调用模型。
- 第三方调用失败统一转换成 `LLMServiceError`，路由再转换成 `502 Bad Gateway`。

## DeepSeek 响应解析

DeepSeek 使用 OpenAI 兼容响应结构：

```json
{
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "回答内容"
      }
    }
  ]
}
```

因此服务层按以下路径读取最终回答：

```text
data
→ choices
→ choices[0]
→ message
→ content
```

## 验证结果

- 合法 Token、知识库和真实 DeepSeek 配置：返回 `200`、完整 `answer` 和 `sources`；
- 没有检索来源：返回 `200`，给出知识库无相关内容的提示；
- 未鉴权：返回 `401`；
- 跨用户知识库：返回 `404`；
- `top_k` 不在 1-10：返回 `422`；
- DeepSeek 配置缺失、网络错误、超时或异常响应：返回 `502`。

## 与前后阶段的关系

```text
T10：只检索原文 context
T11：context + question → DeepSeek → 完整 answer
T12：把 T11 的完整调用改造成 SSE 流式输出
T13：复用检索和 LLM 服务完成故障分析并保存记录
```

## 阶段结论

T11 已完成。DevAtlas 现在已经具备从知识库检索文档并调用 DeepSeek 生成普通回答的后端链路。下一阶段进入 T12：知识库问答 SSE。
