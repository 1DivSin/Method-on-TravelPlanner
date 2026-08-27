# TravelPlanner：论文 Workflow、Claude Code 提示词与海豚错误分析

本文整理三个问题：论文中的 Workflow 究竟是什么、`claude-code-system-prompts-main.zip` 中哪些提示词适合借鉴到海豚，以及当前海豚 auto-workflow 组的 Commonsense 指标为什么偏低。

## 1. 结论摘要

论文的核心不是给模型增加一句 `Please complete the task using workflow skill.`，而是由专家预先编写一个确定性的、程序化的 Execution Blueprint。执行引擎负责步骤顺序、分支、状态和约束检查；LLM 只处理边界明确的局部子任务，不能决定整体 Workflow 路径。

当前海豚 auto-workflow 组的实现是另一种机制：模型读取 Workflow skill，为每道题临时生成 FusionFlow，自己决定步骤、依赖、并发、validator 和中间 Artifact，再由 Haitun 执行，最后还要把 Artifact 映射回 TravelPlanner 的顶层 JSON。因此它更准确地属于 **LLM-generated dynamic workflow**，不是论文中的固定 deterministic Source Code Agent。

这一区别很重要：当前 auto 组并没有完整获得论文所说的“结构上无法违反约束”的优势，反而增加了 Workflow authoring、Artifact 传递、上下文长度和最终 JSON 映射等失败面。

## 2. 论文方法不是单一 Prompt

论文采用 “Blueprint First, Model Second” 架构：

```text
专家定义 operational procedure
        ↓
source-code-based Execution Blueprint
        ↓
确定性执行引擎控制顺序、分支、状态和工具调用
        ↓
LLM 只处理 bounded sub-task
        ↓
程序化 validator / 状态检查
```

论文明确表示，LLM “never” 负责决定 Workflow 的路径。TravelPlanner 中的重复餐厅、最少住宿夜数、当前城市、返回出发地、预算等约束被编码在程序状态和分支中，而不是仅写在自然语言提示词里。

论文的 ablation 也直接支持这一点：将同一组约束文字注入 ReAct、CodeAct 和 ATLAS 的 system prompt 后，基线有所提升但仍落后于 SCA。论文的解释是：知道规则和在结构上无法违反规则不是同一件事。

因此，论文的关键变量是：

- 固定的专家 Workflow；
- 显式 Artifact / 状态；
- 程序化分支和 validator；
- LLM 的局部、受 schema 约束的调用。

它不是一个更长的 `workflow prompt`。

## 3. 当前海豚实验和论文的差别

当前两个 TravelPlanner 组的公共任务提示词相同。实现位于源实验工作区的 `blueprint/run_experiment.py`。

no-workflow 组使用公共 TravelPlanner prompt；auto-workflow 组只在其前面增加：

```text
Please complete the task using workflow skill.
```

但 auto 组同时多了 Workflow skill、`read`、`write`、`run_flow`，以及动态生成和执行 Workflow 的过程。实际链路是：

```text
读取 skill
  → 临时设计 Workflow
  → 生成 source / instruction / Artifact schema
  → run_flow
  → 读取中间结果
  → 再生成顶层 TravelPlanner JSON
```

已观察到的生成结构并不统一：

| 案例 | 动态 Workflow 结构 |
|---|---|
| case 1 | 交通、住宿、餐饮、景点四路并行，再汇总 |
| case 2 | draft → verify → finalize 串行流水线 |
| case 4 | logistics → experiences → assemble → validate |

这种灵活性与论文的固定 Blueprint 不同。特别是 `validate` 在当前实现通常仍是 LLM Step；它可以“建议检查”，但不等于程序在结构上阻止违规。

## 4. 对 `claude-code-system-prompts-main.zip` 的检查

该压缩包不是 Claude Code 的源代码，而是由 Piebald AI 从 Claude Code 编译产物中提取的提示词参考库。README 明确说明：

