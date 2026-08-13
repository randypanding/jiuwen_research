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

---

### 2.4 Agent Memory

仓库路径: `agent-memory/`（Python 内核包 `jiuwen_memory` / pip 名 `JiuwenMemory` + Java 平台 `agent-memory-platform` + Vue 前端）

#### 核心功能

- **六类长期记忆建模**：用户画像、语义、情景、变量、摘要、中期记忆。
  - 证据: `agent-memory/jiuwen_memory/memory_core/manage/mem_model/memory_unit.py:L9-L17`
- **记忆开关矩阵（AgentMemoryConfig）**：长期记忆及各子类型独立开关。
  - 证据: `agent-memory/jiuwen_memory/memory_core/config/config.py:L70-L77`
- **多存储后端工厂**：向量库（chroma/milvus/elasticsearch/gauss）、KV（db/in_memory/shelve）、DB（default/gauss）按环境变量分发。
  - 证据: `agent-memory/jiuwen_memory/server/store_factory.py:L82-L197`
- **记忆索引抽象（Simple 向量 vs File Markdown+sqlite-vec）**：可切换的索引后端。
  - 证据: `agent-memory/jiuwen_memory/foundation/store/base_memory_index.py:L48-L110`、`agent-memory/jiuwen_memory/server/memory_server.py:L431-L444`
- **Embedding 抽象与 HTTP API 实现**。
  - 证据: `agent-memory/jiuwen_memory/foundation/store/base_embedding.py:L24-L45`、`agent-memory/jiuwen_memory/server/memory_server.py:L450-L457`
- **离线 Dreaming（跨会话记忆整合）**：后台周期任务压缩会话、抽取知识、可选触发遗忘。
  - 证据: `agent-memory/jiuwen_memory/memory_core/config/config.py:L111-L125`
- **艾宾浩斯遗忘（软删除）**：低分记忆置 `blacklisted`（仍保留在存储中，仅从检索中剔除）。
  - 证据: `agent-memory/jiuwen_memory/memory_core/config/config.py:L79-L109`、`agent-memory/jiuwen_memory/memory_core/process/forgetting/evaluator.py:L1-L60`
- **记忆落盘加密（AES-256-GCM / SM4 可插拔）**。
  - 证据: `agent-memory/jiuwen_memory/foundation/codec/__init__.py:L1-L53`、`agent-memory/jiuwen_memory/server/memory_server.py:L467-L505`
- **分布式锁**：基于 KV 的 `exclusive_set` + 心跳续期，保护写入与批删。
  - 证据: `agent-memory/jiuwen_memory/server/memory_server.py:L826-L830`
- **REST 记忆 API（FastAPI，默认 8000）**：add/search/update/delete/分页/变量等 17+ 端点。
  - 证据: `agent-memory/jiuwen_memory/server/memory_server.py:L558-L870`
- **MCP 工具服务器**：6 个 MCP 工具，支持 `streamable-http` 与 `stdio`。
  - 证据: `agent-memory/jiuwen_memory/server/mcp_server.py:L352-L470`
- **Scope/User 多租户隔离**：所有操作携带 `user_id` + `scope_id`，支持 per-scope 覆盖模型与抽取规则。
  - 证据: `agent-memory/jiuwen_memory/memory_core/config/config.py:L49-L68`
- **Java 平台服务（Spring Boot，默认 9000）**：认证中心、租户中心、Scope 中心、运维中心、日志中心、WebUI 聚合。
  - 证据: `agent-memory/agent-memory-platform/platform/src/main/java/com/openjiuwen/memory/MemoryServiceApplication.java:L28-L34`

#### 配置选项

Python 内核（`os.getenv` 读取，无统一 BaseSettings）：

| 配置项名 | 默认值 | 说明 | 证据 |
| --- | --- | --- | --- |
| `IP` | `"127.0.0.1"` | 记忆服务监听地址 | `agent-memory/jiuwen_memory/server/memory_server.py:L923` |
| `PORT` | `"8000"` | 记忆服务端口 | `agent-memory/jiuwen_memory/server/memory_server.py:L924` |
| `MEMORY_API_KEY` | `""`（**空即不鉴权**） | REST 接口鉴权凭据，为空字符串时完全跳过鉴权 | `agent-memory/jiuwen_memory/server/memory_server.py:L212` |
| `MEMORY_DATA_DIR` | `~/.jiuwenmemory/memory_data` | 数据根目录 | `agent-memory/jiuwen_memory/server/store_factory.py:L21-L29` |
| `DB_URL` | 上述目录下的 `sqlite_db.db` | SQLAlchemy 异步连接串 | `agent-memory/jiuwen_memory/server/store_factory.py:L62-L70` |
| `FILE_MEMORY_DATA_DIR` | `~/.jiuwenmemory/file_memory_data` | 文件型索引根目录 | `agent-memory/jiuwen_memory/server/store_factory.py:L32-L45` |
| `INDEX_BACKEND` | `"simple"` | 索引后端（simple / file） | `agent-memory/jiuwen_memory/server/memory_server.py:L432` |
| `KV_STORE_TYPE` | `"db"` | KV 后端 | `agent-memory/jiuwen_memory/server/store_factory.py:L84` |
| `DB_STORE_TYPE` | `"default"` | DB 后端 | `agent-memory/jiuwen_memory/server/store_factory.py:L113` |
| `VECTOR_STORE_TYPE` | `"chroma"` | 向量后端 | `agent-memory/jiuwen_memory/server/store_factory.py:L135` |
| `VECTOR_MILVUS_URI` / `_TOKEN` / `_DATABASE` | `""` / `""` / `"default"` | Milvus 连接参数 | `agent-memory/jiuwen_memory/server/store_factory.py:L146-L148` |
| `VECTOR_ES_HOSTS` / `_USERNAME` / `_PASSWORD` | `""` | Elasticsearch 连接参数 | `agent-memory/jiuwen_memory/server/store_factory.py:L155-L163` |
| `VECTOR_ES_INDEX_PREFIX` | `"agent_vector"` | ES 索引前缀 | `agent-memory/jiuwen_memory/server/store_factory.py:L183` |
| `VECTOR_GAUSS_HOST` / `_PORT` | `"localhost"` / `"5432"` | GaussDB 向量库连接 | `agent-memory/jiuwen_memory/server/store_factory.py:L190-L191` |
| `EMBED_MODEL_NAME` / `EMBED_API_KEY` / `EMBED_API_BASE` | `""` | Embedding 服务参数 | `agent-memory/jiuwen_memory/server/memory_server.py:L451-L453` |
| `MODEL_NAME` / `MODEL_PROVIDER` / `API_KEY` / `API_BASE` | `""` | 抽取用 LLM 参数 | `agent-memory/jiuwen_memory/server/memory_server.py:L510-L515` |
| `TEMPERATURE` | `0.95` | 抽取 LLM 温度 | `agent-memory/jiuwen_memory/server/memory_server.py:L511` |
| `MODEL_SSL_VERIFY` | `"false"` | 调用 LLM 时是否校验 TLS 证书（**默认不校验**） | `agent-memory/jiuwen_memory/server/memory_server.py:L517` |
| `MEMORY_ENABLE_MIDDLE_MEMORY` | `"false"` | 中期记忆整合开关 | `agent-memory/jiuwen_memory/server/memory_server.py:L519` |
| `MEMORY_CODEC` | `""` | 落盘加密算法（aes / sm4 / 自定义注册名） | `agent-memory/jiuwen_memory/server/memory_server.py:L460` |
| `AES_KEY` / `SM4_KEY` | `""` | 对应密钥（十六进制） | `agent-memory/jiuwen_memory/server/memory_server.py:L490`、`L471` |
| `ForgettingConfig.enabled` | `False` | 遗忘功能开关 | `agent-memory/jiuwen_memory/memory_core/config/config.py:L102` |
| `ForgettingConfig.threshold` | `0.15` | 低于该分数的记忆被软遗忘 | `agent-memory/jiuwen_memory/memory_core/config/config.py:L103` |
| `ForgettingConfig.max_evict` | `1000` | 单轮最大淘汰条数（防雪崩） | `agent-memory/jiuwen_memory/memory_core/config/config.py:L104` |
| `ForgettingConfig.min_retention_days` | `30` | 最近访问保护窗口（天） | `agent-memory/jiuwen_memory/memory_core/config/config.py:L105` |
| `DreamingConfig.enabled` | `False` | Dreaming 开关 | `agent-memory/jiuwen_memory/memory_core/config/config.py:L117` |
| `DreamingConfig.interval_seconds` | `14400.0`（4 小时） | Dreaming 周期 | `agent-memory/jiuwen_memory/memory_core/config/config.py:L118` |
| `DreamingConfig.min_session_rounds` | `4` | 参与整合的最小会话轮数 | `agent-memory/jiuwen_memory/memory_core/config/config.py:L119` |
| `DreamingConfig.max_sessions_per_sweep` | `10` | 单轮最大处理会话数 | `agent-memory/jiuwen_memory/memory_core/config/config.py:L120` |
| `DreamingConfig.max_compress_tokens` | `30000` | 压缩 token 预算 | `agent-memory/jiuwen_memory/memory_core/config/config.py:L121` |
| `DreamingConfig.max_items_per_session` | `5` | 单会话最多抽取知识条数 | `agent-memory/jiuwen_memory/memory_core/config/config.py:L122` |

