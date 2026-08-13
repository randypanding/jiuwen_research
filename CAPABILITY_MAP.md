# openJiuwen 原生能力清单

> 基于上游Commit: `9638e6a85d0f01d67e3656ee9aeec05c633d60b4`（本仓库 HEAD，聚合下列 11 个 submodule 指针）
> 生成时间: 2026-08-13

各 submodule 被锁定的上游 Commit：

| 组件 | 上游 Commit SHA | 跟踪分支 |
| --- | --- | --- |
| jiuwenswarm | `fc110aafb954aa6d99c886dc8f4e4fdf71973885` | develop |
| agent-core | `73cfc3bc8b74386c5d91c6d1ff11f50e6df510df` | develop |
| agent-studio | `cfe70e96afded38f426159728456e09b82e56661` | studio-2.0 |
| deepsearch | `62aa0e3718d83806aa42c4d89dfe33c2c3a11db0` | v0.1.9 |
| agent-runtime | `34ed6e86b99fab9b3f07d9f063efc1692ab365d2` | main |
| jiuwensymbiosis | `6c27197a3bf90506756cc1d03aa312bb7c3b75f3` | main |
| agent-memory | `600432b55e480bec5948ee40089884ccf15a7c5d` | develop |
| skillhub | `446002b3ddef4b2e85962ed37f169db59a616099` | develop |
| agent-tools | `824a5170517104332d9358721286ce5178125794` | dev |
| agent-protocol | `b25684052a7581723947474cb71f85c5f841e6a2` | main |
| relay | `9de45970272cc6985334b14da116b9e159a7fce6` | main |

说明：本文所有 `路径:行号` 均相对于本仓库根目录（即以 submodule 目录名开头），行号对应上表 Commit。无法定位到确切行号的条目一律标注 `[待核实]`。

---

## 1. 组件概览

| 组件名 | 仓库路径 | 主要语言 | 核心职责 |
| --- | --- | --- | --- |
| Agent Core | `agent-core/` | Python（3788 文件 / ~927k 行） | Agent SDK 内核：单体 Agent（ReAct/Deep）、多智能体 Team、LLM 抽象、记忆/存储、工具与 MCP、会话检查点、运行器与 harness 扩展装配 |
| Agent Studio | `agent-studio/` | Java（3220 / ~421k）+ Python（1334 / ~272k）+ TypeScript（915 / ~199k） | 低代码 Agent/工作流 IDE 与管理平台：画布编排、节点执行引擎、插件/MCP 市场、租户与鉴权、编排产物下发到 Runtime |
| Agent Runtime | `agent-runtime/` | Python（256 / ~42.6k） | Agent 托管运行时：应用注册与生命周期、IR（中间表示）执行、会话/流式对话 API、A2A 暴露 |
| Agent Memory | `agent-memory/` | Python（349 / ~78k）+ Java（210 / ~17.8k）+ TS/Vue | 记忆系统：Python 记忆内核（抽取/检索/融合/遗忘）+ Java 平台服务（多租户 scope、确认流、REST 门面）+ 可视化 |
| Agent Protocol | `agent-protocol/` | C++（150 cpp / ~57.6k，97 h / ~13.2k）+ Python（208 / ~28.9k） | 协议实现与注册中心：A2A C++ SDK、MCP C++ SDK、AgentRegistry（A2X）Agent 注册/发现/预约服务 |
| Agent Tools | `agent-tools/` | Python（322 / ~53.5k） | 推理侧工具：infer_router（KV-Cache 亲和的 OpenAI 兼容 LLM 网关）、vLLM 亲和调度插件、开发者工具集、Tool 开发赛样例 |
| DeepSearch | `deepsearch/` | Python（416 / ~119k） | 深度研究 Agent：多轮检索规划、网页/文件检索、证据聚合与长报告生成 |
| JiuwenSwarm | `jiuwenswarm/` | Python（1210 / ~442k）+ TS/TSX（280 + 112） | 面向编码/终端场景的 Agent 集群产品：CLI/TUI、沙箱执行（jiuwenbox）、权限体系、团队协作（Symphony/SwarmFlow）、A2X 队友预约 |
| JiuwenSymbiosis | `jiuwensymbiosis/` | Python（262 / ~53.3k） | 具身智能：机械臂（Piper / SO-101）控制、视觉抓取（GroundingDINO + SAM2）、技能注册与 NiceGUI 操作台 |
| Relay | `relay/` | TypeScript（1108 / ~200k）+ TSX（450 / ~95.9k）+ JS（485）+ Python（52） | 桌面/服务端 Agent 工作台（OfficeClaw）：会话与 Provider 编排、MCP Server、插件系统、SQLite 持久化、Web UI |
| SkillHub | `skillhub/` | Python（488 / ~93.8k）+ TSX（47 / ~17k） | 技能/插件市场：技能包发布与检索、Playground 试跑（代理到 skill-runner）、GitHub 生态观测 |

---

## 2. 详细能力映射

