# TravelPlanner 20 题：应先改规划还是先改实现？

## 结论

应当先改 Workflow 的规划/架构和约束建模，然后再做实现层的 validator、serializer 和 repair。不是二选一，但优先级应为：

规划语义与任务分解 → typed artifact 与候选过滤 → validator/repair → 并行度优化

当前数据测的是 DeepSeek v4 Flash、validation 1--20、auto v2（动态 Workflow、无 validator）与 no-workflow 的匹配对照。它不是完整 180 题正式 benchmark 分数。

| 指标 | auto-workflow | no-workflow |
|---|---:|---:|
| 非空 plan 交付 | 20/20 | 20/20 |
| auto 生成 Workflow source | 20/20 | 0/20 |
| Commonsense Macro | 11/20 = 55% | 15/20 = 75% |
| Hard Macro | 18/20 = 90% | 17/20 = 85% |
| Final Pass | 11/20 = 55% | 14/20 = 70% |
| 本地格式诊断错误 | 5/20 | 1/20 |

这个组合很有辨识度：auto 通常能找到存在的候选，Hard Macro 甚至略高，但在行程语义、住宿夜数、闭环交通、餐厅组合和字段表达上更容易出错。因此当前主瓶颈不是“有没有调用工具”，而是“如何正确规划并组合结果”。

## 1. 规划/架构层错误（优先级最高）

### Case 2：返程为空的 fallback 规划错误

最终 Day 3 的 current_city 是 from Tucson to Oakland，但 transportation 为 -。生成的 Workflow 明确允许“return artifact 为空时把 transportation 设为 -”。这把“搜索不到返程候选”和“行程不需要返程交通”混为一谈。正确语义应是：返程为空时 Workflow 失败或触发修复，不能静默交付不闭环计划。

### Case 7：住宿夜数和返程日语义未建模

auto 选择了不满足 minimum-nights 的住宿，在 Day 3 继续填写 Dallas accommodation，Day 2 早餐为空。Workflow 虽然写了 minimum_nights <= 2，却没有统一建模“3 天往返通常只有 2 晚住宿”和“返程日 accommodation 应为 -”。这是规划约束没有落地。

### Case 11：把 3 天写成 3 晚住宿

该 Workflow 的 assembly instruction 写成“choose one accommodation used for all 3 nights”，最终 Day 3 仍有 Seattle accommodation，官方因此判定当前城市信息错误。这里是 authoring 阶段错误，不是简单格式错误。

### Cases 13、16、17：缺少餐厅选择策略

Workflow 只要求从 restaurants artifact 选择餐厅，没有定义同日去重、跨天重复策略或候选不足时的退化规则。结果是：

- Case 13：Day 3 晚餐重复 Day 1 的 RollsKing；
- Case 16：Day 3 早餐重复 Day 1 的 Coffee & Chai Co.；
- Case 17：大量餐位重复为 Moradabadi Biryani。

这是 selection policy 缺失，而不是工具调用失败。

### Case 20：自然语言筛选没有变成候选规划

auto 和 no 都选择了不满足 minimum-nights 的 Orlando accommodation。这个共同错误说明“prompt 写了 minimum_nights <= 2”并不等于模型执行了过滤，必须先计算住宿夜数并过滤候选。

## 2. 实现/执行层错误（第二优先级）

### Cases 6、12、14：attraction 字符串格式错误

Workflow 已经要求 attraction 以分号结尾，但最终仍出现没有尾分号的字符串。这不应依赖模型手写，应该由程序统一序列化：

    attraction = ";".join(name_city_entries) + ";"

### Case 18：flight artifact 到最终字段的 serializer 失败

最终输出使用了类似“F3880999, 2022-03-27, Denver to Palm Springs, Dep 11:16, Arr 12:28, Price 227”的自定义摘要，而官方要求“Flight Number: ..., from ..., Departure Time: ..., Arrival Time: ...”。raw flight row 应由统一 serializer 转换。

### Case 15：动态中间层增加运行时故障面