Java 平台（`agent-memory/agent-memory-platform/platform/src/main/resources/application.yml`）：

| 配置项名 | 默认值 | 说明 | 证据 |
| --- | --- | --- | --- |
| `spring.profiles.active` | `sqlite` | 默认数据库 profile（sqlite/mysql/gaussdb） | `agent-memory/agent-memory-platform/platform/src/main/resources/application.yml:L7` |
| `server.port` | `9000` | 平台服务端口 | `agent-memory/agent-memory-platform/platform/src/main/resources/application.yml:L18` |
| `platform.memory-service.base-url` | `http://127.0.0.1:8000` | Python 记忆内核地址 | `agent-memory/agent-memory-platform/platform/src/main/resources/application.yml:L35` |
| `platform.memory-service.api-key` | `MEMERY-2026` | 调用内核的鉴权 Key（**硬编码默认值**） | `agent-memory/agent-memory-platform/platform/src/main/resources/application.yml:L36` |
| `platform.memory-service.connect-timeout` | `10s` | 连接超时 | `agent-memory/agent-memory-platform/platform/src/main/resources/application.yml:L37` |
| `platform.memory-service.read-timeout` | `120s` | 读超时 | `agent-memory/agent-memory-platform/platform/src/main/resources/application.yml:L38` |
| `platform.feature.default-scope` | `__default__` | 默认 Scope | `agent-memory/agent-memory-platform/platform/src/main/resources/application.yml:L40` |
| `platform.confirm-token.ttl` | `5m` | 二次确认令牌有效期 | `agent-memory/agent-memory-platform/platform/src/main/resources/application.yml:L42` |

#### 扩展点

- **扩展点 A: 向量存储（`BaseVectorStore`）**
  - 接口定义: `agent-memory/jiuwen_memory/foundation/store/base_vector_store.py:L258-L670`
  - 注入方式: 子类化后直接传入 `LongTermMemory.register_store(vector_store=...)`（工厂不支持自定义类型名）
  - 证据: `agent-memory/jiuwen_memory/memory_core/long_term_memory.py:L211-L218`
- **扩展点 B: KV 存储（`BaseKVStore`）**
  - 接口定义: `agent-memory/jiuwen_memory/foundation/store/base_kv_store.py:L1-L80`
  - 注入方式: `register_store(kv_store=...)`
- **扩展点 C: DB 引擎包装（`BaseDbStore`）**
  - 接口定义: `agent-memory/jiuwen_memory/foundation/store/base_db_store.py:L1-L28`
  - 注入方式: `register_store(db_store=...)`
- **扩展点 D: Embedding 模型（`Embedding`）**
  - 接口定义: `agent-memory/jiuwen_memory/foundation/store/base_embedding.py:L24-L45`
  - 注入方式: `register_store(embedding_model=...)`
- **扩展点 E: LLM 客户端注册表（`ClientRegistry`）**
  - 接口定义: `agent-memory/jiuwen_memory/common/clients/client_registry.py:L20-L100`
  - 注入方式: `@register_client(name, client_type="llm")` 装饰器或 `register_class(MyClient)`；`create_model_client` 内置分支未命中时回落到注册表
  - 证据: `agent-memory/jiuwen_memory/foundation/llm/model_clients/__init__.py:L48-L80`
- **扩展点 F: 存储编解码器（`StorageCodec` 协议 + `register_storage_codec`）**
  - 接口定义: `agent-memory/jiuwen_memory/foundation/codec/__init__.py:L18-L53`
  - 注入方式: `register_storage_codec("name", instance)` 后将 `MemoryEngineConfig.codec` 设为该名称
- **扩展点 G: 遗忘评估器（`ForgetEvaluator`）**
  - 接口定义: `agent-memory/jiuwen_memory/memory_core/process/forgetting/evaluator.py:L1-L60`
  - 注入方式: `ForgettingConfig(evaluator=<instance>)` → `DreamingConfig(forgetting=...)` → `start_dreaming()`；为 `None` 时回落内置 `EbbinghausEvaluator`
  - 证据: `agent-memory/jiuwen_memory/memory_core/config/config.py:L106-L109`
- **扩展点 H: Java 记忆引擎客户端 SPI（`MemoryEngineClient`）**
  - 接口定义: `agent-memory/agent-memory-platform/platform/src/main/java/com/openjiuwen/memory/common/client/MemoryEngineClient.java:L1-L50`
  - 注入方式: 提供自定义 `@Bean` 覆盖；默认实现以 `@ConditionalOnMissingBean` 装配
  - 证据: `agent-memory/agent-memory-platform/platform/src/main/java/com/openjiuwen/memory/common/spi/SpiDefaults.java:L10-L45`

#### 关键外部依赖

`pymilvus`、`chromadb`、`elasticsearch[async]`、`psycopg2-binary`（GaussDB 向量）、`asyncpg`/`aiomysql`/`async-gaussdb`/`aiosqlite`、`redis`、`sqlite-vec`（file 索引）、`sqlalchemy` + `sqlmodel` + `alembic`、`openai`、`dashscope`、`pycryptodome`（AES）、`gmssl`（SM4）、`fastapi`/`uvicorn`、`mcp`、`watchdog`、`jieba`（`agent-memory/pyproject.toml:L25-L58`）；Java 侧 Spring Boot 3.3.5、MyBatis-Plus、sqlite-jdbc / mysql-connector-j / opengauss-jdbc / gaussdbjdbc、jjwt（`agent-memory/agent-memory-platform/platform/pom.xml`）。

---

### 2.5 Agent Protocol

仓库路径: `agent-protocol/`（三个独立子工程：`A2A/cpp-sdk`、`MCP/cpp-sdk`、`AgentRegistry`）

#### 核心功能

**A2A C++17 SDK**

- **Agent Card 发布与发现**：`AgentCard` 描述能力、技能、安全方案与 JWS 签名，通过 `/.well-known/agent-card.json` 暴露。
  - 证据: `agent-protocol/A2A/cpp-sdk/include/types.h:L586-L605`、`agent-protocol/A2A/cpp-sdk/src/transport/http_server_transport.h:L24`
- **任务生命周期状态机**：`SUBMITTED / WORKING / INPUT_REQUIRED / COMPLETED / CANCELED / FAILED / REJECTED / AUTH_REQUIRED / UNSPECIFIED`。
  - 证据: `agent-protocol/A2A/cpp-sdk/include/types.h:L135-L145`、`L159-L168`
- **JSON-RPC 方法集**：`SendMessage` / `SendStreamingMessage` / `GetTask` / `CancelTask` / `SubscribeToTask` / 推送配置增删查列。
  - 证据: `agent-protocol/A2A/cpp-sdk/src/shared/common_types.h:L15-L29`
- **流式（SSE）响应**：`StreamEmitter` 输出 `Task | Message | TaskArtifactUpdateEvent | TaskStatusUpdateEvent` 变体。
  - 证据: `agent-protocol/A2A/cpp-sdk/src/server/jsonrpc_handler.h:L15-L110`、`agent-protocol/A2A/cpp-sdk/src/shared/common_types.h:L71-L72`
- **Webhook 推送通知**：`PushNotificationConfig`（url/token/authentication）+ 内存存储 + 发送器。
  - 证据: `agent-protocol/A2A/cpp-sdk/include/types.h:L181-L188`
- **五类安全方案**：APIKey、HTTP Auth、OAuth2（4 种 flow）、OpenID Connect、mTLS。
  - 证据: `agent-protocol/A2A/cpp-sdk/include/types.h:L427-L505`
- **协议版本协商**：拦截器附加/校验 `A2A-Protocol-Version`，不匹配返回 -32009。
  - 证据: `agent-protocol/A2A/cpp-sdk/include/types.h:L418-L425`

**MCP C++17 SDK**

