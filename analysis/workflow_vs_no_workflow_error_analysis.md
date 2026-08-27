# TravelPlanner：auto-workflow 相比 no-workflow 的错误归因

## 1. 结论先行

本分析针对
`.runs-validation-v3-prompt-contract-no-validator-20-rerun` 中相同的 validation 1--20 题，模型为 DeepSeek v4 Flash，auto 采用 v2 prompt；v2 要求 author/run 一个动态 Workflow，但明确**不加入独立 validator/audit Step**。

这不是完整 180 题正式 benchmark 分数，而是使用官方 evaluator 的同一套约束实现、将分母限定为这 20 道匹配题的条件诊断。

| 指标 | auto-workflow | no-workflow | 差值（auto - no） |
|---|---:|---:|---:|
| Delivery | 20/20 = 100% | 20/20 = 100% | 0 pp |
| Workflow source | 20/20 | 0/20 | — |
| Commonsense Micro | 149/160 = 93.13% | 154/160 = 96.25% | -3.12 pp |
| Commonsense Macro | 11/20 = 55% | 15/20 = 75% | **-20 pp** |
| Hard Micro | 18/20 = 90% | 17/20 = 85% | +5 pp |
| Hard Macro | 18/20 = 90% | 17/20 = 85% | +5 pp |
| Final Pass | 11/20 = 55% | 14/20 = 70% | **-15 pp** |
| 平均耗时 | 161.8 秒/题 | 43.6 秒/题 | 约 3.7 倍 |

最重要的判断是：新版 prompt 解决了“有没有 Workflow、能不能返回结果”的交付问题，但没有把 Workflow 变成能够强制执行 TravelPlanner 约束的程序。由于没有 validator，最终仍由一个模型在 assembly 阶段重新选择候选并拼接 JSON；动态 Workflow 反而增加了中间 artifact、上下文和失败面。

## 2. 逐题错误归因

下表中的“官方约束错误”是按官方 commonsense implementation 定位的；“格式诊断”是运行器对运输和资源字符串做的额外本地检查。格式错误不应与正式 Commonsense Macro 机械等同，但能说明为什么 Workflow 的返回契约没有被真正执行。

### auto-workflow 的主要失败

| 题号 | 最终错误 | 生成的 Workflow 中对应的原因 | 归因 |
|---:|---|---|---|
| 1 | Day 3 早餐重复了 Day 1 的餐厅（`First Eat`）。no-workflow 也出现餐厅重复。 | `search_restaurants` 的 artifact 示例把完整结果描述为字符串而不是结构化数组，assembly 再由模型自由挑选；没有“跨天/同日去重”的机器约束。 | **共同的模型/候选选择问题**，不是 Workflow 独有；但字符串 artifact 使问题更容易发生。 |
| 2 | Day 3 是 `from Tucson to Oakland`，但 `transportation` 为 `-`。 | assembly 指令明确写了：如果 `flights_return` 为空，就把 Day 3 transportation 设为 `-`。这把“搜索不到返程候选”和“行程不需要返程交通”混为一谈；而 TravelPlanner 的闭环路线要求仍然存在。 | **Workflow 设计直接诱发**。正确策略应是失败/修复，不是静默输出空交通。 |
| 7 | 住宿 `Huge Private Room Near Prospect Park` 不满足最少住宿夜数；Day 3 仍填写 Dallas 住宿；Day 2 早餐为空。 | Workflow 虽然写了 `minimum_nights <= 2`，但没有程序检查；assembly 还要求“每天分配一个 accommodation”，与最后一天返程应为 `-` 的语义发生冲突。搜索 artifact 也只是交给最终模型重选。 | **动态 Workflow 的约束未落地**，并有 assembly 契约冲突。 |
| 11 | Day 3 返程日仍填写 Seattle accommodation，官方判定为当前城市信息错误。 | assembly 指令写成“choose one accommodation used for all 3 nights”，而 3 天往返行程通常只有 Day 1、Day 2 两晚；生成的 Workflow 把“天数”误当成“住宿夜数”。 | **Workflow 设计错误直接造成**。 |
| 13 | Day 3 晚餐重复了 Day 1 的 `RollsKing`。 | assembly 指令主要约束候选来源和字段形状，没有独立的餐厅去重/轮换检查；中间候选经过 Workflow 后仍由单个模型自由选择。 | **Workflow 缺少业务检查**；不是执行器故障。 |
| 16 | Day 3 早餐重复了 Day 1 的 `Coffee & Chai Co.`。 | assembly 只要求从 restaurants artifact 取值，没有约束“同一天三餐不同”或跨天重复策略。 | **Workflow 缺少选择约束**。 |
| 17 | 9 个餐位几乎都选成同一家 `Moradabadi Biryani`，官方判定 Day 1 餐厅重复。 | 生成的 Workflow 对 `Washington` 场景的搜索/汇总非常薄弱，最终 assembly 没有多样性约束；它把搜索结果中的一个候选反复复制到所有槽位。 | **Workflow 的 artifact-to-plan 映射/assembly 失败**。这是最明显的“有 Workflow 但没有真正分工”的例子。 |
| 18 | 住宿 `The Best little room in Brooklyn` 不满足 minimum-nights；同时交通字符串是 `F3880999, 2022-03-27, ...`，不是官方要求的 `Flight Number: ...` 格式。 | Workflow 使用了自定义交通格式的中间/最终表示，没有由程序化 serializer 将原始 flight row 映射为官方字符串；住宿虽在指令中要求 `minimum_nights <= 2`，但没有可执行检查。 | **Workflow 的 typed artifact 与最终格式映射失败**。 |
| 20 | 住宿 minimum-nights 约束失败。no-workflow 也选择了同一住宿，因此这是共同候选选择问题。 | Workflow 明确写了 `minimum_nights <= 2`，但该要求只是自然语言；没有 validator 或候选过滤器阻止模型选择不合格 listing。 | **共同的模型/候选问题，同时暴露 Workflow 无 enforcement**。 |