- 它包含多个条件化的 prompt 片段，而不是一个完整 system prompt 字符串；
- 片段中有运行时插值变量；
- 修改仓库里的 Markdown 不会自动修改 Claude Code；如需实际 patch，需要类似 `tweakcc` 的安装/补丁工具；
- 当前包对应 Claude Code v2.1.241，版本和我们的海豚运行时并不相同。

因此，它可以作为设计参考，但不能直接声称“这就是 CC Dynamic Workflow 的完整原始 prompt”，也不能整包替换 Haitun system prompt。

### 4.1 最适合借鉴的片段

以下文件与当前问题最相关：

1. `system-prompts/tool-description-workflow.md`
   - 明确 Workflow 是确定性多 agent 编排脚本；
   - 要求显式 opt-in，避免任意任务自动拉起大量 agent；
   - 区分 `pipeline` 和有 barrier 的 `parallel`；
   - 规定并发上限、预算、阶段和 resume；
   - 强调脚本编码结构，模型不应临时改变整体编排。

2. `system-prompts/agent-prompt-workflow-subagent-structured-output.md`
   - 子 agent 必须通过结构化输出工具返回；
   - 不要把最终答案放在普通文本中；
   - schema 校验失败时读取错误并修正。

3. `system-prompts/agent-prompt-workflow-script-structured-return-note.md`
   - Workflow script 中的最终返回必须严格调用结构化输出工具；
   - 工具只调用一次，输入 schema 决定返回形状。

4. `system-prompts/agent-prompt-workflow-subagent-plain-text-output.md`
   - 如果使用文本返回，返回值会被调用方原样解析；
   - 要求 JSON 时只返回 raw JSON，不要 code fence、解释或 `Done`。

5. `system-prompts/system-prompt-parallel-tool-call-note-part-of-tool-usage-policy.md`
   - 无依赖的工具调用应并行；有依赖的调用必须串行；
   - 这可用于减少旅行数据搜索的等待，但不能为了并行而破坏 Artifact 依赖。

6. `system-prompts/system-prompt-coordinator-mode-orchestration.md` 和 `system-prompt-writing-subagent-prompts.md`
   - 协调器负责拆解、汇总和验证；
   - 子 agent 提示词必须包含完整上下文、目标和返回契约；
   - 不要把“理解问题”隐含地推给子 agent。

### 4.2 适合加入 Haitun Workflow skill 的最小改造

不建议把 Claude Code 的所有 coordinator/system prompt 原样复制到 Haitun。对当前 TravelPlanner，优先考虑下面四个小片段：

```text
WORKFLOW EXECUTION CONTRACT

You are inside a workflow-backed task. First author and run the declared
workflow. Do not return a natural-language progress report as the answer.
After run_flow returns, map its final Artifact to the required top-level schema.
If the final Artifact is missing or invalid, stop and report the failed step;
do not silently fabricate or bypass the workflow.
```

```text
STRUCTURED RETURN CONTRACT

For every workflow Agent Step, return exactly the declared Artifact schema.
Use the structured result tool for the final Step output. Do not put the
answer in an ordinary text response. If schema validation reports an error,
correct the object and submit it again. At the outer session boundary, emit
only the required TravelPlanner JSON object.
```

```text
DEPENDENCY CONTRACT

Run independent data searches in parallel only when they have no Artifact
dependency. Keep draft → verify → finalize steps sequential. Every validator
must consume the complete draft and candidate data, and must check all fields
required by the official evaluator.
```

```text
FINAL FORMAT CONTRACT

Before returning, verify mechanically that every day object has the seven
required fields, day numbers are consecutive, first/last route strings are
present, accommodation is '-' on the final travel-home day, and attraction
strings use the required semicolon format. Return only {idx, query, plan}.
```

这里的“mechanically”只有在 Haitun 中接入真正的程序 validator 时才有严格含义；如果仍由 LLM 自己检查，应写成“调用程序 validator”，不要把 LLM 自检误称为 deterministic enforcement。