- **服务端工具/提示词/资源注册**：`AddTool` / `AddPrompt` / `AddResource` / `AddResourceTemplate` / `AddCompletion`。
  - 证据: `agent-protocol/MCP/cpp-sdk/include/mcp/mcp_server.h:L299-L401`
- **客户端异步 API（future 风格）**。
  - 证据: `agent-protocol/MCP/cpp-sdk/include/mcp/mcp_client.h:L17-L265`
- **双传输通道**：streamable-HTTP 与 stdio，通过工厂方法创建。
  - 证据: `agent-protocol/MCP/cpp-sdk/include/mcp/mcp_server.h:L410-L438`、`agent-protocol/MCP/cpp-sdk/include/mcp/mcp_client.h:L267-L294`

**AgentRegistry（Python FastAPI，"A2X Registry"）**

- **服务/Agent 注册与注销**：通用条目与 A2A Card 两种注册形态。
  - 证据: `agent-protocol/AgentRegistry/a2x_registry/backend/routers/dataset.py:L615-L687`
- **三种检索策略**：A2X（LLM 递归分类树搜索）、vector（Chroma 向量）、traditional（LLM 关键词），并提供 WebSocket 流式检索与 LLM 相关性裁判。
  - 证据: `agent-protocol/AgentRegistry/a2x_registry/backend/routers/search.py:L22-L61`
- **心跳/租约**：注册项租约续期与释放，后台清扫过期租约。
  - 证据: `agent-protocol/AgentRegistry/a2x_registry/heartbeat/router.py:L73-L115`、`agent-protocol/AgentRegistry/a2x_registry/backend/app.py:L110-L133`
- **预约槽位（Reservation）**：Agent 启动前先占位，支撑 jiuwenswarm 的"空白队友"引导。
  - 证据: `agent-protocol/AgentRegistry/a2x_registry/backend/routers/dataset.py:L704-L765`
- **集群/反熵同步**：peer 管理 + Merkle digest + keepalive 守护。
  - 证据: `agent-protocol/AgentRegistry/a2x_registry/cluster/router.py:L105-L250`
- **API Key 鉴权（SHA-256 哈希存储）**。
  - 证据: `agent-protocol/AgentRegistry/a2x_registry/auth/router.py:L97-L265`
- **平铺 JSON 文件存储**：每个 dataset 一个目录，`service.json` / `taxonomy.json` / `lease_config.json` 等。
  - 证据: `agent-protocol/AgentRegistry/a2x_registry/register/service.py:L56-L59`
- **CLI 入口**：`a2x-registry` / `a2x-build` / `a2x-register` / 三个 evaluate 命令。
  - 证据: `agent-protocol/AgentRegistry/pyproject.toml:L58-L64`

#### 配置选项

| 配置项名 | 默认值 | 说明 | 证据 |
| --- | --- | --- | --- |
| `HttpConfig::ip` / `port` | 无默认（必填） | A2A 服务监听地址与端口 | `agent-protocol/A2A/cpp-sdk/include/server/http_server_builder.h:L20-L25` |
| `HttpConfig::ioThreadNum` | `1` | A2A I/O 事件循环线程数 | `agent-protocol/A2A/cpp-sdk/include/server/http_server_builder.h:L26` |
| `HttpConfig::endpoint` | `"/jsonrpc"` | A2A JSON-RPC 路径 | `agent-protocol/A2A/cpp-sdk/include/server/http_server_builder.h:L28` |
| `TlsConfig::enabled`（A2A） | `false` | 服务端 TLS 开关（**默认关闭**） | `agent-protocol/A2A/cpp-sdk/src/server/http_server.h:L29` |
| `TlsConfig::verifyPeer`（A2A） | `true` | mTLS 对端校验 | `agent-protocol/A2A/cpp-sdk/src/server/http_server.h:L35` |
| `connectTimeoutMs_` / `readTimeoutMs_` | `10000` / `60000`（毫秒） | 推送通知出站超时 | `agent-protocol/A2A/cpp-sdk/src/transport/http_server_transport.h:L77-L78` |
| `DEFAULT_PROTOCOL_VERSION` | `"1.0"` | A2A 协议版本 | `agent-protocol/A2A/cpp-sdk/src/shared/common_types.h:L45` |
| `DEFAULT_MPSC_QUEUE_SIZE` | `1024` | 内部事件队列容量 | `agent-protocol/A2A/cpp-sdk/src/shared/common_types.h:L47` |
| `HTTP_QUEUE_MAX_BATCH_SIZE` | `64` | 事件循环单次最大批量 | `agent-protocol/A2A/cpp-sdk/src/shared/common_types.h:L48` |
| `HTTP_LISTEN_BACKLOG` | `128` | TCP backlog | `agent-protocol/A2A/cpp-sdk/src/shared/common_types.h:L51` |
| `A2A_BUILD_CLIENT` / `A2A_BUILD_SERVER` | `ON` | 构建客户端/服务端组件 | `agent-protocol/A2A/cpp-sdk/CMakeLists.txt:L8-L9` |
| `A2A_ENABLE_EXAMPLES` / `A2A_ENABLE_TESTS` | `OFF` | 构建示例/单测 | `agent-protocol/A2A/cpp-sdk/CMakeLists.txt:L10-L11` |
| `DEFAULT_SERVER_NAME` / `DEFAULT_CLIENT_NAME` | `"MCP Server"` / `"MCP Client"` | MCP initialize 中的实现名 | `agent-protocol/MCP/cpp-sdk/include/mcp/mcp_type.h:L36-L37` |
| `DEFAULT_VERSION` | `"1.0.0"` | MCP 实现版本 | `agent-protocol/MCP/cpp-sdk/include/mcp/mcp_type.h:L38` |
| `DEFAULT_TIMEOUT` | `30000`（毫秒） | MCP 请求超时 | `agent-protocol/MCP/cpp-sdk/include/mcp/mcp_type.h:L39` |
| `DEFAULT_TOOLS_PAGE_SIZE` / `DEFAULT_RESOURCES_PAGE_SIZE` | `50` | MCP 列表分页大小 | `agent-protocol/MCP/cpp-sdk/include/mcp/mcp_type.h:L40-L41` |
| `StreamableHttpServerConfig::isJsonResponseEnabled` | `false` | 返回 JSON 而非 SSE | `agent-protocol/MCP/cpp-sdk/include/mcp/mcp_type.h:L70` |
| `StreamableHttpServerConfig::stateless` | `false` | 无状态 HTTP 模式 | `agent-protocol/MCP/cpp-sdk/include/mcp/mcp_type.h:L72` |
| `StreamableHttpServerConfig::ioThreads` | `1` | MCP HTTP I/O 线程数 | `agent-protocol/MCP/cpp-sdk/include/mcp/mcp_type.h:L73` |
| `TlsConfig::enabled`（MCP） | `false` | MCP TLS 开关 | `agent-protocol/MCP/cpp-sdk/include/mcp/mcp_type.h:L50` |
| `ServerConfig::workerThreads` | `1` | MCP 工作线程数 | `agent-protocol/MCP/cpp-sdk/include/mcp/mcp_type.h:L111` |
| `MCP_BUILD_CLIENT` / `MCP_WITH_HTTP` | `ON` | 构建 MCP 客户端 / HTTP 传输 | `agent-protocol/MCP/cpp-sdk/CMakeLists.txt:L14-L16` |
| `MCP_ENABLE_STDIO` | `OFF` | 启用 stdio 传输相关构建 | `agent-protocol/MCP/cpp-sdk/CMakeLists.txt:L11` |
| `A2X_REGISTRY_HOME` | `~/.a2x_registry/` | Registry 数据与凭据根目录 | `agent-protocol/AgentRegistry/a2x_registry/common/paths.py:L31-L40` |
| Registry `--host` / `--port` | `"127.0.0.1"` / `8000` | Registry 服务监听 | `agent-protocol/AgentRegistry/a2x_registry/backend/__main__.py:L29-L31` |
| `DEFAULT_RESERVATION_TTL` | `30`（秒） | 预约槽位默认有效期 | `agent-protocol/AgentRegistry/a2x_registry/register/service.py:L61` |

#### 扩展点

- **扩展点 A: A2A 业务执行器（`AgentExecutor`）**
  - 接口定义: `agent-protocol/A2A/cpp-sdk/include/server/agent_executor.h:L19-L52`（纯虚 `Execute` / `Cancel`，可选重载自定义 JSON-RPC 方法）
  - 注入方式: 传入 `HttpServerBuilder::Build(config, card, extCard, agentExecutor, taskStore)`
  - 证据: `agent-protocol/A2A/cpp-sdk/include/server/http_server_builder.h:L49-L51`