由这些逐题结果可以看到，auto 的 9 个 Commonsense 失败大致可分为：住宿/夜数 4 题（7、11、18、20）、餐厅重复 4 题（1、13、16、17）、交通闭环 1 题（2）。其中 1、20 在 no-workflow 中也失败，不能把它们全部归咎于 Workflow；真正具有 Workflow 特异性的强证据是 2、7、11、13、16、17、18。

### no-workflow 的对照失败

no-workflow 的 5 个 Commonsense 失败主要是：

- 题 1：餐厅重复（auto 也失败）；
- 题 2：同时出现 Flight 与 self-driving，官方判定交通冲突；auto 虽然避免了冲突，却错误地把返程交通置为 `-`；
- 题 7：Day 2 的 `Dem Karaköy` 不在该题的 sandbox 候选数据中；auto 则暴露了更严重的住宿、返程日住宿和缺餐问题；
- 题 9：最后一天没有返程交通，官方判定路线不是 closed circle；auto 在同一题正确填入了 Philadelphia -> Sarasota 返程航班；
- 题 20：住宿 minimum-nights 失败并且 Day 2 缺早餐/餐位。

这说明 Workflow 并非在所有维度都更差：题 9 的返程航段就是一个正向例子。将搜索 outbound/return 拆成独立步骤并在 assembly 中显式引用两个 artifact，能减少 no-workflow 中“忘记返程”的概率。但题 2 表明，如果 Workflow 的 fallback 规则写错，显式分步也会把错误固化。

## 3. 仅格式层面的 auto 错误

本地格式诊断记录了 auto 5/20、no 1/20；auto 的 5 个案例是 2、6、12、14、18：

- 题 2：Day 3 跨城路线的 transportation 为 `-`；
- 题 6：三天 attraction 均没有以分号结尾；
- 题 12：Day 2 attraction 没有尾分号；
- 题 14：Day 2 attraction 没有尾分号；
- 题 18：Day 1、Day 3 transportation 使用了自定义摘要格式；

这些错误尤其能说明“提示词写了格式”不等于“系统强制格式”。例如题 14 的 Workflow assembly 指令已经写了 `semicolon-separated`，模型仍然输出无尾分号字符串。正确做法应是在最终交付前由程序 serializer 统一生成：

```text
attraction = ";".join(name_city_entries) + ";"
transportation = format_flight(raw_flight_row)
```

而不是让最终模型手写标点和字段模板。

## 4. 从生成的 Workflow 可以看到的结构性问题

### 4.1 Artifact 类型在中间步骤中退化为自由文本

题 1 的搜索步骤要求类似“`<complete verbatim flight listing>`”的字符串；其他题虽然写了 JSON，但常常只是“raw tool result verbatim”。这没有建立统一的 typed schema，例如：

```text
outbound_flights: Flight[]
accommodations: Accommodation[]
restaurants: Restaurant[]
attractions: Attraction[]
```

结果是最终 assembly 必须从长字符串中重新解析名称、价格、最低住宿夜数和时间，增加了遗漏、重复和幻觉风险。题 17 的餐厅重复以及题 7/18/20 的住宿选择失败，都符合这种“artifact 没有被真正约束”的模式。

### 4.2 自然语言约束没有变成可执行谓词

Workflow 中经常出现：

- “choose listing with `minimum_nights <= 2`”；
- “total cost must be <= budget”；
- “use exact flight format”；
- “select only candidates present in artifacts”。

但这些都是给模型看的文字，没有对应的 filter、join、schema validator 或 repair edge。没有 validator 的实验条件可以用于测 prompt-only 效果，却不能期待论文式 deterministic workflow 的约束收益。

### 4.3 部分 Workflow 的业务语义本身写错