## 5. Commonsense 指标偏低：必须单独强调

当前保守官方 evaluator 结果如下：

| 指标 | auto-workflow | no-workflow | 差值 |
|---|---:|---:|---:|
| Delivery Rate | 95.00% | 98.89% | −3.89 pp |
| Commonsense Micro | 91.53% | 95.76% | −4.24 pp |
| Commonsense Macro | 71.11% | 76.11% | −5.00 pp |
| Hard Micro | 88.81% | 95.48% | −6.67 pp |
| Hard Macro | 87.22% | 93.89% | −6.67 pp |
| Final Pass | 70.00% | 73.89% | −3.89 pp |

这些数字来自未修改的官方 evaluator；auto 的 113、180 两题缺失答案按空 plan 计入 180 题分母，所以 auto 结果是阶段性保守结果，不应表述为完整 180 题正式完成结果。

### 5.1 为什么 Commonsense Macro 比 Micro 更值得警惕

官方 evaluator 在 validation 集上使用：

- Commonsense Micro：180 题 × 8 个 commonsense checks，共 1440 个检查点；
- Commonsense Macro：一题的全部 commonsense checks 都通过，才算该题通过，共 180 题。

因此 Macro 不是“平均字段正确率”，而是“整题 commonsense 约束全部满足率”。只错一个约束，整题 Macro 就失败。当前结果对应：

```text
auto：128 / 180 题通过全部 commonsense checks
no：  137 / 180 题通过全部 commonsense checks
```

也就是说，auto 比 no 少通过约 9 道完整任务。这个差距不能被“Micro 仍有 91.53%”掩盖：TravelPlanner 的 Final Pass 本来就是联合约束指标，单个 commonsense 错误足以让整题失去最终通过资格。

### 5.2 哪些 Commonsense 约束最需要关注

官方输出中的聚合统计（注意 auto/no 可评估样本数不同，以下主要用于定位错误类型）显示：

| Commonsense 约束 | auto 可评估样本中的通过率 | no 可评估样本中的通过率 | 解释 |
|---|---:|---:|---|
| Non-conf. Transportation | 80.70% | 79.21% | 两组都明显偏低，不能简单归因于 Workflow；长行程尤其容易出现交通冲突 |
| Complete Information | 95.91% | 98.88% | auto 更差，和空计划、最终字段遗漏、Artifact → 顶层 JSON 映射问题一致 |
| Minimum Nights Stay | 96.49% | 98.88% | auto 更差，说明住宿夜数/返程日住宿规则没有稳定固化 |
| Within Sandbox | 98.25% | 98.31% | 两组接近，不像主要差异来源 |
| Diverse Attractions | 99.42% | 100.00% | 不是主因，但存在少量重复/字段问题 |
| Reasonable City Route | 100.00% | 99.44% | auto 并非所有 commonsense 维度都更差 |

最重要的判断是：

1. **交通冲突是两组共同的 TravelPlanner 难点**。auto 甚至略高于 no，因此不能用它单独证明 Haitun Workflow 适配失败。
2. **auto 的相对劣势更集中在 Complete Information 和 Minimum Nights Stay**。这与已经看到的空 plan、缺失 `accommodation`、格式不完整和中间 Artifact 映射问题高度一致。
3. **Macro 下降说明错误具有“整题级联”效果**。一个缺字段或一个住宿夜数错误，就会把整道题从 commonsense pass 中剔除。
4. **缺失的两道 auto 答案会同时拉低 Delivery、Micro、Macro 和 Final Pass**，因此必须和“已生成答案中的约束错误”分开分析。

### 5.3 Commonsense 低并不等于 Workflow 思路失败

当前结果更支持以下分层解释：

```text
基础模型 / TravelPlanner 本身的约束推理错误
        + 动态 Workflow 设计质量不稳定
        + Artifact 和最终 JSON 交付错误
        + 少量 Haitun workspace / 回填适配风险
        → auto 的 Commonsense 和 Hard 指标下降
```