- **扩展点 B: A2A 任务存储（`TaskStore`）**
  - 接口定义: `agent-protocol/A2A/cpp-sdk/include/server/task_store.h:L20-L45`
  - 注入方式: `Build()` 第五参数；传 `nullptr` 时回落 `InMemoryTaskStore`
- **扩展点 C: A2A 客户端传输（`ClientTransport`）**
  - 接口定义: `agent-protocol/A2A/cpp-sdk/include/client/client_transport.h:L44-L164`
  - 注入方式: 实现全部纯虚 RPC 方法；默认 `JsonRpcTransportImpl`
- **扩展点 D: A2A 客户端拦截器（`ClientCallInterceptor`）**
  - 接口定义: `agent-protocol/A2A/cpp-sdk/include/client/client_call_interceptor.h:L19-L35`
  - 注入方式: `ClientTransport::AddRequestMiddleware(...)`（`client_transport.h:L163`）
- **扩展点 E: MCP 工具/提示词/资源回调（`ToolFunc` / `RenderPromptFunc` / `ReadResourceFunc`）**
  - 接口定义: `agent-protocol/MCP/cpp-sdk/include/mcp/mcp_server.h:L112-L290`
  - 注入方式: `server->AddTool(name, fn, params)` 等（同步/异步 lambda 均可）
- **扩展点 F: MCP 鉴权链（`AuthProvider` / `TokenVerifier` / `Authenticator` / `Authorizer`）**
  - 接口定义: `agent-protocol/MCP/cpp-sdk/include/mcp/mcp_auth.h:L17-L133`
  - 注入方式: 客户端经工厂传入 `AuthProvider`；服务端经 `StreamableHttpServerConfig` 传入 `authenticator` / `authorizer`（`mcp_type.h:L75-L76`）
- **扩展点 G: MCP 自动补全处理器（`CompleteFunc`）**
  - 接口定义: `agent-protocol/MCP/cpp-sdk/include/mcp/mcp_server.h:L72-L73`
  - 注入方式: `server->AddCompletion(handler)`（`mcp_server.h:L400`）
- **扩展点 H: Registry 服务变更回调**
  - 接口定义: `agent-protocol/AgentRegistry/a2x_registry/register/service.py:L709-L725`
  - 注入方式: `set_on_service_changed(cb)` / `set_on_taxonomy_state_changed(cb)`，默认空实现

#### 关键外部依赖

A2A / MCP C++ SDK 通过 CMake `FetchContent` 拉取第三方库（`agent-protocol/A2A/cpp-sdk/CMakeLists.txt:L1-L85`、`agent-protocol/MCP/cpp-sdk/CMakeLists.txt:L1-L180`）；AgentRegistry 依赖 FastAPI/uvicorn、ChromaDB（向量检索）、LLM SDK（`agent-protocol/AgentRegistry/pyproject.toml:L1-L82`）；Registry 客户端仅依赖 `httpx>=0.24`（`agent-protocol/AgentRegistry/client/pyproject.toml:L1-L39`）。

---

### 2.6 SkillHub

仓库路径: `skillhub/`（`cli/` 命令行 + `marketplace/` FastAPI 后端 + `frontend/` React SPA）

#### 核心功能

- **技能/插件打包规范**：`skill` / `swarmskill` 以 `SKILL.md` + YAML frontmatter 描述；`tools` / `mcp-stdio` / `restful-api` 以 `plugin.yaml` 描述。
  - 证据: `skillhub/cli/cli_core/plugin.py:L198-L250`、`skillhub/marketplace/plugins_market/validation/constants.py:L69-L123`
- **发布流程**：CLI 打 zip → SHA-256 校验和 → multipart `POST /api/v1/plugins`（携带 `X-Checksum-SHA256`）。
  - 证据: `skillhub/cli/cli_core/handlers.py:L179-L260`、`skillhub/marketplace/plugins_market/routers/plugin.py:L549-L576`
- **安装流程**：取预签名 S3 下载地址 + 期望校验和 → 流式下载 → 校验 SHA-256 与 ZIP 魔数 → 解压。
  - 证据: `skillhub/cli/cli_core/market.py:L457-L573`、`skillhub/marketplace/plugins_market/routers/plugin.py:L1110-L1130`
- **检索/列表/详情**：分页 + 关键词 + 类型 + 作者 + 排序字段过滤。
  - 证据: `skillhub/marketplace/plugins_market/routers/plugin.py:L1076-L1087`、`skillhub/cli/cli_core/schemas/plugin.py:L180-L192`
- **版本规范**：仅接受 semver `x.y.z` 或 7 位小写十六进制 commit SHA，禁止 `v` 前缀，CLI 与服务端双向校验。
  - 证据: `skillhub/cli/cli_core/schemas/plugin.py:L13-L88`、`skillhub/marketplace/plugins_market/validation/constants.py:L27-L63`
- **自动化技能评审流水线**：4 个确定性引擎（system / skill_facet / behavior_facts / rule）+ 1 个 LLM 语义引擎。
  - 证据: `skillhub/marketplace/skill_review/engines/registry.py:L11-L15`
- **批量导入（skill-import）**：管理员用系统令牌批量上传技能包（限流）。
  - 证据: `skillhub/marketplace/plugins_market/routers/plugin.py:L715-L730`、`skillhub/cli/cli_core/handlers.py:L430-L503`
- **Git 源导入**：登记仓库 URL + ref，服务端调用 `git` 同步技能，按用户滑动窗口限流。
  - 证据: `skillhub/marketplace/plugins_market/routers/plugin.py:L890-L1076`、`L234-L258`
- **混合语义检索**：BM25 + 向量 + 可选 LLM 树状渐进检索，启动时预热索引。
  - 证据: `skillhub/marketplace/main.py:L63-L87`、`L140-L160`
- **Playground 在线试跑**：反向代理到独立的 `skill-runner` K8s Service，剥离并重注入客户端执行字段以防绕过审核，按用户日配额限流。
  - 证据: `skillhub/marketplace/plugins_market/routers/playground_proxy.py:L106-L141`
- **双鉴权路径**：用户 Token（回源 GitCode / GitHub `/user` 校验）与 `X-System-Token`（HMAC 比对），二者互斥。
  - 证据: `skillhub/cli/cli_core/handlers.py:L80-L100`、`skillhub/marketplace/plugins_market/routers/plugin.py:L261-L284`
- **个性化推荐（可选）**：Milvus 索引 + Redis 行为历史 + MMR 多样性重排。
  - 证据: `skillhub/marketplace/plugins_market/routers/register.py:L27-L30`
- **人工审核工作流**：自动评审后由管理员终审，驱动 `publish_result` 状态。
  - 证据: `skillhub/marketplace/plugins_market/routers/plugin.py:L1244-L1290`、`L115-L117`
- **openJiuwen 生态仓库观测**：硬编码 10 个兄弟仓库名用于 star/watch 统计。
  - 证据: `skillhub/marketplace/plugins_market/routers/github_watch.py:L56-L67`

#### 配置选项

