# Method-on-TravelPlanner

## TravelPlanner 实验结果（2026-08-27 快照）

本仓库汇总当前可供公开校对的 TravelPlanner validation 实验结果。正式对照实验均使用官方 180 题 validation split，并由锁定在提交 `e52c87f4ac348a3410c46dc3553c519db5ec5e23` 的官方 evaluator 评测。

### 正式结果

| 模型 / 协议 | 实验组 | Delivery | Commonsense Micro | Commonsense Macro | Hard Micro | Hard Macro | Final Pass |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DeepSeek V4 Flash / official prompt v5 | auto-workflow | 98.33% | 82.92% | 27.22% | 55.95% | 52.78% | 22.78% |
| DeepSeek V4 Flash / official prompt v5 | no-workflow | 100.00% | 84.10% | 28.89% | 66.43% | 66.11% | 24.44% |
| Claude Opus 5 / official prompt v1 | auto-workflow | 96.11% | 92.57% | 71.67% | 90.24% | 88.33% | 70.56% |
| Claude Opus 5 / official prompt v1 | no-workflow | 98.89% | 95.76% | 76.11% | 95.48% | 93.89% | 73.89% |

`auto-workflow` 和 `no-workflow` 使用相同的公共 TravelPlanner 用户模板。`auto-workflow` 仅额外增加 `Please complete the task using workflow skill.`，并获得 workflow skill 及 `read`、`write`、`run_flow`；两组使用相同的六类 TravelPlanner 数据工具。正式运行按题隔离 session，重试只允许进程级失败，不因答案质量或 evaluator 失败重新采样。

两个完整实验的逐题完成情况如下：

| 模型 | 实验组 | 完成记录 | 总题数 |
| --- | --- | ---: | ---: |
| DeepSeek V4 Flash | auto-workflow | 177 | 180 |
| DeepSeek V4 Flash | no-workflow | 180 | 180 |
| Claude Opus 5 | auto-workflow | 173 | 180 |
| Claude Opus 5 | no-workflow | 178 | 180 |

### 66 题 Token 诊断

`results/opus5-dynamic-workflow-token-66/` 是 2026-08-27 生成的中期诊断快照，只包含 66/180 道已完成题目，不是完整 benchmark 结果。

- 已完成题目的条件 Final Pass：50/66，75.76%。
- 为运行官方 evaluator，缺失题目以空计划补齐；由此得到的全量 Final Pass 27.78% 只能解释为当前进度下界。
- 66 题完整链路共记录 2,034 次模型调用、53,778,914 input tokens、806,031 output tokens，总计 54,584,945 tokens。
- `token-phase-report.json` 将外层 agent 成本按读 skill/grammar、编写 workflow、直接查询 TravelPlanner、调用 workflow 和最终响应分类，并另列 workflow 内 collection、assembly/selection、validation 等阶段。

### 20 题 Prompt v2 诊断

`results/deepseek-v3-diagnostic-20/` 保留分析文档引用的 DeepSeek V4 Flash 20 题诊断证据。该实验研究结构化 Workflow 执行/返回合同，不含独立 validator，也不是正式 180 题结果。目录包含双组 predictions、records、条件评分，以及题 2、11、18 的动态 Workflow 示例。

### 文件说明

每个正式实验组目录包含：

- `predictions.jsonl`：按官方 validation 顺序排列的逐题提交结果。
- `records.json`：逐题状态、耗时、重试次数、输出路径及 SHA-256。
- `official-evaluator.json`：结构化评测指标、输入哈希、官方 evaluator 版本和转换记录。
- `official-evaluator.stdout.txt` / `official-evaluator.stderr.txt`：官方 evaluator 的原始输出，便于核查结构化结果。

未重复收录 `official-evaluator-input.jsonl`，因为本次正式实验中它与 `predictions.jsonl` 内容及 SHA-256 相同。也未收录模型 session 日志、缓存、数据库、数据集副本、运行 workspace 或 API 配置。

中期 token 诊断目录额外包含：

- `interim-report.json`：66 个已完成案例的通过计数、条件指标和全量下界。
- `snapshot-manifest.json`：中期快照所含案例及来源清单。
- `token-report.json`：外层 agent、workflow 与完整链路 token 总量。
- `token-phase-report.json`：按动作及 workflow step 类型划分的 token 统计。

### 分析文档

- [`analysis/travelplanner_workflow_analysis.md`](analysis/travelplanner_workflow_analysis.md)：论文固定 Blueprint、Claude Code 提示词与当前动态 Workflow 实现的差异。
- [`analysis/workflow_vs_no_workflow_error_analysis.md`](analysis/workflow_vs_no_workflow_error_analysis.md)：两实验组的错误类型与逐题诊断。
- [`analysis/plan_quality_diagnosis.md`](analysis/plan_quality_diagnosis.md)：住宿夜数、返程闭环、餐厅多样性、序列化和 validator 等问题分析。

### 解释边界

- 这些都是 validation split 结果，不能当作官方 test leaderboard 成绩。
- `request_completion_rate` 或逐题 `status=completed` 只表示获得了可解析输出，不等于 Final Pass。
- 当前 `auto-workflow` 是模型逐题生成并执行动态 Workflow，不是论文中由专家预先编写的确定性 Execution Blueprint。
- JSON 中的绝对路径是原始运行环境的审计信息；仓库校对时应以相对目录中的文件和 SHA-256 为准。