### 2.1 Agent Core

仓库路径: `agent-core/`（Python 包名 `openjiuwen`）

#### 核心功能

- **单体 Agent 运行内核（ReAct）**：`ReActAgent` 实现"思考-工具调用-观察"主循环，是所有上层 Agent 的执行基座。
  - 证据: `agent-core/openjiuwen/core/single_agent/agents/react_agent.py:L195-L300`
- **Agent Rail（护栏/轨道）抽象**：以抽象基类形式定义 Agent 运行前后的拦截轨道，支持安全、审计等横切逻辑。
  - 证据: `agent-core/openjiuwen/core/single_agent/rail/base.py:L672-L720`
- **LLM 客户端统一抽象**：`BaseModelClient` 统一封装不同模型供应商（OpenAI/Anthropic/DashScope/Transformers 等）的调用协议。
  - 证据: `agent-core/openjiuwen/core/foundation/llm/model_clients/base_model_client.py:L44-L120`
- **向量存储抽象与注册**：以注册函数方式动态挂载多种向量库实现。
  - 证据: `agent-core/openjiuwen/core/foundation/store/__init__.py:L42-L60`
- **会话检查点（Checkpointer）**：抽象出会话状态持久化接口，支撑断点续跑与多轮上下文恢复。
  - 证据: `agent-core/openjiuwen/core/session/checkpointer/base.py:L14-L60`
- **上下文工程（Context Engine）**：按 token 预算裁剪/重载历史消息窗口。
  - 证据: `agent-core/openjiuwen/core/context_engine/schema/config.py:L23-L113`
- **Deep Agent 编排规格**：以声明式 Spec 描述任务循环、技能发现、沙箱限制等深度智能体行为。
  - 证据: `agent-core/openjiuwen/harness/schema/deep_agent_spec.py:L426-L480`
- **Harness 扩展热装配**：运行期把扩展（rail/tool/memory 等）热绑定到 Agent 实例。
  - 证据: `agent-core/openjiuwen/harness/extension_binder.py:L27-L60`
- **分布式 Runner（远端客户端 / 服务端适配器）**：把 Agent 以远程服务形式拉起或接入。
  - 证据: `agent-core/openjiuwen/core/runner/drunner/remote_client/__init__.py:L20-L40`、`agent-core/openjiuwen/core/runner/drunner/server_adapter/__init__.py:L29-L59`
- **工具调用超时与并发治理**：在能力管理器层统一约束工具执行时长。
  - 证据: `agent-core/openjiuwen/core/single_agent/ability_manager.py:L78-L83`
- **CLI 入口**：`openjiuwen`、`team-member`、`openjiuwen-team-mcp` 三个可执行入口。
  - 证据: `agent-core/pyproject.toml:L171-L173`

#### 配置选项