| 配置项名 | 默认值 | 说明 | 证据 |
| --- | --- | --- | --- |
| `STORE_HOST` / `STORE_PORT` | `127.0.0.1` / `8100` | 后端监听地址与端口 | `skillhub/.env.example:L12-L13` |
| `MARKET_DEBUG` | `false` | 开发模式（uvicorn reload） | `skillhub/.env.example:L16` |
| `DB_TYPE` | `mysql` | 仅支持 MySQL | `skillhub/.env.example:L29` |
| `DB_HOST` / `DB_PORT` | `localhost` / `3306` | MySQL 连接 | `skillhub/.env.example:L30-L31` |
| `STORE_DB_NAME` | `openjiuwen_market` | 数据库名 | `skillhub/.env.example:L35` |
| `REDIS_HOST` | `""`（空即禁用 Redis） | Redis 主机 | `skillhub/.env.example:L40` |
| `REDIS_PORT` | `6379` | Redis 端口 | `skillhub/.env.example:L41` |
| `AUTH_USER_API_URL` | `https://gitcode.com/api/v5/user` | 用户 Token 校验回源地址 | `skillhub/.env.example:L52` |
| `SYSTEM_ADMIN_TOKEN` | `""` | 系统级令牌，为空表示未启用 | `skillhub/.env.example:L55` |
| `SYSTEM_ADMIN_USER` | `system_admin` | 系统令牌操作时注入的用户名 | `skillhub/.env.example:L57` |
| `MARKET_GITCODE_OAUTH_ENABLED` | `false` | GitCode OAuth 登录开关 | `skillhub/.env.example:L67` |
| `MARKET_GITHUB_OAUTH_ENABLED` | `false` | GitHub OAuth 登录开关 | `skillhub/.env.example:L77` |
| `MARKET_GITHUB_STAR_ENABLED` | `false` | 一键 Star 功能开关 | `skillhub/.env.example:L83` |
| `MARKET_OAUTH_FRONTEND_ORIGIN` | `http://127.0.0.1:9002` | OAuth 回跳前端源 | `skillhub/.env.example:L85` |
| `STORAGE_TYPE` | `MinIO` | 对象存储类型（MinIO / OBS） | `skillhub/.env.example:L92` |
| `MARKET_BUCKET_NAME` | `openjiuwen-market-test` | 技能包存储桶 | `skillhub/.env.example:L93` |
| `MARKET_S3_ENDPOINT` | `http://localhost:9000` | S3/MinIO 端点 | `skillhub/.env.example:L94` |
| `SERVER_AES_MASTER_KEY` | `""` | 服务端密文根密钥（Base64 32 字节） | `skillhub/.env.example:L131` |
| `HUAWEICLOUD_KMS_ENABLED` | `False` | 华为云 KMS 托管开关 | `skillhub/.env.example:L135` |
| `MARKET_RETRIEVAL_EMBEDDING_BATCH_SIZE` | `16` | 向量化批大小 | `skillhub/.env.example:L162` |
| `MARKET_RETRIEVAL_BUILD_METHOD` | 注释态默认 `embedding_bm25` | 离线索引构建策略（bm25/embedding/embedding_bm25/all） | `skillhub/.env.example:L183-L187` |
| `MARKET_RETRIEVAL_SEARCH_METHOD` | 注释态默认 `embedding` | 在线检索策略（bm25/embedding/auto/progressive） | `skillhub/.env.example:L189-L195` |
| `MARKET_SKILL_REVIEW_ENABLED` | `false` | 自动化技能评审开关 | `skillhub/.env.example:L217` |
| `FRONTEND_PORT` | `9002` | 前端端口 | `skillhub/.env.example:L230` |
| `BACKEND_URL` / `BACKEND_PORT` | `127.0.0.1` / `8100` | Nginx 反代后端地址 | `skillhub/.env.example:L239-L240` |
| `PLAYGROUND_ENABLED` | `false` | 在线试跑开关（仅 K8s 环境） | `skillhub/.env.example:L252` |
| `SKILL_RUNNER_URL` | `http://skill-runner.skillhub-system.svc.cluster.local:8900` | skill-runner 服务地址 | `skillhub/.env.example:L254` |
| `PLAYGROUND_DAILY_LIMIT` | `20` | 每用户每日试跑次数上限 | `skillhub/.env.example:L257` |
| `PLAYGROUND_MULTI_INSTANCE` | `false` | 多副本时改用 Redis 存会话 | `skillhub/.env.example:L262` |
| `MARKET_RECOMMENDER_ENABLED` | `false` | 个性化推荐开关 | `skillhub/.env.example:L276` |
| `MARKET_REC_MMR_LAMBDA` | `0.5` | MMR 相关性/多样性权重 | `skillhub/.env.example:L284` |
| `OPENJIUWEN_MARKET_URL` | 见代码 | CLI 默认市场地址 | `skillhub/cli/cli_core/handlers.py:L68` |
| `OPENJIUWEN_USER_TOKEN` / `OPENJIUWEN_SYSTEM_TOKEN` | 无 | CLI 默认凭据来源 | `skillhub/cli/cli_core/handlers.py:L81-L82` |

#### 扩展点

- **扩展点 A: 评审引擎（`ReviewEngine` 冻结 dataclass）**
  - 接口定义: `skillhub/marketplace/skill_review/engines/types.py:L37-L48`（`run: Callable[[ReviewEngineContext], ReviewEngineResult]`）
  - 注入方式: 构造 `ReviewEngine(...)` 后加入 `create_default_review_engine_registry()` 的 `deterministic_engines` / `semantic_engines` 列表；**无动态加载**，注册表仅在启动时实例化一次
  - 证据: `skillhub/marketplace/skill_review/engines/registry.py:L11-L15`
- **扩展点 B: 检索 LLM 客户端（`ProgressiveLLMClient` ABC）**
  - 接口定义: `skillhub/marketplace/dispatch/retrieval/llm/base/protocols.py:L16-L80`
  - 注入方式: 子类实例传入 `BuildConfig(llm_openai_client=...)` / `IndexManager.configure(...)`
  - 证据: `skillhub/marketplace/main.py:L190-L195`
- **扩展点 C: 技能包访问器（`PackageAccess`）**
  - 接口定义: `skillhub/marketplace/skill_review/runtime/package_access/base.py:L1-L28`
  - 注入方式: 子类实例放入 `ReviewEngineContext`（`skillhub/marketplace/skill_review/engines/types.py:L17`）；内置 `ZipPackageAccess` 与 `FileCatalogAccess`
- **扩展点 D: CLI 子命令注册表（`COMMAND_HANDLERS`）**
  - 接口定义: `skillhub/cli/cli_core/handlers.py:L506-L516`
  - 注入方式: 在 `parsers.py` 增加子解析器 + 在 `handlers.py` 增加 `handle_X` + 在字典中登记
  - 证据: `skillhub/cli/openjiuwen_plugin/parsers.py:L255-L267`
- **扩展点 E: FastAPI 路由注册（`router_register`）**
  - 接口定义: `skillhub/marketplace/plugins_market/routers/register.py:L17-L48`
  - 注入方式: 新建 `APIRouter` 后在该函数内 `app.include_router(...)`；recommender / playground / clawhub 兼容路由按开关条件注册

#### 关键外部依赖

后端：FastAPI、SQLAlchemy + MySQL、Redis、boto3/MinIO（对象存储）、Milvus（推荐）、OpenAI 兼容 embedding/LLM API（`skillhub/marketplace/pyproject.toml:L10-L35`）；CLI 仅依赖轻量 HTTP/YAML 栈（`skillhub/cli/openjiuwen_plugin/pyproject.toml:L11-L16`）；检索/派发 SDK 独立打包（`skillhub/marketplace/dispatch/pyproject.toml:L11-L13`、`skillhub/marketplace/retrieval/pyproject.toml:L11-L18`）。

---

### 2.7 Agent Tools

仓库路径: `agent-tools/`（`packages/` 可安装 Python 包 + `dev_tools_suite/` 开发者工具 + `reward_tool/` + 竞赛提交目录）

#### 核心功能

- **OpenAI 兼容推理路由（infer_router）**：FastAPI 网关暴露 `/v1/chat/completions`、`/v1/completions`，向后端 vLLM/SGLang worker 转发，支持 SSE 流式与非流式。
  - 证据: `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/api/server.py:L1-L145`
- **`jiuwenext` 请求扩展（AgentHints / CacheControl）**：请求可携带 priority、预估输出 token、下一轮 prefill 提示、prefix_id、缓存 TTL，用于驱动调度与路由。
  - 证据: `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/schemas/agent_hints.py:L7-L62`、`agent-tools/packages/infer_router/src/openjiuwentools/infer_router/preprocess/preprocessor.py:L13-L60`
- **KV Cache 管理器**：按 worker 跟踪缓存块，支持 LRU 老化、衰减因子、TTL、会话亲和映射，以及可选 radix-tree 前缀匹配；同时兼容 `VLLM` 与 `SGLANG` 两种引擎事件。
  - 证据: `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/kv_cache/kv_cache.py:L1-L60`
- **Worker 服务发现（双实现）**：配置文件发现与 etcd v2 HTTP API 发现（可选 watch / basic auth）。
  - 证据: `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/discovery/config_discovery.py:L12-L130`、`agent-tools/packages/infer_router/src/openjiuwentools/infer_router/discovery/etcd_discovery.py:L15-L170`
- **负载均衡**：内置 `round_robin` 与 `weighted`（结合 KV 缓存与负载）两种算法，支持分离式 prefill/decode worker 配对选择。
  - 证据: `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/routing/router.py:L16-L199`
- **熔断与重试**：`retry_async()` 支持最大尝试次数、抖动与熔断器联动。
  - 证据: `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/fault_tolerance/fault_tolerance.py:L32-L60`
- **Prometheus 指标**：请求量/耗时、按 worker 与 model 的路由量、队列长度、KV 命中/未命中、缓存块数、AgentHints 使用率、优先级分布等。
  - 证据: `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/monitoring/metrics.py:L1-L50`
- **可选 API Key 鉴权中间件**：接受 `X-API-Key` 或 `Authorization: Bearer`，`/health` 免鉴权，默认关闭。
  - 证据: `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/api/auth.py:L11-L58`