典型例子：

- 题 2 把“返程候选为空”处理成 `transportation = '-'`；
- 题 11 把 3 天行程写成 3 晚住宿；
- 题 7 既要求每天 accommodation，又要求返程日按字段不适用时使用 `-`；
- 题 12 直接把“起点无餐厅数据、航班很晚/很早”硬编码为 Day 1/3 所有餐位为空。这样的假设可能对该题成立，但不是通用 TravelPlanner 规则。

这类错误发生在 author 阶段，后续 run_flow 只会忠实执行错误的图；Workflow 的存在反而使错误看起来更“有结构”。

### 4.4 多个 Agent 并没有形成独立交叉验证

多数图是“并行搜索 Agent -> 单个 assembly Agent”。搜索 Agent 返回候选后，没有一个独立的 constraint checker 或 selection verifier；因此多个 Agent 主要增加了调用和 artifact 传输，并没有增加可验证性。题 15 还观察到 structured tool-call 参数解析失败和 `finish_reason='length'`，说明中间层越多，运行时失败面越大。

### 4.5 外部 instruction 文件使生成结果不完全自包含

题 3、6、9、13、15 的 Workflow 通过 `./instructions/*.md` 引用 assembly 或子步骤。当前运行器确实把这些文件保存在 workspace 中，所以本次可以执行；但只保存 `.workflow/.g4` 源码时无法独立复现完整语义，也不利于审计“究竟哪一句提示词导致了错误”。固定 Workflow 实验应把指令、schema、过滤器和 evaluator 版本一起固化。

### 4.6 并行不是主要错误来源，但动态 Workflow 有明显开销

无依赖的 flights/accommodation/restaurants/attractions 搜索本来就适合并行；本次生成图的 `max_concurrency` 多为 4 或 5，方向上是合理的。auto 仍平均 161.8 秒/题，no 43.6 秒/题，主要额外成本来自：author workflow、启动/编译 run_flow、多个 Agent step、Artifact 序列化和最终 assembly。这个结果不支持继续盲目加大并行来解决正确性问题；并行只能减少等待，不能修复错误谓词。

## 5. 归因边界

不能从这 20 题得出“Workflow 天生比 no-workflow 差”。更准确的表述是：

1. 本实验测的是 **LLM 动态生成的 Workflow + 无 validator**，不是论文中的固定 deterministic workflow；
2. v2 prompt 确实改善了 Workflow 交付率和部分返程建模，但没有改善约束满足率；
3. auto 的 Commonsense Macro 比 no 低 20 个百分点，主要是动态 author/assembly 没有把约束编译成可执行检查；
4. no-workflow 的错误更多是单轮模型遗漏返程、交通冲突或住宿过滤；auto 则额外引入了错误 Workflow 语义、artifact 类型退化和多步选择漂移；
5. 因此当前最稳妥的结论是“动态 Workflow 在本设置下未体现论文式约束收益，并带来 3.7 倍延迟”，而不是“Workflow 范式本身无效”。

## 6. 下一步建议（按优先级）

1. **先做 fixed canonical workflow 对照**：固定 5 个搜索步骤（typed arrays）+ 固定 assembly，不让模型重新发明图结构；这才是和论文思路更接近的比较。
2. **在候选层做程序化过滤**：住宿按 `minimum_nights <= days-1`、`maximum_occupancy >= people_number` 过滤；返程航段为空时让 Workflow fail/repair，不允许静默 `-`。
3. **在输出层做程序化 serializer**：统一 flight、attraction 分号、`Name, City` 字段格式，避免由模型手写标点。
4. **最后再加轻量 validator/repair**：至少检查候选 membership、住宿夜数、闭环交通、字段完整性、预算；失败时只重跑 assembly，而不是重跑全部搜索。
5. **保留逐步 artifact 日志**：每题记录 raw tool rows、过滤后的候选、最终选择及每条约束的 pass/fail，这样才能区分“搜索没有结果”“过滤错误”和“assembly 选错”。

证据文件：

- [20 题诊断结果](../results/deepseek-v3-diagnostic-20/smoke-diagnostic.json)
- [auto records](../results/deepseek-v3-diagnostic-20/auto_workflow/records.json)
- [no-workflow records](../results/deepseek-v3-diagnostic-20/no_workflow/records.json)
- [auto Workflow 示例（题 2）](../results/deepseek-v3-diagnostic-20/auto_workflow/workflow-examples/oakland_tucson_trip.g4)
- [auto Workflow 示例（题 11）](../results/deepseek-v3-diagnostic-20/auto_workflow/workflow-examples/seattle_trip_planner.workflow)
- [auto Workflow 示例（题 18）](../results/deepseek-v3-diagnostic-20/auto_workflow/workflow-examples/trip.workflow)
- 实验运行器与 v2 prompt：源实验工作区中的 `blueprint/run_experiment.py`
