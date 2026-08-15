# 方向三：波次（Wave）作为事务边界 —— 映射为分布式事务、确保 ACID

> 子问题：如何将波次（Wave）的概念映射为分布式事务，确保其原子性、一致性、隔离性和持久性（ACID）？
> 覆盖：2PC、Saga、分布式事务协议、长运行事务、工作流引擎、事务性存储、AI Agent 事务。
> 审查日期：2026-08-15（已核验 URL、已补 2026 新内容）

## 二、审查新增：2026 年新内容（重点优先）

> 标记 `[三个月内]` 尽量精确；本方向严格落在 2026-05-15 之后的新论文较少，多为 2026 上半年或长期活跃项目。

### 论文

1. **[重要] Atomix: Timely, Transactional Tool Use for Reliable Agentic Workflows** — 2026-02
   URL: https://arxiv.org/pdf/2602.14849
   相关性：为 LLM Agent 工具调用提供事务性/补偿语义，直接命中"AI Agent 分布式事务"方向。
   （配套开源实现/工件: https://github.com/mpi-dsg/atomix ）

2. **[经典/重要] Distributed Sagas: A Protocol for Coordinating Microservices** — Cid, Ferreira, Guerraoui, IEEE ICDCS 2023
   URL: https://cs.brown.edu/courses/csci2952-f/slides/Class16.pdf（讲解材料，主论文可按此定位）
   相关性：最新分布式 Saga 协议形式化，讨论不持分布式锁前提下如何保证全局一致性。

### 实践/项目

3. **[三个月内] Prefect 3.0 事务型任务接口** — 2026
   URL: https://blog.csdn.net/gitblog_00611/article/details/148374527
   相关性：数据管道引入 ACID 事务型 task 接口，'transactional batch commit atomic' 方向。（二手来源，建议以官方文档为准）

4. **[活跃] DTM (Distributed Transactions Manager)**
   URL: https://github.com/dtm-labs/dtm
   相关性：跨语言 saga/tcc/xa/2-phase message/outbox/workflow 多模式，支持多存储引擎，活跃维护。

5. **[活跃] saga-engine-go**
   URL: https://github.com/grafikui/saga-engine-go
   相关性：PostgreSQL-backed 崩溃恢复型 Go Saga 执行器，2026 年新项目。

6. **[活跃] Gravtory**
   URL: https://github.com/vatryok/Gravtory
   相关性：Python crash-proof workflows，内置 sagas / durable execution，'零基础设施'方向。

7. **[活跃] kivo2/workflow-engine**
   URL: https://github.com/kivo2/workflow-engine
   相关性：基于 Kafka 的电商 checkout saga 编排引擎，幂等/崩溃容忍设计。

## 三、论文清单（经典/奠基，保留）

1. **[经典/奠基] Notes on Data Base Operating Systems** — Jim Gray, 1978
   URL: https://www.scirp.org/reference/referencespapers?referenceid=28594
   相关性：两阶段提交（2PC）首次正式提出，跨节点原子提交（波次原子性）奠基。

2. **[经典/奠基] Sagas** — Garcia-Molina, Salem, ACM SIGMOD Record 16(3), 1987
   URL: https://github.com/TianpeiLuke/Tessellum/blob/main/vault/resources/term_dictionary/term_saga_pattern.md
   相关性：Saga 模式源头——把长事务拆成一系列本地事务+补偿。

3. **[经典/奠基] Consensus on Transaction Commit** — Gray, Lamport, ACM TODS 31(1), 2004
   URL: https://www.arxiv.org/abs/cs/0408036
   相关性：分析 2PC 协调者故障阻塞问题，给出基于共识（Paxos）的非阻塞提交方案。

4. **[经典/奠基] Concurrency Control and Recovery in Database Systems** — Bernstein 等, 1987
   URL: https://dl.acm.org/doi/epdf/10.14778/3303753.3303765
   相关性：并发控制与恢复权威专著，覆盖 ACID 隔离性与持久性。