尤其不能把 Commonsense Macro 低直接解释为“Workflow 让模型不会规划了”。需要先修复输出契约和程序化 validator，再看剩余的 TravelPlanner 约束错误。

## 6. 代表性错误和原因分类

### A. Workflow 没有真正完成

部分案例最终只留下自然语言、skill 读取和工具调用过程，没有严格的 `{idx, query, plan}`。这属于 Workflow activation / authoring / final-delivery contract 失败，不是航班候选本身错误。

### B. Workflow 成功运行，但最终映射不完整

部分案例生成了多个 Step、成功 `run_flow`，但最终 JSON 仍出现最后一天缺 `accommodation`、住宿字段带多余分号等问题。这说明当前 validator 主要是 LLM 自检，而不是不可绕过的程序检查。

### C. 业务约束错误

例如最少住宿夜数、交通不冲突、候选数据范围、完整字段等。这些才是 TravelPlanner 本身的 commonsense/hard constraint 错误，需要逐条按 evaluator 输出定位。

### D. 运行时适配风险

仍需检查 workflow 临时 workspace、`run_flow` Artifact 回填、上下文截断、工具集合和超时行为。但已有多个 Workflow 成功完成，当前证据不足以支持“Haitun 全面不兼容”的结论。

## 7. 给学长的简短回答

> 论文不是提出一个 Workflow 提示词，而是提出“专家预定义的确定性程序 Workflow + LLM 局部调用”。我们当前海豚实验是模型每题动态生成 Workflow，因此没有真正复现论文最关键的 deterministic enforcement。`claude-code-system-prompts` 压缩包能提供结构化返回、并行/流水线、协调器和子 agent 提示词的参考，但不是完整 CC Dynamic Workflow system prompt，也不能直接整包移植。当前 auto 的 Commonsense Macro 只有 71.11%，低于 no 的 76.11%，对应 128/180 对 137/180 道题通过全部 commonsense checks；主要警报不是所有约束都变差，而是 auto 在完整信息、住宿夜数和最终格式/Artifact 映射上更容易出现整题级失败。交通冲突是两组共同难点，不能单独归咎于 Haitun。下一步应优先加入结构化最终返回和真正程序化 validator，再用固定 Workflow 对照动态 Workflow。

## 8. 建议的下一步实验

1. 保持当前 no-workflow 作为基线。
2. 保留当前 dynamic workflow 组，记录每题 workflow source、Step 输出和最终映射。
3. 新增 fixed workflow 组：开发者预先固定 `search → select → validate → format`，模型不得修改图结构、schema 或 validator。
4. 新增程序化 formatter/validator：由代码生成最终 JSON 并检查所有字段，不让 LLM 负责最后一次格式拼装。
5. 对每题记录八个 commonsense checks 的逐项结果，特别是 `Complete Information`、`Minimum Nights Stay`、`Non-conf. Transportation`。
6. 对 auto/no 做逐题配对统计，区分：两组都过、仅 auto 过、仅 no 过、两组都失败；缺失答案单独标记，不与业务约束失败混为一类。

## 9. 新版 Prompt（无 Validator）20 题 smoke test

为验证 Claude Code 提示词中“结构化返回 + 明确 Workflow 执行契约”的作用，已在源实验工作区的 `blueprint/run_experiment.py` 中加入 opt-in 的 `TRAVELPLANNER_PROMPT_VARIANT=v2`。默认 v1 行为保持不变；本次使用 v2，模型为 DeepSeek v4 Flash，两个 arm 的公共 TravelPlanner prompt、数据、重试策略和工具保持一致。

v2 只增加以下要求，不加入独立 validator/audit Step：

- 必须 author 并通过 `run_flow` 执行一个具体 Workflow；
- 无依赖的搜索并行，有依赖的选择/汇总串行；
- 每个 Agent Step 通过结构化 step-result 工具返回 Artifact；
- 最终 assembly Step 产生完整 `{idx, query, plan}`；
- Workflow 过程不得泄漏到最终回答。