| 配置项名 | 默认值 | 说明 | 证据 |
| --- | --- | --- | --- |
| `ReActAgentConfig.model_provider` | `"openai"` | ReAct Agent 使用的模型供应商 | `agent-core/openjiuwen/core/single_agent/agents/react_agent.py:L203` |
| `ReActAgentConfig.max_iterations` | `5` | ReAct 主循环最大迭代轮数 | `agent-core/openjiuwen/core/single_agent/agents/react_agent.py:L216` |
| `ReActAgentConfig.parallel_tool_calls` | 见定义 | 是否允许并行工具调用 | `agent-core/openjiuwen/core/single_agent/agents/react_agent.py:L264` |
| `ModelRequestConfig.temperature` | `0.95` | 采样温度 | `agent-core/openjiuwen/core/foundation/llm/schema/config.py:L141` |
| `ModelRequestConfig.top_p` | `0.1` | 核采样阈值 | `agent-core/openjiuwen/core/foundation/llm/schema/config.py:L142` |
| `ModelRequestConfig.max_tokens` | `None` | 单次生成最大 token 数，`None` 表示不限制 | `agent-core/openjiuwen/core/foundation/llm/schema/config.py:L143` |
| `ModelClientConfig`（模型连接配置类） | — | 模型客户端连接参数集合（endpoint/key/provider 等） | `agent-core/openjiuwen/core/foundation/llm/schema/config.py:L39-L137` |
| `ContextEngineConfig.max_context_message_num` | 见定义 | 上下文保留的最大消息条数 | `agent-core/openjiuwen/core/context_engine/schema/config.py:L99` |
| `ContextEngineConfig.default_window_round_num` | 见定义 | 默认保留的对话轮数窗口 | `agent-core/openjiuwen/core/context_engine/schema/config.py:L101` |
| `ContextEngineConfig.enable_reload` | 见定义 | 是否允许上下文重载 | `agent-core/openjiuwen/core/context_engine/schema/config.py:L102` |
| `ContextEngineConfig.enable_tiktoken_counter` | 见定义 | 是否使用 tiktoken 精确计数 | `agent-core/openjiuwen/core/context_engine/schema/config.py:L103` |
| `ContextEngineConfig.context_window_tokens` | 见定义 | 上下文窗口 token 上限 | `agent-core/openjiuwen/core/context_engine/schema/config.py:L104` |
| `ContextEngineConfig.enable_context_debug` | 见定义 | 是否输出上下文调试信息 | `agent-core/openjiuwen/core/context_engine/schema/config.py:L112` |
| 摘要压缩 `enabled` | `False` | 上下文压缩默认关闭 | `agent-core/openjiuwen/core/context_engine/schema/config.py:L12` |
| 摘要压缩 `chunk_size_tokens` | `3000` | 压缩分块大小 | `agent-core/openjiuwen/core/context_engine/schema/config.py:L13` |
| `DeepAgentSpec.enable_task_loop` | `True` | 是否启用深度任务循环 | `agent-core/openjiuwen/harness/schema/deep_agent_spec.py:L441` |
| `DeepAgentSpec.enable_security_rail` | `True` | 是否启用安全护栏 | `agent-core/openjiuwen/harness/schema/deep_agent_spec.py:L444` |
| `DeepAgentSpec.max_iterations` | `15` | Deep Agent 最大迭代次数 | `agent-core/openjiuwen/harness/schema/deep_agent_spec.py:L446` |
| `DeepAgentSpec.enable_skill_discovery` | `False` | 是否启用技能自动发现 | `agent-core/openjiuwen/harness/schema/deep_agent_spec.py:L453` |
| `DeepAgentSpec.restrict_to_sandbox` | `False` | 是否强制在沙箱内执行 | `agent-core/openjiuwen/harness/schema/deep_agent_spec.py:L472` |
| `DeepAgentSpec.completion_timeout` | `600.0` | 单次完成超时（秒） | `agent-core/openjiuwen/harness/schema/deep_agent_spec.py:L474` |
| `ObservabilityConfig.enabled` | `True` | 可观测性开关 | `agent-core/openjiuwen/extensions/observability/config.py:L53` |
| `ObservabilityConfig.service_name` | `"openjiuwen-agent-teams"` | 上报服务名 | `agent-core/openjiuwen/extensions/observability/config.py:L54` |
| `ObservabilityConfig.exporter` | `"otlp_grpc"` | Trace 导出协议 | `agent-core/openjiuwen/extensions/observability/config.py:L55` |
| `ObservabilityConfig.endpoint` | `"http://localhost:4317"` | OTLP 采集端点 | `agent-core/openjiuwen/extensions/observability/config.py:L56` |
| `ObservabilityConfig.sample_rate` | `1.0` | 采样率 | `agent-core/openjiuwen/extensions/observability/config.py:L57` |
| `ObservabilityConfig.redact_prompts` | `False` | 是否脱敏 prompt 内容 | `agent-core/openjiuwen/extensions/observability/config.py:L58` |
| `ObservabilityConfig.backend` | `"langfuse"` | 可观测性后端 | `agent-core/openjiuwen/extensions/observability/config.py:L62` |
| `DEFAULT_TOOL_CALL_TIMEOUT` | `300.0` | 工具调用默认超时（秒） | `agent-core/openjiuwen/core/single_agent/ability_manager.py:L78` |
| `MAX_TOOL_CALL_TIMEOUT_HARD_LIMIT` | `3600.0` | 工具调用超时硬上限（秒） | `agent-core/openjiuwen/core/single_agent/ability_manager.py:L82-L83` |

#### 扩展点

- **扩展点 A: 向量存储注册（`register_vector_store`）**
  - 接口定义: `agent-core/openjiuwen/core/foundation/store/__init__.py:L42-L60`
  - 注入方式: 调用 `register_vector_store(name, cls)` 注册自定义向量库实现，按名称解析
- **扩展点 B: 远程客户端注册（`openjiuwen.remote_clients` entry point）**
  - 接口定义: `agent-core/openjiuwen/core/runner/drunner/remote_client/__init__.py:L20-L40`
  - 注入方式: 通过 `pyproject.toml` 的 `[project.entry-points."openjiuwen.remote_clients"]` 声明第三方包，运行期按 entry point 名解析
  - 证据: `agent-core/pyproject.toml:L164-L165`
- **扩展点 C: 服务端适配器注册（`openjiuwen.server_adapters` entry point）**
  - 接口定义: `agent-core/openjiuwen/core/runner/drunner/server_adapter/__init__.py:L29-L59`
  - 注入方式: `[project.entry-points."openjiuwen.server_adapters"]` 声明，`_resolve_entry_point` 动态加载
  - 证据: `agent-core/pyproject.toml:L167-L168`
- **扩展点 D: Agent Rail（护栏轨道）**
  - 接口定义: `agent-core/openjiuwen/core/single_agent/rail/base.py:L672-L720`（`AgentRail(ABC)`）
  - 注入方式: 子类化 `AgentRail` 并在 manifest 中声明，由 `_build_rail_from_entry_point` 装配
  - 证据: `agent-core/openjiuwen/harness/manifest/meta_elements.py:L507-L540`
