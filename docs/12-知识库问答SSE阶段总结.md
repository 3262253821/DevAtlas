# T12 知识库问答 SSE 阶段总结

## 阶段目标

在 T11 普通 RAG 问答基础上，把完整 JSON 回答改造成 SSE 流式输出，让客户端可以逐段展示回答，并同时接收检索来源和完成状态。

## 产出

新增或修改：

- `backend/app/schemas/qa.py`：增加 `QAStreamRequest`；
- `backend/app/services/llm.py`：增加 DeepSeek 流式调用；
- `backend/app/routers/qa.py`：增加 `/qa/stream` 和 SSE 事件生成；
- `backend/requirements.txt`：增加 `openai`，使用 OpenAI 兼容客户端解析流式响应。

## 接口

```text
POST /api/v1/knowledge-bases/{knowledge_base_id}/qa/stream
```

请求示例：

```json
{
  "question": "你的文档中写的主要内容是什么？",
  "top_k": 3,
  "conversation_id": null
}
```

响应类型：

```text
Content-Type: text/event-stream
```

## 完整调用链

```text
HTTP 请求
→ qa.stream_question()
→ JWT 当前用户鉴权
→ 校验知识库 owner_id
→ T10 retrieve_context()
→ build_rag_messages()
→ T12 stream_chat_with_llm()
→ DeepSeek 返回流式 chunk
→ 发送 token 事件
→ 发送 citation 事件
→ 发送 done 事件
```

## SSE 事件

### token

回答的一小段文本，前端按接收顺序追加到当前回答中：

```text
event: token
data: {"text":"回答片段"}
```

### citation

检索来源，包含文档、版本、chunk 和距离信息：

```text
event: citation
data: {"index":1,"document_id":2,"version_id":2,"chunk_index":29,"filename":"文档.txt","distance":0.55}
```

### done

表示回答正常结束：

```text
event: done
data: {"conversation_id":null,"message_id":null}
```

当前没有问答历史表，所以两个 ID 暂时为 `null`。

### error

流式调用已经建立后，如果 DeepSeek 调用失败，通过 SSE 发送错误事件：

```text
event: error
data: {"code":"LLM_SERVICE_ERROR","message":"大模型服务暂时不可用"}
```

SSE 已经开始后不能再改成普通 HTTP `502`，因此必须使用 `error` 事件通知客户端。

## 关键设计

- `top_k` 只限制 T10 检索的文档块数量，不限制 DeepSeek 最终回答长度。
- 没有检索来源时不调用 DeepSeek，直接发送提示 token 和 `done`，减少无依据回答。
- 权限校验和 T10/T11 保持一致，不能通过修改路径 ID 访问其他用户知识库。
- 使用 OpenAI 兼容客户端处理 DeepSeek 流，客户端负责 SSE 事件边界和数据解析，业务代码只提取 `chunk.choices[0].delta.content`。
- 不把 API Key 或第三方详细错误返回给客户端。

## 本阶段遇到的问题和解决

最初使用 `requests.iter_lines()` 手动解析 `data:` 行，并直接执行 `json.loads(data_text)`。实际流中出现空数据行，导致 `json.loads("")` 抛出解析异常；临时诊断代码还因缩进错误触发了 `UnboundLocalError`。后来改用 OpenAI 兼容客户端处理 DeepSeek 的流式响应，解决了事件边界和空行兼容问题。

## 验证结果

- `8001/docs` 和 `openapi.json` 正常；
- 登录获取 Token 正常；
- 合法 SSE 请求返回 `200`；
- 响应事件链路为 `token → citation → done`；
- `top_k=3` 时最多返回 3 个 citation 来源；
- 无相关文档时返回提示 token 和 `done`；
- 未鉴权返回 `401`；
- 跨用户知识库返回 `404`；
- 空问题或非法 `top_k` 返回 `422`。

## 阶段结论

T12 已完成。DevAtlas 现在具备从知识库检索、调用 DeepSeek 到 SSE 流式展示回答和来源的后端链路。下一阶段进入 T13：故障分析和 incident 记录。