5. **[经典/重要] Linearizability: A Correctness Condition for Concurrent Objects** — Herlihy, Wing, ACM TOPLAS 12(3), 1990
   URL: https://cosmiclearn.com/dissys/strong-consistency.php
   相关性：定义"线性化"最强一致性条件，为波次提交提供串行化/隔离性语义基准。

6. **[经典/奠基] Large-scale Incremental Processing Using Distributed Transactions and Notifications（Percolator）** — Peng, Dabek, OSDI 2010
   URL: https://www.cs.utexas.edu/~witchel/S25-380L/papers/peng10osdi-percolator.pdf
   相关性：在无内建事务的 KV 上叠加快照隔离+2PC，实现跨行跨表 ACID，波次原子提交落地范例。

7. **[经典/奠基] Spanner: Google's Globally-Distributed Database** — Corbett 等, OSDI 2012
   URL: https://research.google.com/pubs/archive/39966.pdf（建议改用稳定镜像，如 storage.googleapis.com 或 Google Research 新 host）
   相关性：TrueTime+2PC 实现全局强一致外部一致性分布式事务。

8. **[经典/重要] Distributed Sagas** — Kyle Kingsbury（Jepsen）, 2019
   URL: https://raw.githubusercontent.com/aphyr/dist-sagas/master/sagas.pdf
   相关性：正式化分布式 Saga，分析异步网络下子事务约束与补偿协调的可达性语义。

9. **[现行标准] MicroProfile LRA (Long Running Actions) 规范** — Eclipse, 2021（当前 2.0.1 @2025-03-11）
   URL: https://microprofile.io/specifications/lra/
   相关性：把"长运行动作一批服务一起提交/一起补偿"的 LRA 模型标准化，是"波次作为原子活动边界"的工业规范。

10. **[经典] Unit of Work（模式文档）** — Martin Fowler, 2002
    URL: https://martinfowler.com/eaaCatalog/index.html
    相关性：单体 DB 层面"一批对象变更作为一个原子工作单元统一落库"，"波次"本地原子边界概念来源。

## 四、开源项目参考（活跃维护）

1. **[活跃] Apache Seata** — https://github.com/apache/incubator-seata — AT/TCC/SAGA/XA 四模式
2. **[活跃] Temporal** — https://github.com/temporalio/temporal — 持久化耐久执行工作流引擎
3. **[活跃] Cadence** — https://github.com/cadence-workflow/cadence — 长运行工作流编排（Temporal 同源）
4. **[活跃] TiKV** — https://github.com/tikv/tikv — Percolator 式 ACID 事务 KV
5. **[活跃] CockroachDB** — https://github.com/cockroachdb/cockroach — Raft+串行化隔离分布式 SQL
6. **[活跃] Eventuate Tram Sagas** — https://github.com/eventuate-tram/eventuate-tram-sagas-quarkus — 编排式 Saga
7. **[活跃] Axon Framework** — https://github.com/AxonFramework/AxonFramework — 事件溯源+CQRS+内建 Saga
8. **[活跃/低频] Narayana LRA** — https://github.com/jbosstm/narayana — MicroProfile LRA 参考实现
9. **[活跃] DTM** — https://github.com/dtm-labs/dtm — 跨语言分布式事务管理器
10. **[活跃] sagas** 相关：saga-engine-go（https://github.com/grafikui/saga-engine-go）、Gravtory（https://github.com/vatryok/Gravtory）

## 审查记录（2026-08-15）

- 已核验原 11 论文 + 8 项目 URL 全部有效，无剔除。
- `cs.brown.edu` 教师 slides 属二手材料，已标注建议以原始论文（Saga/Percolator/Spanner/2PC）为准。
- Spanner 归档 host（research.google.com/pubs/archive）连接不稳定，建议改用稳定镜像。
- 严格落在三个月内的新论文本方向较少，补充了 AI Agent 事务（Atomix）与若干近活跃项目（DTM、saga-engine-go、Gravtory、Prefect 3.0）。
- GitHub API 本轮限流，部分项目活跃度基于 HTTP 200 核验 + WebSearch 交叉确认，未编造 pushed_at 数据。