- **扩展点 E: Harness 扩展热绑定（`apply_extension_hot`）**
  - 接口定义: `agent-core/openjiuwen/harness/extension_binder.py:L27-L60`
  - 注入方式: 运行期传入扩展描述对象，异步热挂载到已有 Agent
- **扩展点 F: 会话检查点后端（`Checkpointer`）**
  - 接口定义: `agent-core/openjiuwen/core/session/checkpointer/base.py:L14-L60`
  - 注入方式: 子类化 `Checkpointer` 实现自定义持久化后端
- **扩展点 G: 模型客户端（`BaseModelClient`）**
  - 接口定义: `agent-core/openjiuwen/core/foundation/llm/model_clients/base_model_client.py:L44-L120`
  - 注入方式: 子类化后按 `model_provider` 名称被 Agent 配置选中

#### 关键外部依赖

LLM/推理: `openai`、`anthropic`、`dashscope`、`transformers`、`tiktoken`（`agent-core/pyproject.toml:L35-L39`）；协议: `fastmcp`、`mcp`、`a2a-sdk`（`agent-core/pyproject.toml:L43-L44`、`L75`）；存储/检索: `sqlalchemy`、`pymilvus`、`pgvector`、`chromadb`、`elasticsearch`、`redis`、`pyoxigraph`（`agent-core/pyproject.toml:L32`、`L41`、`L68`、`L77-L85`）；消息: `pulsar`（`agent-core/pyproject.toml:L76`）；记忆: `mem0ai`、`JiuwenMemory`（`agent-core/pyproject.toml:L89-L90`）；外部 Agent SDK: `claude-agent-sdk`、`openai-codex`（`agent-core/pyproject.toml:L92-L93`）。

---

### 2.2 Agent Studio

仓库路径: `agent-studio/`（Java 后端 + Angular 前端 + Python agent_builder / agent-runtime 子工程）

#### 核心功能

- **多模块 Spring Boot 后端**：Maven 聚合 POM 声明 5 个模块（studio-storage / studio-common / studio-manager / studio-manager-api / studio-manager-service）。
  - 证据: `agent-studio/backend/pom.xml:L16-L22`
- **studio-manager 主服务入口**：Spring Boot 应用，开启组件扫描、Mapper 扫描、定时任务、AOP 与 Feign。
  - 证据: `agent-studio/backend/studio-manager/src/main/java/com/openjiuwen/studio/agent/manager/Application.java:L24-L47`
- **可视化工作流节点类型体系**：以枚举穷举画布可用节点（START/END/LLM/AGENT/KNOWLEDGE_REPO/PLUGIN/BRANCH/CODE/INTENT_DETECTION/LOOP/HTTP/MCP/LTM/QA 等），并携带其 IR 类型与 Dify 兼容别名。
  - 证据: `agent-studio/backend/studio-common/src/main/java/com/openjiuwen/studio/agent/common/enums/NodeType.java:L20-L200`（START `L20`、END `L25`、LLM `L30`、AGENT `L35`、LOOP `L141`、HTTP `L171`、MCP `L176`）
- **IR（中间表示）翻译引擎**：把 Studio 画布 DSL 翻译成 jiuwen 运行时可执行 IR，每种节点一个 Adapter。
  - 证据: `agent-studio/backend/studio-manager-service/src/main/java/com/openjiuwen/studio/agent/manager/workflow/jiuwen/adapt/Adapter.java:L15-L56`
- **Dify DSL 导入**：通过 `NodeConverter` 集合把 Dify 工作流转换为 Studio 节点。
  - 证据: `agent-studio/backend/studio-manager-service/src/main/java/com/openjiuwen/studio/agent/manager/workflow/convert/adapt/difyadapter/NodeConverter.java:L18-L46`
- **发布/下线到 Agent Runtime**：通过 Feign 调用 Runtime 的 release 接口完成智能体上下架。
  - 证据: `agent-studio/backend/studio-manager-service/src/main/java/com/openjiuwen/studio/agent/manager/rce/client/AgentRuntimeClient.java:L42-L62`（`POST /v1/{project_id}/releases` 见 `L51`，`DELETE .../{release_id}` 见 `L61`）
- **MCP 服务器管理与调用**：MCP 注册中心 CRUD + 鉴权抽象 + 启动时同步。
  - 证据: `agent-studio/backend/studio-manager-service/src/main/java/com/openjiuwen/studio/agent/manager/service/mcp/auth/IMcpBase.java:L13-L31`、`agent-studio/backend/studio-manager-service/src/main/java/com/openjiuwen/studio/agent/manager/service/mcp/McpConfig.java:L13-L19`
- **知识库/RAG 接入**：支持自建向量库、KooSearch、LakeSearch 三种后端并可切换。
  - 证据: `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L387-L410`
- **Prompt 工程与评测**：Prompt CRUD/版本、评测任务、优化任务、SSE 流式推理。
  - 证据: `agent-studio/agent_builder/adapter/template_adapter.py:L18-L216`（模板装配 ABC）