成功运行目录为：

```text
blueprint/.runs-validation-v3-prompt-contract-no-validator-20-rerun
```

两组均完成 20/20，没有 process failure。auto 的 20/20 个案例都检测到 Workflow source，且检查未发现独立 validator/audit Step；有少数 assembly instruction 中出现“verify total cost”等普通业务动词，但不是额外 validator 节点。

官方 `evaluation/eval.py` 的 validation 入口固定要求 180 行，不能把 20 行直接当正式 benchmark 分数。因此下面是使用官方仓库中相同的 commonsense/hard constraint 实现、将分母改为 20 题后的 **条件 smoke 诊断**，不是正式 validation leaderboard 结果：

| 指标 | auto v2（20 题） | no-workflow（20 题） |
|---|---:|---:|
| Delivery | 20/20 = 100.00% | 20/20 = 100.00% |
| Commonsense Micro | 149/160 = 93.13% | 154/160 = 96.25% |
| Commonsense Macro | 11/20 = 55.00% | 15/20 = 75.00% |
| Hard Micro | 18/20 = 90.00% | 17/20 = 85.00% |
| Hard Macro | 18/20 = 90.00% | 17/20 = 85.00% |
| Final Pass | 11/20 = 55.00% | 14/20 = 70.00% |

### 9.1 对新版 Prompt 的初步判断

新版 prompt 对“能否生成并交付 Workflow”有明显帮助：auto 20/20 都生成了 Workflow 并交付非空 plan，和本轮没有出现 workflow-miss 或空 plan。但它暂时没有解决约束正确性，尤其没有解决 Commonsense Macro：auto 只有 11/20 道题通过全部 commonsense checks，no 为 15/20。

这一结果进一步说明：

1. **结构化返回契约主要改善交付，不等于改善业务约束。** auto 的 Delivery 达到 100%，但 Commonsense Macro 仍比 no 低 20 个百分点。
2. **不加 validator 时，Workflow 的约束优势仍未被固化。** v2 要求 assembly Step 输出完整 JSON，但最终仍有 5/20 个本地格式诊断案例；no 只有 1/20。
3. **auto 的 Hard 指标反而略高于 no（18/20 vs 17/20），说明 20 题样本太小，不能据此判定整体优劣。** 当前最稳定的信号仍是 auto 的额外耗时和 Commonsense Macro 劣势。
4. auto 平均单题耗时约 161.8 秒，no 约 43.6 秒，动态 Workflow 约为 no 的 3.7 倍；这是 authoring、搜索 Step、Artifact 传递和 run_flow 的直接成本。

### 9.2 v2 运行中暴露的具体问题

- case 2：最终返回的最后一天有跨城路线，但 `transportation` 为 `-`；
- cases 6、12、14：attraction 没有按要求以分号结尾；
- case 18：交通字段没有符合官方 flight/self-driving/taxi 格式；
- case 15：曾出现结构化工具参数无法解析，以及 Workflow 内模型 `finish_reason='length'` 导致一次 `run_flow` 错误，之后同一会话继续恢复并最终交付；
- Commonsense 失败主要集中在餐厅重复、住宿有效性/住宿字段、当前城市信息和完整信息，而不是 Workflow source 生成失败。

因此，这一版 v2 的结论是：**它值得保留为基础提示词改进，但还不能作为论文式 deterministic Workflow 的替代。** 下一步如果暂时仍不加入完整 validator，可以先加入更轻量的“候选数据和字段映射表”约束；若目标是提高 Commonsense Macro，则最终仍需要程序化检查或固定 Workflow，而不能只继续堆 prompt。

本文件所引用的主要材料：

- 论文：`2508.02721v2.pdf`
- 实验脚本：`blueprint/run_experiment.py`
- 官方 evaluator：`blueprint/vendor/travelplanner-official/evaluation/eval.py`
- CC prompt 参考包：`claude-code-system-prompts-main.zip`