- **vLLM KV 亲和 Monkey-Patch 插件**：`apply_patches()` 在 import 期替换 14 个 vLLM 子系统（scheduler、block pool、KV cache manager/coordinator、engine core、OpenAI serving 等），提供 4 个 vLLM 版本分支（v0.13.0 / v0.17.0 / v0.18.0 / v0.21.0）。
  - 证据: `agent-tools/packages/openJiuwen-vllm-affinity/v0.21.0/jiuwen_vllm_affinity/kv_cache_plugin/patcher.py:L41-L55`
- **`jiuwen-infer-worker` CLI**：把 vLLM 引擎包装为 JiuWen worker，支持 YAML + CLI 覆盖、`aggregated`/`prefill`/`decode` 模式、etcd 注册、ZMQ KV 事件中继。
  - 证据: `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/vllm/args.py:L1-L52`
- **LLM Trace 日志分析器（`trace-llm-report`）**：解析 `[LLM_IO_TRACE]` 结构化日志，还原 LLM 轮次与工具调用间隙，输出 HTML 性能时间线；零运行时依赖。
  - 证据: `agent-tools/dev_tools_suite/log_parse/src/trace_log_parse/parser.py:L12-L269`、`agent-tools/dev_tools_suite/log_parse/pyproject.toml:L6`
- **诊断技能包 `relayclaw-jiuwen-log-diagnosis`**：以 `SKILL.md` + `cases/` + `evals/` + `evolutions/` + `references/` 组织的 Agent 技能（非 Python 库），供 Agent 平台按元数据加载。
  - 证据: `agent-tools/dev_tools_suite/skills/relayclaw-jiuwen-log-diagnosis/SKILL.md:L1-L3`

#### 配置选项

infer_router 的全部运行时配置集中于一个 pydantic-settings `BaseSettings` 类，优先级为 环境变量 > YAML 文件 > 默认值（`agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L53-L130`）。