- **前端 DAG 画布**：Angular 20 + AntV X6 画布 + Monaco 代码编辑器 + ng-zorro-antd。
  - 证据: `agent-studio/frontend/package.json:L21-L63`

#### 配置选项

以下均出自 `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml`（行号为该文件行号）。

| 配置项名 | 默认值 | 说明 | 证据 |
| --- | --- | --- | --- |
| `soft_delete` | `true` | 逻辑删除开关 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L4` |
| `spring_datasource_url` | 无（必填） | 主库 JDBC 连接串 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L13` |
| `spring_datasource_driver_class_name` | `org.mariadb.jdbc.Driver` | 数据库驱动 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L16` |
| `spring_sql_init_mode` | `always` | 启动时自动执行 DDL/DML | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L30` |
| `redis_host` | `127.0.0.1` | Redis 主机 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L76`、`L173` |
| `redis_port` | `6379` | Redis 端口 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L77`、`L175` |
| `agent_runtime_endpoint` | `http://127.0.0.1:31014` | Agent Runtime 基地址 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L102`、`L495`、`L508`、`L716` |
| `studio_operationLog_switch` | `false` | 操作审计日志开关 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L109` |
| `server.port` | `31111` | studio-manager 服务端口 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L114` |
| `dynamic_permission_enabled` | `false` | 动态权限（从 OBS 拉取角色权限）开关 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L151` |
| `system_crypt_name` | `NO_OP_CIPHER` | 敏感信息加密算法；默认值为**不加密** | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L154` |
| `audio_support_interaction` | `false` | 语音交互开关 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L158` |
| `okhttp_read_timeout` | `900`（秒） | OkHttp 读超时（大模型流式） | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L168` |
| `redis_expire_time` | `604800`（7 天） | 会话消息在 Redis 的 TTL | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L176` |
| `redis_max_message_num` | `100` | 单会话在 Redis 中保留的最大消息条数 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L177` |
| `redis_client_type` | `redisson` | Redis 客户端实现 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L186` |
| `inner.agent-runtime.endpoint` | 空 | 内网 Runtime 地址 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L205` |
| `run_agent_stream_url` | `/v1/%s/agents/%s/conversations` | Runtime 流式会话 URL 模板 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L207` |
| `knowledge_source` | `LakeSearch` | 默认知识库后端 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L387` |
| `knowledge_internal_enabled` | `true` | 是否开放自建知识库 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L389` |
| `knowledge_bound_limit` | `3` | 单智能体可绑定知识库数上限 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L391`、`L573` |
| `knowledge_ocr_enable` | `false` | 文档 OCR 解析开关 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L410` |
| `mcp_name_en_check` | `false` | MCP 名称英文校验 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L427` |
| `enable_url_check` | `true` | URL 校验（SSRF 防护） | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L430`、`L576` |
| `env_sandbox_enable` | `false` | 代码节点沙箱执行开关 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L434` |
| `max_upload_num` | `20` | 单次最大上传文件数 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L450` |
| `max_upload_total_size` | `204800`（KB） | 上传总大小上限 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L452` |
| `file_upload_expiration_days` | `7` | 上传文件保留天数 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L457` |
| `agent_builder_endpoint` | `http://127.0.0.1:31015` | agent_builder（Python）基地址 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L510` |
| `soft_delete_ttl_days` | `730` | 逻辑删除数据物理清理周期 | `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L832` |

#### 扩展点

- **扩展点 A: 工作流节点 IR 适配器（`Adapter` / `AbstractIRNodeAdapter`）**
  - 接口定义: `agent-studio/backend/studio-manager-service/src/main/java/com/openjiuwen/studio/agent/manager/workflow/jiuwen/adapt/Adapter.java:L15-L56`
  - 注入方式: 在 `NodeType` 枚举新增类型，实现类继承 `AbstractIRNodeAdapter` 并注册为 Spring Bean，由 `IrAdapterService` 按 `getNodeType()` 汇聚分发
  - 证据: `agent-studio/backend/studio-common/src/main/java/com/openjiuwen/studio/agent/common/enums/NodeType.java:L20-L200`
- **扩展点 B: Dify 节点转换器（`NodeConverter`）**
  - 接口定义: `agent-studio/backend/studio-manager-service/src/main/java/com/openjiuwen/studio/agent/manager/workflow/convert/adapt/difyadapter/NodeConverter.java:L18-L46`
  - 注入方式: 实现该接口并标注 `@Component`，`DifyDSLAdapter` 以 `List<NodeConverter>` 构造注入并按 `supportNodeType` 过滤
- **扩展点 C: MCP 鉴权策略（`IMcpBase`）**
  - 接口定义: `agent-studio/backend/studio-manager-service/src/main/java/com/openjiuwen/studio/agent/manager/service/mcp/auth/IMcpBase.java:L13-L31`
  - 注入方式: 提供该接口的 Spring 实现（可用 `@Primary` 覆盖默认 `McpBaseImpl`）
- **扩展点 D: 动态权限加载（`PermissionLoader` + OBS JSON）**
  - 接口定义: `agent-studio/backend/studio-manager-service/src/main/java/com/openjiuwen/studio/agent/manager/config/PermissionProperties.java:L18-L40`
  - 注入方式: 通过 `dynamic_permission_enabled` 开启，指向自定义的 OBS 角色权限 JSON
  - 证据: `agent-studio/backend/studio-manager-service/src/main/resources/application-manager.yml:L151`
- **扩展点 E: Prompt 模板装配 ABC（Python）**
  - 接口定义: `agent-studio/agent_builder/adapter/template_adapter.py:L18-L216`
  - 注入方式: 子类化 `MetaTemplate` 并实现 `_assemble_input_value` / `_streaming_build` / `_full_build`
- **扩展点 F: 占位符编辑器 ABC（Python）**
  - 接口定义: `agent-studio/agent_builder/adapter/placeholder_editor.py:L9-L30`
  - 注入方式: 子类化并实现 `parse` / `render`

#### 关键外部依赖

Spring Boot 3.5.15、MyBatis + PageHelper、Redisson、MariaDB/PostgreSQL/OpenGauss 驱动、MCP Java SDK `0.16.0`、OkHttp SSE、swagger-parser（插件 OpenAPI 解析）、Huawei OBS SDK、Quartz（`agent-studio/backend/pom.xml:L25-L92`）；前端 Angular 20 + ng-zorro-antd + AntV X6 + Monaco（`agent-studio/frontend/package.json:L21-L63`）；Python 运行时依赖 `openjiuwen[sandbox]`（git 分支依赖）、FastAPI、spiffworkflow、mcp、elasticsearch、redis、sqlalchemy（`agent-studio/agent-runtime/pyproject.toml:L20-L40`）。

---

### 2.3 Agent Runtime

仓库路径: `agent-runtime/`（Python 多包 monorepo：`foundation` / `management` / `server` / `service` / `cli` / `applications`）

#### 核心功能

- **Agent/Plugin 部署生命周期管理**：`DeploymentManager` 以策略模式支持 subprocess / docker / k8s 三种部署后端，k8s 依赖缺失时自动降级。
  - 证据: `agent-runtime/management/openjiuwen_runtime/management/manager.py:L83-L107`
- **子进程部署器**：为每个部署创建独立 venv，pip 安装 WHL 后以 `python -m <module>` 拉起。
  - 证据: `agent-runtime/management/openjiuwen_runtime/management/deployments/subprocess/deployer.py:L114-L238`
- **Docker / K8s 部署器**：分别通过 docker CLI 与 Kubernetes Python 客户端创建工作负载。
  - 证据: `agent-runtime/management/openjiuwen_runtime/management/deployments/docker/deployer.py:L70-L130`、`agent-runtime/management/openjiuwen_runtime/management/deployments/k8s/deployer.py:L40-L60`
- **管理面 REST API**：`/health`、`POST /api/v1/agents/deploy`、`GET /api/v1/agents`、`GET|DELETE /api/v1/agents/{deployment_id}`。
  - 证据: `agent-runtime/server/openjiuwen_runtime/server/main.py:L84-L349`
- **单 Agent 服务 SDK（AgentApp）**：为每个已部署 Agent 暴露 `/query`（SSE 流式）、`/reset_conversation`、`/agent_detail`、`/health`。
  - 证据: `agent-runtime/service/openjiuwen_runtime/service/app/agent_app.py:L153-L336`
- **会话路由与并发配额**：`SessionRouter`（request_id→session_id）与 `ServiceRouter`（session_id→service_id）维护亲和关系。
  - 证据: `agent-runtime/management/openjiuwen_runtime/management/session/router.py:L10-L86`
- **WebSocket 多路复用通道**：单条 WS 连接上复用多个 `request_id` 流。
  - 证据: `agent-runtime/management/openjiuwen_runtime/management/session/ws_client_channel.py:L1-L57`
- **租户上下文中间件**：从 `X-User-ID` / `X-Space-ID` 头解析租户并注入 `request.state`。
  - 证据: `agent-runtime/server/openjiuwen_runtime/server/middleware/tenant.py:L22-L60`
- **链路层 Ed25519 鉴权**：WebSocket 控制链路的令牌签名/校验与证书 pin 存储。
  - 证据: `agent-runtime/foundation/openjiuwen_runtime/foundation/security/link_auth.py:L1-L81`
- **A2A JSON-RPC 编排服务**：挂载 A2A SDK 路由，Redis 任务存储 + 领导者选举式启动协调，向 VersatileAdapter 下派子任务。
  - 证据: `agent-runtime/applications/a2a_service/app.py:L388-L489`
- **工作流 IR 执行服务**：`POST /execute_invoke` / `POST /execute_stream`，从 OBS/Redis 取 IR 后驱动 `openjiuwen` Runner 执行。
  - 证据: `agent-runtime/applications/ir_execution_service/ir_execution_service/ir_execution_service_app.py:L109-L200`
- **CLI 打包与部署**：`openjiuwen` 命令组提供 `agent deploy/list/get/delete`、`plugin ...`、`new agent` 脚手架。
  - 证据: `agent-runtime/cli/openjiuwen_runtime/cli/main.py:L40-L92`、`agent-runtime/cli/pyproject.toml:L36`

#### 配置选项

| 配置项名 | 默认值 | 说明 | 证据 |
| --- | --- | --- | --- |
| `RUNTIME_DB_TYPE` | `"sqlite"` | 后端数据库类型（sqlite/mysql/gaussdb/opengauss） | `agent-runtime/foundation/openjiuwen_runtime/foundation/config.py:L20` |
| `RUNTIME_DB_HOST` / `PORT` / `USER` / `PASSWORD` / `NAME` | 均为 `None` | 数据库连接参数（非 sqlite 时必填） | `agent-runtime/foundation/openjiuwen_runtime/foundation/config.py:L25-L29` |
| `IP` | `None` | 对外通告的部署实例 IP | `agent-runtime/foundation/openjiuwen_runtime/foundation/config.py:L34` |
| `LOWCODE_IMAGE` | `None` | 低代码 Agent 容器镜像 | `agent-runtime/foundation/openjiuwen_runtime/foundation/config.py:L35` |
| `DEPLOY_DIR` | `"/tmp/deploys"` | 部署产物根目录 | `agent-runtime/foundation/openjiuwen_runtime/foundation/config.py:L38` |
| `DIST_DIR` | `"/tmp/dist"` | WHL 包目录 | `agent-runtime/foundation/openjiuwen_runtime/foundation/config.py:L39` |
| `HOST` | `"0.0.0.0"` | 管理服务监听地址 | `agent-runtime/foundation/openjiuwen_runtime/foundation/config.py:L40` |
| `PORT` | `8186` | 管理服务监听端口 | `agent-runtime/foundation/openjiuwen_runtime/foundation/config.py:L41` |
| `UV_EXTRA_ARGS` | `""` | 透传给 `uv pip install` 的额外参数 | `agent-runtime/foundation/openjiuwen_runtime/foundation/config.py:L42` |
| `DEPLOY_TYPE` | `"subprocess"` | 全局部署模式 | `agent-runtime/foundation/openjiuwen_runtime/foundation/config.py:L43` |
| `MODE` | `"product"` | `dev` 用本地 dist 安装，`product` 走 PyPI | `agent-runtime/foundation/openjiuwen_runtime/foundation/config.py:L44` |
| `KUBECONFIG` | `""` | K8s kubeconfig 路径 | `agent-runtime/foundation/openjiuwen_runtime/foundation/config.py:L45` |
| `K8S_DEFAULT_CONFIG_PATH` | `""` | K8s 部署默认参数 JSON 路径 | `agent-runtime/foundation/openjiuwen_runtime/foundation/config.py:L46` |
| `CLAW_LINK_AUTH_MODE` | `"off"` | 链路鉴权模式（off/observe/enforce），默认关闭 | `agent-runtime/foundation/openjiuwen_runtime/foundation/security/link_auth.py:L64-L71` |
| `CLAW_LINK_TOKEN_TTL` | `300`（秒） | 链路令牌有效期 | `agent-runtime/foundation/openjiuwen_runtime/foundation/security/link_auth.py:L74-L81` |
| `WORKFLOW_EXECUTE_TIMEOUT` | `"300"` | IR 工作流执行超时（秒） | `agent-runtime/applications/ir_execution_service/ir_execution_service/ir_execution_service_app.py:L65` |
| `RUNTIME_USERDATA` | 无 | 通过环境变量透传给被部署 Agent 的用户数据 | `agent-runtime/service/openjiuwen_runtime/service/app/base_app.py:L35` |
| `RUNTIME_IR_PATH` | 无 | 低代码 Agent 的 IR 文件路径 | `agent-runtime/service/openjiuwen_runtime/service/app/base_app.py:L41` |
| `bootstrap_coordination_enabled` | `True` | A2A 服务启动的 Redis 领导者协调开关 | `agent-runtime/applications/a2a_service/config.py:L36` |
| `rate_limit_max_requests` | `1` | 单会话并发请求上限 | `agent-runtime/applications/a2a_service/config.py:L43` |
| `versatile_adapter_url` | `None` | VersatileAdapter A2A 端点 | `agent-runtime/applications/a2a_service/config.py:L49` |
| `versatile_adapter_timeout` | `57`（秒） | 调用 VersatileAdapter 的超时 | `agent-runtime/applications/a2a_service/config.py:L52` |
| `max_concurrent_sub_agents` | `3` | 并发子 Agent 上限 | `agent-runtime/applications/a2a_service/config.py:L59` |
| `sub_agent_timeout_seconds` | `1800` | 单个子 Agent 执行超时 | `agent-runtime/applications/a2a_service/config.py:L60` |
| `max_call_depth` | `3` | 递归派发最大深度 | `agent-runtime/applications/a2a_service/config.py:L63` |
| CLI `--host` / `--port` | `"0.0.0.0"` / `8090` | 单 Agent 服务监听地址与端口 | `agent-runtime/service/openjiuwen_runtime/service/app/base_app.py:L54-L55` |

#### 扩展点

- **扩展点 A: 部署器（`Deployer[T]` ABC）**
  - 接口定义: `agent-runtime/management/openjiuwen_runtime/management/deployments/base/deployer.py:L15-L68`
  - 注入方式: 子类化后传入 `BaseDeploymentStrategy(deployer=...)`
- **扩展点 B: 部署策略（`BaseDeploymentStrategy[T]`）**
  - 接口定义: `agent-runtime/management/openjiuwen_runtime/management/deployments/base/strategy.py:L67-L269`
  - 注入方式: `DeploymentManager(strategies={DeployMode.X: MyStrategy()})`
  - 证据: `agent-runtime/management/openjiuwen_runtime/management/manager.py:L83-L89`
- **扩展点 C: 会话策略（`ISessionStrategy` ABC）**
  - 接口定义: `agent-runtime/management/openjiuwen_runtime/management/session/interfaces.py:L169-L177`
  - 注入方式: 通过 `IAccess.init(..., strategy=...)` 注入
- **扩展点 D: 响应解析器（`IResponseParser` ABC）**
  - 接口定义: `agent-runtime/management/openjiuwen_runtime/management/session/interfaces.py:L141-L153`
  - 注入方式: `IAccess.init(response_parser=...)` 或 `IServiceMessageChannel.send(..., response_parser=...)`
- **扩展点 E: 服务/会话处理器（`IServiceHandler` / `ISessionHandler`）**
  - 接口定义: `agent-runtime/management/openjiuwen_runtime/management/session/interfaces.py:L292-L363`
  - 注入方式: 由 `IServiceInstanceFactory.new_service()` 产出（`interfaces.py:L246-L251`）
- **扩展点 F: 部署控制器协议（`IDeployController` Protocol）**
  - 接口定义: `agent-runtime/management/openjiuwen_runtime/management/session/runtime.py:L11-L28`
  - 注入方式: 结构化子类型（duck typing），实现 `resource_id` / `deploy()` / `delete()` 即可
- **扩展点 G: 查询中间件（`Middleware`）**
  - 接口定义: `agent-runtime/service/openjiuwen_runtime/service/app/middleware.py:L50-L133`（钩子 `before_query` / `after_query` / `on_error` / `before_response`）
  - 注入方式: `AgentApp.add_middleware(instance)` 或 `@app.middleware(MyMiddleware)`
  - 证据: `agent-runtime/service/openjiuwen_runtime/service/app/agent_app.py:L113-L143`
- **扩展点 H: 生命周期钩子（`@app.init` / `@app.shutdown`）**
  - 接口定义: `agent-runtime/service/openjiuwen_runtime/service/app/base_app.py:L122-L146`
  - 注入方式: 装饰函数，FastAPI startup/shutdown 事件触发（`base_app.py:L151-L161`）
- **扩展点 I: 查询钩子（`@app.query` / `@app.agent_detail`）**
  - 接口定义: `agent-runtime/service/openjiuwen_runtime/service/app/agent_app.py:L87-L111`
  - 注入方式: 装饰异步生成器函数，作为 `_query_hook` / `_agent_detail_hook`
- **扩展点 J: 插件工具注册（`@restful.tool()`）**
  - 接口定义: `agent-runtime/service/openjiuwen_runtime/service/app/restful.py:L44-L60`
  - 注入方式: 在 `PluginApp` 内装饰函数，自动生成 `POST /<tool_name>` 与 `GET /tools` 清单
- **扩展点 K: 子应用挂载（`AppGroup.mount()`）**
  - 接口定义: `agent-runtime/service/openjiuwen_runtime/service/app/app_group.py:L76-L100`
  - 注入方式: 以 URL 前缀挂载另一个 `BaseApp`

#### 关键外部依赖

`fastapi` / `uvicorn`、`sqlalchemy`、`pymysql`/`aiomysql`/`aiosqlite`、`redis`、`pydantic-settings`、`cryptography`（Ed25519）、可选 `async-gaussdb` 与 `aio-pika`（`agent-runtime/foundation/pyproject.toml:L10-L28`）；`kubernetes` / `kubernetes_asyncio`、`websockets`、`httpx`（`agent-runtime/management/pyproject.toml:L10-L35`）；`a2a-sdk==1.0.0`（`agent-runtime/applications/a2a_service/pyproject.toml:L7-L29`）；`openjiuwen[chromadb,obs]` 与 `openjiuwen_studio`（`agent-runtime/applications/ir_execution_service/pyproject.toml:L11-L22`）。