日志曾出现 structured tool-call 参数解析失败、finish_reason=length 和一次 run_flow 错误，之后会话恢复才完成。它不是 Commonsense 失败的主因，但说明 Artifact、子 Agent 和 run_flow 层级会增加实现复杂度。

## 3. 共同的模型/候选选择错误

Case 1 中 auto 和 no 都有餐厅重复；Case 20 中两组都选错 minimum-nights accommodation。这些不能简单归因于 Workflow，而是共同的候选组合弱点。auto 的自由文本 artifact 可能放大风险，但不能把所有问题都算作 Workflow 特异性。

## 4. 生成 Workflow 的结构证据

对 20 个 .workflow/.g4 做结构检查可见：

- 20/20 有 Workflow source；
- 0/20 有真正的 validator/audit Step（v2 实验明确禁止）；
- 大多数图是 4--5 个并行搜索 Step 加 1 个 assembly Step；
- 只有 Case 3 明确出现 parse/search/select/assemble 的多阶段选择结构；
- 搜索 Artifact 常被描述为 complete raw/verbatim listing，没有统一的 Flight[]、Accommodation[]、Restaurant[]、Attraction[] schema；
- minimum nights、budget、candidate membership、exact format 等约束多数仍是自然语言，没有对应的可执行 filter/predicate。

因此当前 auto 的图更像“多个模型搜索候选后，由一个模型重新理解长文本并拼接 plan”，而不是固定的 deterministic planning pipeline。

## 5. 建议的改动顺序

### 第一阶段：先修规划/架构

固定一个 canonical TravelPlanner Workflow，不让模型每题重新发明业务图：

    parse_query
      -> parallel search_outbound / search_return / search_accommodation / search_restaurant / search_attraction
      -> programmatic candidate_filter
      -> assembly
      -> validator
      -> failure: repair_assembly -> validator
      -> success: serializer -> final plan

应先固定这些规则：

1. n 天闭环旅行通常有 n-1 晚住宿，返程日 accommodation 为 -；
2. 返程候选为空不能静默输出 transportation = -；
3. 住宿先按 minimum nights、maximum occupancy、城市过滤；
4. 每个资源必须有明确 membership 关系；
5. 餐厅组合要有去重和候选不足时的退化规则；
6. Day 1/Day n 的交通和餐位规则由统一 schema 定义。

### 第二阶段：补实现层 validator/serializer

Validator 至少检查：day 数量和字段完整性、闭环 outbound/return、交通格式、候选 membership、minimum nights/occupancy、住宿夜数、必需餐位和景点、餐厅重复、城市一致性和总预算。失败时只重跑 assembly/repair，不要重新搜索。

## 6. 对“现在是否直接补 validator”的判断

可以补，但不建议把它作为唯一改动。若直接在现有动态 Workflow 上追加 validator，可能出现：

- validator 发现 Day 3 transportation 缺失，但原 Workflow 仍认为 fallback 为 - 合法；
- validator 发现 minimum-nights 不满足，但 artifact 是长字符串，无法可靠过滤；
- validator 要求 attraction 尾分号，但 assembly 继续手写字符串；
- repair agent 在错误的 Workflow 语义下反复产生同类错误。

建议实验顺序：

1. 规划修正版、无 validator，确认 schema 和住宿/返程/餐厅规则；
2. 同一规划加 validator/repair，测实现层强制检查的增益；
3. 固定 Workflow 对比动态 Workflow；
4. 最后测试并行度和性能。

## 最终判断

当前证据更支持“先从规划角度入手，同时准备实现层修复”，而不是单独补 validator。业务错误的主导模式是住宿夜数、返程闭环和餐厅多样性；格式和候选 membership 则适合由 serializer/validator 解决。继续堆 prompt 或盲目增加并行，不能解决这些错误。

证据：

- [20 题诊断](../results/deepseek-v3-diagnostic-20/smoke-diagnostic.json)
- [auto records](../results/deepseek-v3-diagnostic-20/auto_workflow/records.json)
- [no-workflow records](../results/deepseek-v3-diagnostic-20/no_workflow/records.json)
- [错误逐题分析](workflow_vs_no_workflow_error_analysis.md)