| 配置项名 | 默认值 | 说明 | 证据 |
| --- | --- | --- | --- |
| `host` / `port` | `0.0.0.0` / `8000` | 路由服务监听地址与端口 | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L57-L58` |
| `log_level` | `info` | 日志级别 | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L59` |
| `worker_discovery_interval` | `30` | worker 重发现间隔（秒） | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L62` |
| `worker_health_check_interval` | `30` | 健康检查间隔（秒） | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L63` |
| `worker_health_check_timeout` | `10` | 单次健康检查超时（秒） | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L64` |
| `worker_health_check_max_failures` | `3` | 连续失败阈值 | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L65` |
| `request_forward_timeout` | `120` | 转发请求超时（秒） | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L66` |
| `worker_discovery_type` | `config` | 发现后端：`config` 或 `etcd` | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L69` |
| `worker_config_path` | `workers.json` | 静态 worker 配置文件路径 | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L70` |
| `etcd_hosts` / `etcd_port` | `["localhost"]` / `2379` | etcd 连接 | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L73-L74` |
| `etcd_prefix` | `/jiuwen/workers` | worker 注册键前缀 | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L75` |
| `etcd_user` / `etcd_password` | `None` | etcd 凭据（可选） | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L76-L77` |
| `etcd_enable_watch` | `False` | 实时 watch（否则轮询） | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L78` |
| `default_scheduling_strategy` | `FCFS` | 默认调度策略 | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L81` |
| `kv_cache_max_blocks` | `1000` | 跟踪的最大缓存块数 | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L84` |
| `kv_cache_aging_block_factor` | `0.3` | 参与老化淘汰的块比例 | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L85` |
| `kv_cache_decay_factor` | `0.9` | 复用得分衰减因子 | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L86` |
| `kv_cache_block_size` | `16` | 每块 token 数 | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L87` |
| `kv_cache_enable_session_affinity` | `True` | 同会话粘住同一 worker | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L88` |
| `kv_cache_enable_radix_tree` | `False` | Radix Tree 前缀匹配（SGLang） | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L89` |
| `kv_event_mode` | `inner_event` | KV 事件来源：`inner_event` / `worker_event` | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L92` |
| `api_key` | `None` | 鉴权密钥（`enable_auth=True` 时必填） | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L98` |
| `enable_auth` | `False` | 是否开启请求鉴权中间件 | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L99` |
| `enable_metrics` / `metrics_port` | `True` / `8001` | Prometheus 指标开关与端口 | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L102-L103` |
| `load_balancing_algorithm` | `weighted` | 生效的负载均衡算法名 | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L106` |
| `retry_attempts` / `retry_delay` | `3` / `0.5` | 重试次数与基础退避 | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L109-L110` |
| `http_pool_connections` | `500` | httpx 连接池大小 | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L113` |
| `max_concurrent_requests` | `1000` | 并发在途请求信号量 | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L121` |
| `tokenizer_load_from_file` / `tokenizer_local_dir` | `False` / `None` | 从本地目录加载 tokenizer | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L124-L125` |
| `CONFIG_PATH`（环境变量） | `config.yaml` | YAML 配置文件路径 | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/config/config.py:L20` |
| `KV_TARGET`（环境变量） | 无 | 覆盖 P2P 分离式连接器的 `X-KV-Target` 头 | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/api/server.py:L65-L69` |
| `--worker-mode` | `aggregated` | worker 模式：`aggregated`/`prefill`/`decode` | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/vllm/args.py:L40-L43` |
| `--request-plane` | `http` | 请求平面：`http` / `tcp` | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/vllm/args.py:L31-L32` |
| `--kv-relay-endpoint` | 见代码 | KV 事件中继的 ZMQ PUB 地址 | `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/vllm/args.py:L38-L39` |

#### 扩展点

- **扩展点 A: `WorkerDiscovery` 抽象基类（新增服务发现后端）**
  - 接口定义: `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/discovery/base.py:L8-L29`（`discover()` / `start()` / `stop()`）
  - 注入方式: 子类返回 `list[WorkerInfo]`，并在服务端工厂处按 `settings.worker_discovery_type` 分支实例化
  - 证据: `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/api/server.py:L1283-L1330`
- **扩展点 B: `LoadBalancingAlgorithm` 基类（新增负载均衡算法）**
  - 接口定义: `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/routing/load_balance.py:L64-L82`（`select_worker` / `select_worker_pair`）
  - 注入方式: 在 `Router.__init__` 的 `self.algorithms` 字典登记名称，再由 `settings.load_balancing_algorithm` 选中
  - 证据: `agent-tools/packages/infer_router/src/openjiuwentools/infer_router/routing/router.py:L23-L29`
- **扩展点 C: `openjiuwentools.components` 入口点组**
  - 接口定义: `agent-tools/packages/infer_router/pyproject.toml:L53-L54`
  - 注入方式: 第三方包通过 setuptools entry-point 发布到该组，由 `importlib.metadata.entry_points(group="openjiuwentools.components")` 发现
- **扩展点 D: vLLM 插件注册钩子**
  - 接口定义: `agent-tools/packages/openJiuwen-vllm-affinity/v0.21.0/jiuwen_vllm_affinity/kv_cache_plugin/plugin.py:L1-L7`（`register()`）
  - 注入方式: 新增 `register_<subsystem>()` 并在 `apply_patches()` 中调用
  - 证据: `agent-tools/packages/openJiuwen-vllm-affinity/v0.21.0/jiuwen_vllm_affinity/kv_cache_plugin/patcher.py:L41-L55`
- **扩展点 E: `@tool` 装饰器（来自 agent-core，本仓库仅为消费方）**
  - 注入方式: `from openjiuwen.core.utils.tool.tool import tool` + `from openjiuwen.core.utils.tool.param import Param`，装饰普通函数即成为 Agent 可调用工具
  - 证据: `agent-tools/Agent Innovation Challenge/比赛提交（Competition Submission）/AutoCursor队 - Computer Use Tool/core/autoCursor_Tools.py:L1-L21`

#### 关键外部依赖

infer_router：FastAPI / uvicorn / pydantic(-settings) / httpx / loguru / prometheus-client / pyyaml / transformers / tokenizers / orjson，可选 extras 含 pyzmq + msgspec（ZMQ KV 事件）与 etcd3（`agent-tools/packages/infer_router/pyproject.toml:L24-L51`）；`trace-log-parse` 声明 `dependencies = []`，纯标准库实现（`agent-tools/dev_tools_suite/log_parse/pyproject.toml:L6`）；vllm-affinity 插件直接依赖被 patch 的 vLLM 版本本身。

---

### 2.8 JiuwenSwarm

仓库路径: `jiuwenswarm/`（主包 `jiuwenswarm/jiuwenswarm/` + 沙箱子包 `jiuwenswarm/jiuwenbox/`）

版本 `0.2.4.beta4`（`jiuwenswarm/pyproject.toml:L7`），共 13 个 console_scripts 入口（`jiuwenswarm/pyproject.toml:L118-L131`），其中 `jiuwenswarm-agentserver` → `jiuwenswarm.server.app_agentserver:main`、`jiuwenswarm-gateway` → `jiuwenswarm.gateway.app_gateway:main`。

#### 核心功能

- **多 Agent 团队编排（TeamManager）**：会话级团队生命周期、事件广播、等待队列、cron 完成回调、团队演化监听；WebSocket 侧派发 `team.*` 系列方法。
  - 证据: `jiuwenswarm/jiuwenswarm/agents/harness/team/team_manager.py:L269-L500`、`jiuwenswarm/jiuwenswarm/server/agent_ws_server.py:L1506-L1537`
- **分布式团队角色**：`teammate` / `teamleader` 两种角色，远端成员在服务启动时由 bootstrap 守护协程注册。
  - 证据: `jiuwenswarm/jiuwenswarm/resources/config.yaml:L582-L583`、`jiuwenswarm/jiuwenswarm/server/app_agentserver.py:L196-L208`
- **WebSocket 协议层（AgentWebSocketServer）**：E2AEnvelope/E2AResponse JSON 线格式，内部链路 8 MiB / Web 链路 100 MiB 上限，`connection.ack` 握手帧。
  - 证据: `jiuwenswarm/jiuwenswarm/server/agent_ws_server.py:L1330-L1331`、`jiuwenswarm/jiuwenswarm/common/ws_limits.py:L1-L11`
- **完整 `ReqMethod` 方法枚举**：涵盖 `initialize`、`chat.*`、`session.*`、`team.*`、`command.*`、`history.*`、`agents.*`、`skills.*`、`files.*`、`schedule.*`、`acp.tool_response`、`extensions.*`、`harness.packages.*` 等全部线上方法名。
  - 证据: `jiuwenswarm/jiuwenswarm/common/schema/message.py:L10-L130`
- **ACP（Agent Client Protocol）支持**：`AcpChannel` + `AcpGatewayBridge` 以 JSON-RPC 2.0 over stdio 实现会话列举/新建/提示结果/会话增量更新。
  - 证据: `jiuwenswarm/jiuwenswarm/gateway/channel_manager/protocol/acp/acp_connect.py:L122-L666`、`L790-L800`
- **MCP 客户端集成**：配置驱动的 `mcp.servers` 列表（`stdio`/`sse`/`http`/`streamable-http` 四种传输），支持运行时增删启停与预检探测。
  - 证据: `jiuwenswarm/jiuwenswarm/common/mcp_config.py:L43-L120`、`jiuwenswarm/jiuwenswarm/server/agent_ws_server.py:L5833-L6197`
- **Playwright 浏览器 MCP 运行时**：内置浏览器自动化 MCP Server，默认 `streamable-http` 接入并可自动拉起。
  - 证据: `jiuwenswarm/jiuwenswarm/resources/.env.template:L65-L74`
- **多层沙箱（jiuwenbox）**：Landlock LSM 文件访问控制 + Seccomp BPF 系统调用过滤 + bubblewrap 命名空间 + cgroup 资源限额 + 网络隔离，并提供沙箱管理 REST 服务与空闲/僵尸回收。
  - 证据: `jiuwenswarm/jiuwenbox/src/jiuwenbox/supervisor/landlock.py:L25-L88`、`jiuwenswarm/jiuwenbox/src/jiuwenbox/supervisor/seccomp.py:L274-L336`、`jiuwenswarm/jiuwenbox/src/jiuwenbox/server/sandbox_manager.py:L135-L650`
- **会话与检查点持久化**：复用 agent-core 的 `CheckpointerFactory`，单机 `shelve`/`sqlite`/`in_memory`，分布式 `redis` + Elasticsearch；支持会话回溯（rewind / rewind_and_restore / rewind_compact / rewind_context）。
  - 证据: `jiuwenswarm/jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:L42`、`jiuwenswarm/jiuwenswarm/server/agent_ws_server.py:L1494-L1504`
- **Code Mode（编码模式）**：模式切换 rail 拦截工具调用，配套 code-todo 工具族、计划审批 rail 与计划中断 rail。
  - 证据: `jiuwenswarm/jiuwenswarm/agents/harness/code/rails/code_agent_mode_rail.py:L105-L160`、`jiuwenswarm/jiuwenswarm/agents/harness/code/tools/code_todo_tools.py:L42-L115`
- **模型路由与多 Provider 配置**：`models.defaults` 列表描述多套 client/request 配置，支持运行时 `list/switch/add` 动态切换。
  - 证据: `jiuwenswarm/jiuwenswarm/resources/config.yaml:L235-L245`、`jiuwenswarm/jiuwenswarm/server/agent_ws_server.py:L5501-L5617`
- **分级权限与审批流**：`permission_mode: normal|strict` + 按工具粒度的 `allow`/`ask`/`deny` 规则 + 熔断 rail + 破坏性 shell 操作前置确认。
  - 证据: `jiuwenswarm/jiuwenswarm/resources/config.yaml:L895-L940`、`jiuwenswarm/jiuwenswarm/agents/harness/common/rails/permissions/owner_scopes.py:L36-L100`
- **子 Agent 派生与可观测性**：`TaskTool` 派生子 Agent，启动时安装调试补丁与 OTel span 包装钩子；子 Agent 以 YAML AgentCard 定义并可动态增删改。
  - 证据: `jiuwenswarm/jiuwenswarm/server/app_agentserver.py:L143-L156`、`jiuwenswarm/jiuwenswarm/server/agent_ws_server.py:L1684-L1700`
- **流式事件管线**：流处理主循环 + 每轮心跳，事件经 `JiuSwarmStreamEventRail` 富化后推送；ACP 侧独立发送 `acp.session_update`/`acp.usage_update`/`acp.final_text`。
  - 证据: `jiuwenswarm/jiuwenswarm/server/agent_ws_server.py:L2620-L2813`、`jiuwenswarm/jiuwenswarm/agents/harness/common/rails/stream_event_rail.py:L221-L260`

#### 配置选项

主配置文件为 `jiuwenswarm/jiuwenswarm/resources/config.yaml`（1359 行，首次运行复制到 `~/.jiuwenswarm/config/config.yaml`），大量值支持 `${ENV:-default}` 插值。

| 配置项名 | 默认值 | 说明 | 证据 |
| --- | --- | --- | --- |
| `preferred_language` | `zh` | 前端显示语言（zh/en） | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L2` |
| `setup_guide.enabled` | `true` | 首次运行模型配置引导 | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L5-L6` |
| `auto_recap.enabled` | `true` | 空闲后自动生成会话摘要 | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L9-L10` |
| `a2ui.enabled` | `false` | A2UI Agent SDK 集成开关 | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L12-L13` |
| `symphony.enabled` | `false` | Symphony 技能图编排引擎开关 | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L19-L20` |
| `symphony.evolution.enabled` | `false` | 从会话轨迹生成动态技能图 overlay | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L40-L41` |
| `symphony.skill_retrieval.enabled` | `false` | 语义技能检索索引 | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L51-L52` |
| `logging.level` | `INFO` | 全局日志级别 | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L81-L82` |
| `memory.mode` | `${MEMORY_MODE:-local}` | 内置记忆存储位置：local / cloud | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L102` |
| `memory.engine` | `${MEMORY_ENGINE:-builtin}` | 记忆引擎：builtin / external / both / none | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L108` |
| `memory.jiuwen.mode` | `${JIUWEN_MEMORY_MODE:-server}` | 接入 agent-memory 的方式：server（HTTP）/ sdk（进程内） | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L197-L199` |
| `memory.jiuwen.server.base_url` | `${JIUWEN_MEMORY_BASE_URL:-http://127.0.0.1:8137}` | agent-memory 服务地址 | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L205-L206` |
| `models.defaults[].model_client_config` | `${API_BASE}` / `${API_KEY}` / `${MODEL_NAME}` / `${MODEL_PROVIDER}` | 主模型连接参数（全部走环境变量） | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L235-L245`、`jiuwenswarm/jiuwenswarm/common/config.py:L1192-L1195` |
| `models.defaults[].model_client_config.timeout` | `360` | 单次模型 HTTP 请求超时（秒） | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L242-L243` |
| `models.defaults[].model_client_config.stream_first_chunk_timeout` | `300` | 流式首包等待上限（秒） | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L244-L245` |
| `MODEL_ALIAS`（环境变量） | `""` | 模型展示别名 | `jiuwenswarm/jiuwenswarm/common/config.py:L1189` |
| `permissions.enabled` | `false` | 分级权限引擎总开关 | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L895-L896` |
| `permissions.permission_mode` | `normal` | severity 映射模式：normal / strict | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L898` |
| `permissions.defaults."*"` | `allow` | 未显式配置工具的兜底策略 | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L900-L901` |
| `permissions.tools.*` | `bash: ask`、`write: allow` 等 | 按工具粒度的审批级别 | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L903-L940` |
| `mcp.servers` | `[]` | MCP Server 列表 | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L1155-L1156` |
| `modes.team.jiuwen_team.enable_swarmflow` | `false` | 多 Agent 轮间通信（SwarmFlow）开关 | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L1222` |
| `modes.team.jiuwen_team.swarmflow_budget` | 注释态（未设置＝不限） | SwarmFlow 团队级 token 预算上限 | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L1226-L1227` |
| `team.role` | `teammate` | 分布式团队角色：teammate / teamleader | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L582-L583` |
| `agent_client.type` | `websocket` | Gateway→AgentServer 通道：websocket / yuanrong / agentos_router | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L624-L627` |
| `JIUWEN_KV_URL`（环境变量） | `redis://localhost:6379/0` | 分布式模式 KV 存储 | `jiuwenswarm/jiuwenswarm/resources/config.yaml:L220` |
| `JIUWENSWARM_HOME`（环境变量） | `Path.home()` | 覆盖用户主目录 | `jiuwenswarm/jiuwenswarm/common/utils.py:L364-L370` |
| `JIUWENSWARM_DATA_DIR`（环境变量） | `~/.jiuwenswarm` | 覆盖数据/工作区目录（多实例隔离） | `jiuwenswarm/jiuwenswarm/common/utils.py:L402-L412` |
| `JIUWENSWARM_CONFIG_DIR`（环境变量） | 未设置 | 覆盖配置目录 | `jiuwenswarm/jiuwenswarm/common/config.py:L39` |
| `AGENT_SERVER_HOST`（环境变量） | `127.0.0.1` | AgentServer 绑定地址 | `jiuwenswarm/jiuwenswarm/server/app_agentserver.py:L311` |
| `AGENT_SERVER_PORT` / `AGENT_PORT`（环境变量） | `18092` | AgentServer WebSocket 端口 | `jiuwenswarm/jiuwenswarm/server/app_agentserver.py:L291`、`L314-L320` |
| `GATEWAY_HOST` / `GATEWAY_PORT`（环境变量） | `127.0.0.1` / `19001` | Gateway 绑定地址与端口 | `jiuwenswarm/jiuwenswarm/gateway/app_gateway.py:L1977-L1978` |
| `WEB_PORT`（环境变量） | `19000` | Web 通道端口 | `jiuwenswarm/jiuwenswarm/gateway/app_gateway.py:L2974` |
| `MODEL_PROVIDER`（环境变量） | `OpenAI` | LLM Provider 类型 | `jiuwenswarm/jiuwenswarm/resources/.env.template:L5` |
| `FREE_SEARCH_SSL_VERIFY`（环境变量） | `false` | 免费搜索是否校验 TLS | `jiuwenswarm/jiuwenswarm/resources/.env.template:L58` |
| `BROWSER_RUNTIME_MCP_ENABLED`（环境变量） | `1` | 浏览器 MCP 运行时开关 | `jiuwenswarm/jiuwenswarm/resources/.env.template:L65` |
| `BROWSER_RUNTIME_MCP_CLIENT_TYPE`（环境变量） | `streamable-http` | 浏览器 MCP 传输方式 | `jiuwenswarm/jiuwenswarm/resources/.env.template:L68` |
| `BROWSER_RUNTIME_MCP_SERVER_PATH`（环境变量） | `http://127.0.0.1:8940/mcp` | 浏览器 MCP 端点 | `jiuwenswarm/jiuwenswarm/resources/.env.template:L74` |
| `extensions.extension_dirs` | 包内 `jiuwenswarm/extensions` | 扩展搜索路径（分号分隔） | `jiuwenswarm/jiuwenswarm/extensions/manager.py:L28-L40` |

