# 阶段 5：API 和数据库设计总结

## 阶段状态

- 状态：已完成并经用户确认
- 项目：DevAtlas｜研发知识协同平台
- 下一阶段：阶段 6：拆分开发任务
- 当前仍未编写业务代码

## 本阶段产出

- `05-API接口文档.md`
- `05-数据库设计.md`

## 已确认的 API 契约

- API 前缀：`/api/v1`；
- 认证：Bearer JWT；
- 登录使用 JSON；
- 文档上传使用 `multipart/form-data`；
- 问答和故障分析使用 POST SSE；
- SSE 事件：`token`、`citation`、`done`、`error`；
- 错误使用统一 `code/message/details` 结构；
- 文档上传支持 `indexed`、`failed` 和 `duplicate` 状态。

## 已确认的数据库结构

### P0

- `users`；
- `knowledge_bases`；
- `documents`；
- `document_versions`；
- `document_chunks`；
- `incidents`；
- `incident_citations`。

### P1

- `conversations`；
- `messages`；
- `message_citations`。

## 不能丢失的设计决策

- 文件逻辑身份由知识库和规范化文件名确定；
- 文件内容哈希用于重复上传幂等；
- 内容变化创建新版本，不覆盖历史版本；
- 只有 `indexed` 版本可以参与默认检索；
- MySQL 是业务事实来源，Chroma 是检索索引；
- 删除必须同步清理 MySQL、原始文件和 Chroma；
- MySQL 和 Chroma 不是同一事务系统，必须通过 Service 做失败补偿；
- 故障分析记录属于 P0，普通问答历史属于 P1；
- 接口、数据库和向量 metadata 必须保留知识库、文档、版本和文档块关联。

## 对开发中真实问题的处理原则

设计文档冻结的是需求契约和数据关系，不保证实现阶段没有错误。遇到问题时按以下顺序判断：

1. 是代码实现错误；
2. 是接口请求/响应不一致；
3. 是数据库迁移或约束错误；
4. 是 MySQL、Chroma、LLM 等外部依赖问题；
5. 是原设计遗漏或需求变化。

只有第 5 类问题需要更新 PRD、技术方案、API 或数据库设计；其他问题优先修复代码并补测试。

## 下一步

阶段 6 将把 API、数据库和页面流程拆成可执行开发任务，明确任务依赖、完成标准、测试点和 Git 提交节奏。阶段 6 完成后才进入阶段 7 正式初始化和编码。
