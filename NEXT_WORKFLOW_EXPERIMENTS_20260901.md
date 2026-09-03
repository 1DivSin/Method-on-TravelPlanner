# Next Workflow Experiments

按以下顺序执行：

1. [x] 完成 psi-agent PR #25 的 TravelPlanner frozen-30 诊断评测（非完整 30 题推理结果）。
   - PR #25 是参照 cc-dynamic-workflow 的修改结果；本次固定候选 commit 为 `82268b424dbd486f6092e4cfdb3ae1a91c01f74d`。
   - r5 在 30 题中返回 29 题；case 33 在三次相同 prompt 的 process/transport 尝试后仍失败。
   - 按已授权的诊断口径保留全部 29 个 process-complete 答案，以空计划填充 case 33 和其余 150 个 validation case，再运行 180 行官方 evaluator。
   - 官方 evaluator 原始 Final Pass Rate 为 `19/180 = 10.5556%`；对应 frozen-30 诊断计数为 `19/30 = 63.3333%`，其中 case 33 计为失败。该结果不能表述为完整 30 题推理结果，也不能外推为真实 180 题准确率。
   - 其余官方原始指标：Delivery `29/180`，Commonsense Micro `224/1440`，Commonsense Macro `21/180`，Hard Micro `65/420`，Hard Macro `26/180`。
   - token usage、provider cost 和 normalized cost 均为 `unknown`；1503 条 provider request 日志中没有 token-usage signal，不得把缺失值记为 0 或据调用次数估算费用。
   - 结果见 `evaluations/pr25-dynamic-authoring-frozen30-20260902-r5/REPORT.md` 和同目录 `auto_workflow/official-evaluator.json`。
   - 路径问题已修正：共享 executable 位于 `/public/home/sychen/cxy/workflow/psi-agent/.venv/bin/psi-agent`。Unix socket 的 `EPERM` 来自受限 sandbox；授权 host context 可正常创建，r5 的 10 个 socket 均成功监听。

2. [ ] 测试开源 Dynamic Workflow：
   `https://github.com/ChaosRealmsAI/open-dynamic-workflow?utm_source=chatgpt.com`
   - 运行 Claude Code + open-dynamic-workflow。
   - 与纯 Claude Code、纯海豚和 psi-agent method 对比准确率、token 和 cost。

3. [ ] 补测纯 Claude Code 和纯海豚的 cost。
   - 复用先前测试结果或同一测试设置，不因补测 cost 改变任务、模型或评测口径。
   - 分别汇总准确率、token 和 cost，供后续对比。

4. [ ] 完成 psi-agent 完整 method 的 TravelPlanner 180 题测试。
   - 使用最终确定的完整 method 版本。
   - 记录准确率、token 和 cost。