#### 扩展点

- **扩展点 A: `BaseExtension` 扩展包 ABC**
  - 接口定义: `jiuwenswarm/jiuwenswarm/extensions/sdk/base.py:L15-L36`（抽象方法 `initialize(config)` / `shutdown()`）
  - 注入方式: 在 `extensions.extension_dirs` 下建目录，放 `extension.yaml` 清单 + `BaseExtension` 子类（可选自带 `config.yaml`）；`ExtensionLoader.discover_extension_roots()` 扫描并动态 import 实例化，服务启动时由 `ExtensionManager.load_all_extensions()` 统一加载
  - 证据: `jiuwenswarm/jiuwenswarm/extensions/loader.py:L43-L80`、`jiuwenswarm/jiuwenswarm/server/app_agentserver.py:L175-L178`
- **扩展点 B: `ExtensionRegistry` 注册分发**
  - 接口定义: `jiuwenswarm/jiuwenswarm/extensions/registry.py:L55-L65`（`register_agent_server_client` / `register_crypto_utility` / `register_third_agent`）
  - 注入方式: 自定义 `AgentServerClient` 可替换 Gateway↔AgentServer 通信路径；`ThirdAgentExtension` 注册第三方 Agent 后端
  - 证据: `jiuwenswarm/jiuwenswarm/extensions/registry.py:L17-L29`
- **扩展点 C: `BaseChannel` 通道 ABC（IM / 协议接入）**
  - 接口定义: `jiuwenswarm/jiuwenswarm/gateway/channel_manager/base.py:L116-L165`（`start()` / `stop()` / `send()`）
  - 注入方式: 子类化后注册到 `RobotMessageRouter`；现有实现含 Web / TUI / Desktop / ACP / A2A 及飞书、钉钉、Slack、Discord、Telegram、企业微信、WhatsApp 等
  - 证据: `jiuwenswarm/jiuwenswarm/gateway/channel_manager/base.py:L50-L60`
- **扩展点 D: `RailManager` 运行时 Rail 热插拔**
  - 接口定义: `jiuwenswarm/jiuwenswarm/agents/harness/common/plugins/rail_manager.py:L57-L130`
  - 注入方式: 在 `~/.jiuwenswarm/agent/workspace/extensions/<name>/rail.py` 放置 `DeepAgentRail` 子类（类名/优先级/启用态写入 `extensions_config.json`），由 `harness.packages.activate` / `deactivate` 触发热加载
  - 证据: `jiuwenswarm/jiuwenswarm/agents/harness/common/plugins/rail_manager.py:L79-L82`、`jiuwenswarm/jiuwenswarm/server/agent_ws_server.py:L1629-L1635`
- **扩展点 E: MCP Server 配置式工具注册**
  - 接口定义: `jiuwenswarm/jiuwenswarm/common/mcp_config.py:L43-L120`
  - 注入方式: 向 `mcp.servers[]` 追加 `name` + `transport` + `command`/`url`；亦可通过 `command.mcp` 的 `add`/`remove` 免重启生效
  - 证据: `jiuwenswarm/jiuwenswarm/server/agent_ws_server.py:L5833-L5860`
- **扩展点 F: Hooks / 回调框架**
  - 接口定义: `jiuwenswarm/jiuwenswarm/server/agent_ws_server.py:L1620-L1625`（`hooks.list`）
  - 注入方式: 复用 agent-core 的 `AsyncCallbackFramework`，由 `ExtensionRegistry` 下发给扩展；`before_chat_request` 等钩子在请求路径上触发
  - 证据: `jiuwenswarm/jiuwenswarm/server/agent_ws_server.py:L1882-L1890`

#### 关键外部依赖

核心依赖 `openjiuwen[claude,codex] @ git+https://gitcode.com/openJiuwen/agent-core.git@develop`（`jiuwenswarm/pyproject.toml:L20`），即直接以 Git 依赖方式绑定 agent-core 的 develop 分支；传输与服务层用 `websockets>=12.0`、`fastapi>=0.115`、`uvicorn[standard]>=0.30`、`pydantic>=2.0`；向量与持久化用 `chromadb`、`pgvector`、`faiss-cpu`、`sqlite-vec==0.1.6`、`aiosqlite`；生态 SDK 含 `skillnet-ai==0.0.16`、`a2ui-agent-sdk==0.2.1`、`google-genai`、可选 `jiuwenswarm-tui`、`pywebview`（`jiuwenswarm/pyproject.toml:L14-L102`）。
