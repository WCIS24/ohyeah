# 里程碑报告

## 目录

1. 研究问题与报告边界
2. 冻结状态与事实源说明
3. 系统全链条与模块总览
4. 评测口径、子集与实验矩阵
5. 模块级结果与消融解释
6. 组合模块 C 与“不是叠加幻觉”的判定
7. Baseline 文献对齐
8. 复现与封装
9. 讨论、局限与后续工作
10. 结论
11. 缺证据项清单

## 1. 研究问题与报告边界

本项目聚焦于复杂金融查询的检索增强问答。这里的“复杂”不是泛指问题长度，而是指查询在求解时同时提出了四类要求：第一，系统必须理解金融缩写、简称和行业术语；第二，系统必须在多个段落乃至多个文档之间补齐证据链；第三，系统必须在需要时执行数值计算，而不是只做文本匹配；第四，系统必须把上述过程封装为可复现、可审计、可冻结的工程链路。这个问题定义与选题评价文档中提出的目标一致，即“引入多步检索推理机制提升金融 RAG 系统在复杂金融查询中的性能”，并特别强调缩写歧义、跨段证据和数值比较是金融场景下的真实困难点。

不过，本报告不再沿用最初“必须靠 multistep 才能提升”的假设，而是严格以当前仓库已经跑通、已经封条、已经写入 `docs/TABLE_*` 与 `docs/SEAL_*` 的结果为唯一事实源。换言之，报告的目标不是复述最早的设想，而是回答三个更硬的问题：第一，当前哪一部分已经形成稳定结论；第二，哪一部分只是合理 baseline 但未带来净增益；第三，哪一部分虽然出现交互效果，但还不能写成论文里的正向主结论。

这一定义直接决定了报告的写法。凡是能写成“强结论”的部分，都必须同时满足两条：一是表格里有稳定指标改善；二是 run 级别的开关能定位到明确模块。凡是不满足这两条的内容，报告不会强行上价值，而是明确写成 baseline、负结论、弱结论或风险披露。尤其是 calculator 与组合模块 C，本报告不会把“coverage 上升”偷换为“闭环成功”。

这种写法看上去比常规实验报告更“克制”，但它恰恰更适合当前项目所处的阶段。因为本项目已经从“还能继续随意试模块”的探索期，进入了“要把阶段性结果封装成论文叙事”的冻结期。到了这个阶段，最重要的不是把每个想法都写成贡献，而是把已经稳定的部分写实，把尚未闭环的部分写透。只有这样，后续正文、答辩陈述、图表脚注与附录审计才不会彼此打架。换句话说，本报告不是为了制造一个看起来更完整的故事，而是为了留下一个以后还能被复现、还能被核验、还能被继续迭代的故事。

## 2. 冻结状态与事实源说明

当前封条状态是 `READY`，对应的 seal matrix 为 `20260228_055920_06d6bb`，20 个 seal runs 全部达到 `status=ok`，并且当前启用图的 `has_data=False` 数量为 0。这一结论来自 `docs/SEAL_FINAL_CHECK.md`，其中明确记录了 `matrix_status=20/20 ok`、`plot_has_data_false_count=0`、`tables_updated=Yes`、`plots_updated=Yes`。因此，本报告的实验部分可以直接把本轮 seal 视为有效、可复现、可冻结的结果集合。

同时，封条文档也明确规定了事实源的优先级。第一层事实源是 `configs/step6_matrix_seal.yaml`、`configs/step6_experiments_seal.yaml`、`scripts/plot_config.yaml`；第二层事实源是 `docs/TABLE_MAIN.md`、`docs/TABLE_NUMERIC.md`、`docs/TABLE_ABLATION.md` 与 `docs/SEAL_*`；第三层才是本地 `outputs/**`。之所以这样排序，是因为远端仓库不把 `outputs/` 作为提交边界，真正可提交、可审计的证据指针必须落在 `docs/TABLE_*` 与 `docs/SEAL_*`。因此，凡是本报告使用了 `outputs/**` 日志、JSON 或 `calc_stats.json` 之类的补充证据，都会明确标注为“本地审计补充，不可远端核验”。

封装边界也已写清。`outputs/`、`data/`、`models/` 不属于 commit 边界；commit-safe 的证据表面是 `docs/TABLE_*`、`docs/SEAL_FREEZE_MANIFEST.md`、`docs/SEAL_FINAL_CHECK.md`，以及 `thesis/figures_seal/**`。这意味着论文写作时，图表和结论应优先引用 commit-safe 文档，而不是把 `outputs/` 当成正式发表表面。

## 3. 系统全链条与模块总览

从当前 seal 配置看，系统不是一个黑盒模型，而是一条可拆解的链路：输入 query 后，先进入 retriever；retriever 决定采用 dense、bm25 或 hybrid；随后在 retrieval 侧可选择不开启 multistep、开启 multistep，或者用 PQE 替代 multistep；在 answer 侧，可选择不开启 calculator、开启 calculator，或者把 PQE 与 calculator 联动起来。这样的设计使得每个模块都能以“开关”形式进入消融矩阵，而不是只能做整体系统对比。

换句话说，本项目的工程主线可以概括为“retrieval 先决定能否把证据找回来，answer-side tool 再决定能否把数值链路收束起来”。这条主线和选题评价文档中“复杂金融查询同时受到缩写歧义、跨段证据和数值计算约束”的判断是一致的，只是当前 seal 结果告诉我们：真正稳定的增益主要出现在 retrieval 侧，而不是 answer-side calculator 侧。

### 表 1 系统模块总览表

| 模块 | 主要输入 | 主要输出 | 关键开关 | 代表 run | 当前定位 |
| --- | --- | --- | --- | --- | --- |
| Retriever FT | query、corpus chunk | dense ranking | `retriever.dense.model_name_or_path` | `m01`、`m02` | 强结论模块 |
| 检索模式 | query、索引 | dense/bm25/hybrid 结果 | `retriever.mode` | `m02`、`m03`、`m04` | 强结论模块 |
| Multistep | 初始 query、首轮结果 | 迭代检索轨迹 | `multistep.enabled`、`multistep.max_steps`、`multistep.gate.*` | `m05`、`m07`、`m09` | baseline |
| PQE | query、初始 top-k | 扩展 query 集合 | `qexpand.enabled`、`qexpand.abbrev.enabled`、`qexpand.prf_year.enabled` | `m18`、`m19` | 替换模块 |
| Calculator | retrieval 证据、numeric task | 数值答案 | `calculator.enabled`、`calculator.gate.*` | `m11`、`m12`、`m13`、`m15` | 诊断模块 |
| 组合模块 C | PQE 输出 + calculator 路由 | retrieval + numeric interaction | `qexpand.*` + `calculator.*` | `m20` | 弱结论，未闭环 |
| 子集口径 | dev query 集 | complex / abbrev / numeric 子集 | `eval.subsets.*` | `m18`、`m20` | 口径风险需披露 |

如果把这条链路写成更贴近论文方法章的流程，可以概括为五步。第一步，系统读入自然语言 query，并在 query 级别判断其中是否存在缩写、年份、省略口径或明显的数值任务线索。第二步，retriever 依据 `retriever.mode` 选择 dense、bm25 或 hybrid 索引策略；在当前 seal 中，主线默认落在 dense。第三步，若开启 PQE 或 multistep，系统会在 retrieval 前后对 query 或候选结果做二次改写与再检索；这一步的目的不是直接生成答案，而是让 top-k 候选覆盖更可能包含答案证据。第四步，reader / answer 侧读取候选证据，若命中数值任务路由，则进入 calculator 或 fallback。第五步，系统输出文本答案或数值答案，并在评测脚本中分别写入 retrieval metrics 与 numeric metrics。

这五步里，真正决定上限的是前两步，真正暴露瓶颈的是后两步。原因很直接：如果前两步没有把对的公司、对的年份、对的段落找回来，后面的 calculator 再强也只能在错误证据上工作；反过来，如果 retrieval 已经把候选空间大幅压缩到正确证据附近，后面的模块才有机会表现出增益。因此，本项目后续所有对照都可以读成对这条链路中某一处“瓶颈位置”的定位。Retriever FT 回答的是“底座检索器是否足够懂金融语料”，mode 对照回答的是“什么索引模式更适合作为主链”，multistep 与 PQE 回答的是“query-side 该如何补 retrieval gap”，calculator 与组合模块 C 回答的是“拿到更多证据以后，数值链路能否闭环”。

从工程实现角度看，这种模块拆分还有一个重要作用：它把“方法创新”与“工程封装”放在同一张矩阵里。很多实验项目最后只能得出一句“整体系统变好了”，却说不清是数据、模型、阈值、prompt 还是后处理起了作用。当前仓库通过 `step6_matrix_seal.yaml` 把核心变量尽量显式化，意味着论文写作时可以把方法章与实验章一一对上，而不是让读者面对一个难以复现的黑盒流水线。

## 4. 评测口径、子集与实验矩阵

本轮 seal matrix 覆盖 20 个 runs，结构上分为四层。第一层是 retriever FT 与 mode 对照，包括 `m01` pre-FT dense、`m02` post-FT dense、`m03` bm25、`m04` hybrid。第二层是 multistep 及其 gate 对照，包括 `m05` 到 `m10`。第三层是 calculator 及其 gate / allow-list / task-space 对照，包括 `m11` 到 `m17`。第四层是 PQE 替代链路与其交互，包括 `m18`、`m19`、`m20`。这种矩阵设计的优点是每一层都有 baseline，缺点是 answer-side 和 retrieval-side 的指标并不完全落在同一个表里，因此需要通过 `TABLE_MAIN`、`TABLE_NUMERIC`、`TABLE_ABLATION` 三张表联合阅读。

子集口径方面，当前仓库已经有 `data/subsets_v2/subsets_stats.json`，其中记录了 `complex=243`、`abbrev=501`、`numeric=466` 和 `rule_hits.two_years=49`，说明复杂子集里确实包含“两年比较”类样本，也就意味着复杂金融查询并非一个空标签。然而，当前 seal 运行的 resolved config 仍指向 `data/subsets/dev_*`，而不是 `data/subsets_v2/*`。因此，本报告会把“子集概念已经修正”与“当前 seal 运行尚未完全切换到新路径”同时写出，不把口径修复写成已经完全落地的事实。

### 表 2 消融矩阵总表

| run | 关键开关 | 关键指标 | 结论等级 | 说明 |
| --- | --- | --- | --- | --- |
| `m01` pre-FT dense | `dense + pre-FT model` | `full_r10=0.3246` | baseline | retriever FT 前对照 |
| `m02` post-FT dense | `dense + FT model` | `full_r10=0.3789`、`full_mrr10=0.2554` | Strong | FT 后主基线 |
| `m03` bm25 | `retriever.mode=bm25` | `full_r10=0.2246` | Negative | 词法基线显著弱于 dense |
| `m04` hybrid | `retriever.mode=hybrid` | `full_r10=0.3491` | Moderate baseline | 好于 bm25，弱于 dense |
| `m05` multistep | `multistep.enabled=true` | `full_r10=0.3789`、`full_mrr10=0.2556` | Negative | 与 `m02` 基本持平 |
| `m07` gate open | `multistep.gate.min_gap_conf=0.0` | `full_mrr10=0.2556` | Negative | 放开 gate 仍无净增益 |
| `m09` gate disabled | `multistep.gate.enabled=false` | `full_r10=0.3789` | Negative | 说明问题不只在 gate |
| `m12` calculator main | `calculator.enabled=true`、`allow=["yoy","diff"]` | `num_em=0.3197`、`num_cov=0.6695` | Negative | 作为 calculator 主 baseline |
| `m13` calc gate off | `calculator.gate.enabled=false` | `num_em=0.2867`、`num_cov=0.6824` | Negative | coverage 上升但 EM 更低 |
| `m15` calc task expand | `allow += ["share","multiple"]` | `num_em=0.2933`、`num_cov=0.6824` | Negative | 扩任务空间未形成闭环 |
| `m18` PQE full | `qexpand.abbrev=true`、`qexpand.prf_year=true` | `full_r10=0.3842`、`complex_r10=0.4074` | Moderate | 替换 multistep 的主增益模块 |
| `m19` PQE abbrev-only | `qexpand.prf_year=false` | `full_r10=0.3789` | Negative ablation | 说明主增益来自 PRF-year |
| `m20` PQE + calc | `qexpand.* + calculator.*` | `num_cov=0.6867`、`num_em=0.3079` | Weak | 有交互，无闭环 |

这张表的阅读方式需要再说明一次，因为它实际上压缩了三张正式表和一套 seal config。对 retrieval-side 模块，应优先看 `TABLE_MAIN` 中的 `full_r10`、`full_mrr10`、`complex_r10` 与 `abbrev_r10`。其中，`R@10` 更接近“答案证据有没有被找回来”，`MRR@10` 更接近“答案证据排得靠不靠前”。这两个指标同时改善，才能说明模块既扩充了召回，也没有牺牲排序质量。对 numeric-side 模块，则应优先看 `TABLE_NUMERIC` 中的 `numeric_em` 与 `numeric_coverage`。其中，coverage 表示系统是否愿意给出数值答案，EM 表示给出的数值答案是否正确。只涨 coverage 不涨 EM，通常意味着链路更激进了，但没有更可靠。

也正因为指标语义不同，报告才需要把“强结论”“弱结论”“负结论”分层。Retriever FT 与 dense mode 的强结论来自 retrieval 主指标同步提升；PQE 的中等强度结论来自 retrieval 主指标小幅但一致提升，且 `m19` 反事实对照支撑了触发机制；multistep 的负结论来自主指标基本不动，且日志对“为什么不动”给出了相对清楚的停止原因；calculator 和组合模块 C 的弱结论或负结论，则来自 numeric coverage 与 numeric EM 的背离。换句话说，结论等级不是主观打分，而是对“指标是否一致、对照是否干净、日志是否能解释”的综合压缩。

这张表还有一个论文写作上的价值：它帮助区分“适合进摘要的结论”和“适合进讨论的结论”。摘要最忌讳把尚未闭环的模块也写成成果，因此像 `m20` 这种有交互但无闭环的结果，更适合放在实验后半段与局限讨论里；而 `m01 -> m02`、`m02 -> m18` 这类对照，则可以自然进入摘要、结论和方法贡献段。这个区分并不是保守，而是为了保证整篇论文在口径上前后一致。

## 5. 模块级结果与消融解释

### 5.1 Retriever FT：当前链路中最稳的强结论

Retriever FT 是本轮最干净、也最可重复的正向结论。`m01` 与 `m02` 只在 dense retriever 的模型路径上有差异，其余 retrieval mode 与 answer-side 开关保持一致，因此该对照可以直接理解为“pre-FT vs post-FT”。结果上，`full_r10` 从 `0.3246` 提升到 `0.3789`，`full_mrr10` 从 `0.2030` 提升到 `0.2554`，`complex_r10` 从 `0.3457` 提升到 `0.3951`，`abbrev_r10` 从 `0.3174` 提升到 `0.3713`。这四个方向同时改善，说明 FT 不是只对某个特定子集偶然生效，而是把整个 retrieval foundation 往上抬了一层。（证据：`TABLE_MAIN` 第3行与第4行；run_id=`20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m01`、`20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m02`）

更重要的是，这个结论没有依赖 calculator，也没有依赖 PQE 或 multistep，因此它可以单独成立。论文写作时，这一结论可以作为“系统主增益首先来自检索器领域适配”的核心论点，而不需要把后续模块绑上去做联合论证。也正因为如此，Retriever FT 是当前最适合写进摘要和结论的强结论模块。

边界同样要交代清楚。第一，本轮 seal 并没有重新比较更广泛的 dense encoder 家族，只证明了当前 `models/retriever_ft/20260203_005729_cd195e` 比 `sentence-transformers/all-MiniLM-L6-v2` 更适合当前任务。第二，`latest` 可变指针已被 seal config 固定成显式模型路径，因此这不是一个漂移结论，而是一个可冻结结论。

### 5.2 Dense / BM25 / Hybrid：dense 是当前 seal 的唯一稳定模式

检索模式对照同样给出了较强结论。`m02` dense、`m03` bm25、`m04` hybrid 在同一 FT model 之上比较。结果上，dense 的 `full_r10=0.3789`，显著高于 bm25 的 `0.2246`，也高于 hybrid 的 `0.3491`；`full_mrr10` 上 dense `0.2554` 同样高于 bm25 `0.1266` 和 hybrid `0.2092`。因此，当前 seal 里不存在“hybrid 虽然 recall 稍弱但 ranking 更强”的补救叙事，dense 在 recall 与 ranking 两个维度都更强。（证据：`TABLE_MAIN` 第4、5、6行；run_id=`...m02`、`...m03`、`...m04`）

这件事的意义有两层。第一，它告诉我们后续 PQE 的收益不是建立在一个弱检索器上“补漏洞”，而是在当前最强 retrieval mode 上继续微调；第二，它说明 bm25 和 hybrid 的保留价值主要是 baseline 与对照，而不是论文里主方法的一部分。换言之，dense 是主链，bm25 与 hybrid 是证伪“是否必须混合才能更好”的必要对照。

需要保守处理的地方在于，当前 hybrid 只比较了 `alpha=0.5` 这一设定，不能把“hybrid 全部无效”写成一般性理论结论。更准确的表述应当是：在当前 seal config 下，dense 是最优模式；hybrid 在本轮未超过 dense。

### 5.3 Multistep：合理的 baseline，但不是当前主增益来源

项目最初的问题设定高度强调多步检索，因此 multistep 被纳入 baseline 完全合理；但 seal 结果表明，它不是当前主增益来源。`m02` 与 `m05` 比较时，`full_r10` 完全不变，仍为 `0.3789`；`full_mrr10` 仅从 `0.2554` 变到 `0.2556`，改善幅度只有 `+0.0002`。这不是“有提升但较弱”，而是“在论文主结果层面几乎不可见”。（证据：`TABLE_MAIN` 第4行与第7行；run_id=`...m02`、`...m05`）

更关键的是，本地 multistep 日志解释了为什么它不显著。`m05` 的 stop reasons 为 `{'MAX_STEPS': 45, 'GATE_BLOCKED': 525}`，说明绝大多数样本根本没有进入有效的后续迭代；而 `m09`、`m10` 在 gate disabled 后仍然清一色出现 `NO_GAP`，说明即便把 gate 放开，系统也没有找到足以改变 top-k 的新增证据。这意味着 multistep 的失败并不只是阈值调得太严，而是当前任务分布下，迭代策略本身没有形成有用的 retrieval 增量。（证据：`TABLE_ABLATION` 第4行与第6行；run_id=`...m07`、`...m09`；补充证据：`outputs/20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m05_ms/logs.txt`、`...m09_ms/logs.txt`，本地审计补充）

因此，multistep 在本报告中的位置应当被明确为“baseline”。它有理论合理性，也有工程实现价值，但当前 seal 结果没有支持它继续承担论文主方法的角色。这个定位并不削弱项目，反而提高了结论的可信度：我们并没有为了保住最初设想而忽视反证。

从研究叙事上看，multistep 的这组负结果其实完成了一项很重要的“排除法”工作。复杂金融查询天然让人联想到“必须多跳、必须反复检索、必须显式推理”，但当前结果表明，至少在这套数据和实现下，query-side 的轻量改写比显式迭代更划算。也就是说，问题未必在于“系统不会多步思考”，更可能在于“原始 query 缺了几个关键检索线索”，而这些线索通过 PQE 这类更直接的办法就能补齐。正因为 multistep baseline 被明确证伪，PQE 的替代价值才不是随便找个模块来接棒，而是建立在一条被认真检验过的比较链上。

### 5.4 PQE：替代 multistep 的 retrieval-side 有效模块

如果说 multistep 是被证伪的 baseline，那么 PQE 就是当前 retrieval 侧真正替代它的模块。`m02` 对 `m18` 的结果显示，`full_r10` 从 `0.3789` 提升到 `0.3842`，`complex_r10` 从 `0.3951` 提升到 `0.4074`，`abbrev_r10` 从 `0.3713` 提升到 `0.3752`。提升幅度不算大，但方向一致，且复杂子集的改善最明显，这与金融复杂查询里“年份补全、口径补全”更重要的直觉一致。（证据：`TABLE_MAIN` 第4行与第20行；run_id=`...m02`、`...m18`）

PQE 为什么有效，不能只看表，还要看触发证据。本地 `m18` 日志显示，full set 上 `queries_expanded=483/570`，其中 `prf_year_expanded_count=483`，而 `abbrev_expanded_count=11`；complex 子集上 `queries_expanded=219/243`，abbrev 子集上 `queries_expanded=426/501`。这说明 PQE 的主体不是简单的缩写展开，而是对年份与 PRF 信号的系统性扩展。换句话说，PQE 的真实收益来自“把复杂查询需要的年份线索提前写回 query”，这比原先依赖 multistep 反复摸索证据链更直接。（补充证据：`outputs/20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m18/logs.txt`，本地审计补充）

`m19` 提供了关键的反事实对照。该 run 只保留 `abbrev.enabled=true`，关闭 `prf_year.enabled`，结果几乎回到 baseline：`full_r10=0.3789`，`complex_r10=0.3951`。因此，PQE 的主增益并非“展开简称”本身，而是 `prf_year` 带来的 query reformulation。这个结论非常适合在论文中写成“PQE 不是一个泛化查询扩展器，而是一个对复杂金融查询尤其是年份口径问题更敏感的 retrieval-side 替代模块”。（证据：`TABLE_ABLATION` 第13行与 `TABLE_MAIN` 第20行；run_id=`...m19`、`...m18`）

边界在于，PQE 当前是“中等强度正向结论”，不是像 Retriever FT 那样的大幅提升。论文写法上更适合说“在当前最优 dense retriever 上继续带来稳定但幅度有限的 retrieval lift”，而不宜写成“显著重构了系统性能上限”。

但从工程可解释性的角度看，PQE 比很多“黑箱增强”更适合写进论文主线。原因在于它的触发机制和收益路径都相对透明：`m18` 的日志能直接看见扩展了多少 query、哪类扩展占主导、哪些子集触发更频繁；`m19` 又把“abbrev-only”这条局部路径单独剥离出来，证明主增益来自 `prf_year`。这种可解释性意味着 PQE 不只是“分数略有上升”，而是“可以说明为什么上升、上升发生在何处、如果关闭关键子模块会怎样”。对于一篇需要兼顾工程复现和学术叙事的里程碑报告，这类模块比单纯分数更高但不可解释的方法更有写作价值。

### 5.5 Calculator：单模块没有形成闭环收益

Calculator 是本项目里最需要克制写法的部分。单看 `m11` 到 `m15`，你会发现 coverage 与 EM 经常反向移动：例如 `m11 -> m12` 时，`num_cov` 从 `0.6180` 提升到 `0.6695`，但 `num_em` 从 `0.3964` 下降到 `0.3197`；`m12 -> m13` 时，coverage 继续升到 `0.6824`，EM 又降到 `0.2867`；`m15` 扩大任务空间后，coverage 维持 `0.6824`，EM 仍只有 `0.2933`。这说明 calculator 并不是“只差一个阈值就能闭环”，而是存在系统性的 route-quality gap。（证据：`TABLE_NUMERIC` 第13至17行；run_id=`...m11`、`...m12`、`...m13`、`...m15`）

封条文档对这一点给出了明确的工程判断：当前 calculator 应定位为 diagnostic / exploratory module，而不是 sealed production gain module。这个判断不是文字上的保守，而是由 closure 检查矩阵推出来的。`docs/CALC_CLOSURE_REPORT.md` 明确写到，虽然某些设置下 `numeric_em` 可以提升，但在统一 guardrail 下没有形成稳定 closure-level gains；核心原因是 `calc_used` 子路径与 `fallback` 子路径之间的质量差距没有收敛。也就是说，calculator 真正的问题不在“算术公式不够多”，而在“什么时候该进 calculator、进了以后能否拿到对的 facts”。

本地 `calc_stats.json` 进一步支撑了这个定位。以 `m12` 为例，`fallback_ratio≈0.8596`；`m13` gate off 后 `fallback_ratio≈0.8000`，但 EM 下降；`m15` 扩任务空间后 `fallback_ratio≈0.8053`，仍未形成净收益。这说明只要 task detection 和 fact selection 仍然不稳，单纯扩大 calculator 接管范围通常只会换来“coverage 上去、EM 下来”的结果。

因此，calculator 在论文中的正确写法不应是“核心创新模块”，而应是“数值链路的诊断模块与后续工作接口”。这虽然不是一个正向主结论，但它对论文很重要，因为它解释了为什么项目最后把主贡献范围锁定在 retrieval FT、mode ablation、PQE replacement，而没有把 calculator 也包进主贡献里。

这类“负结论但有解释力”的结果，在里程碑报告里其实非常关键。如果只写正向结果，读者会误以为项目只是把有效模块堆在一起；而 calculator 的失败恰好说明，本项目已经把数值链路的问题定位到比“有没有工具”更细的层次。现在真正缺的不是一个算式库，而是让系统在正确样本上触发 calculator，并保证送进去的事实本身足够干净。这个结论虽然不光鲜，但它把下一阶段的工作空间大幅缩小了：后续无需再盲目扩展工具能力，而应集中修路由质量、事实对齐和 calculator-used path 的 precision。

### 5.6 子集口径：概念上已修复，运行时仍有漂移风险

子集口径看似只是工程细节，实际上直接影响“complex”“abbrev”“numeric”这些词在论文里是否可信。当前 `data/subsets_v2/subsets_stats.json` 已给出明确统计：`complex=243`、`abbrev=501`、`numeric=466`，其中 `two_years=49`，说明复杂子集里确实包含需要跨年份比较的样本。这使得“复杂金融查询”在本项目中不是一句泛话，而是有明确切分依据的评测口径。

但 seal resolved config 仍然指向 `data/subsets/dev_complex_qids.txt`、`data/subsets/dev_abbrev_qids.txt`、`data/subsets/dev_numeric_qids.txt`。因此，严格来说，本轮结果的“complex/abbrev/numeric”语义已经有了新口径定义，但运行时路径尚未完全切到 `subsets_v2`。这个问题并不推翻当前结论，因为 `TABLE_*` 中的相对改善关系仍然存在；但它要求论文在复现章节里明确披露：子集口径修复已经文档化，路径对齐仍是下一轮 freeze refresh 的工作项。（证据：`data/subsets_v2/subsets_stats.json`；`outputs/...m18/config.resolved.yaml` 第188-190行，本地审计补充）

把这件事单独写出来，还有一个论文口径上的考虑。复杂金融查询并不是一个读者天然接受的标签，答辩或审稿时很容易被追问“complex 到底复杂在哪”。如果子集定义本身不稳定，那么后面所有关于“complex 子集上提升更明显”的陈述都会被削弱。因此，当前最稳妥的写法是把 `subsets_v2` 视为概念修复，把本轮 seal 视为在旧路径上的最后一次冻结；这样既承认了已有工作，也不把尚未完全切换的路径写成已完成事实。

### 5.7 模块结论分层：哪些能进摘要，哪些只能进讨论

为了避免论文不同部分口径不一致，本报告把模块结论分成三层。第一层是可以直接进入摘要和最终结论的内容，包括 Retriever FT、dense mode 以及 PQE replacement。它们的共同特征是：有明确的 baseline 对照，有干净的 run-level 开关，有表格中稳定改善的主指标，而且没有依赖未闭环模块的补充叙事。对应证据分别是 `m01 -> m02`、`m02` 对 `m03/m04`、`m02 -> m18` 加 `m19` 反事实对照。（证据：`TABLE_MAIN` 第3-6行、第20行；`TABLE_ABLATION` 第13行；run_id=`...m01`、`...m02`、`...m03`、`...m04`、`...m18`、`...m19`）

第二层是可以进入实验主体、但不适合写成“贡献”的内容，包括 multistep baseline 与 calculator diagnostic。它们对论文仍然重要，因为它们回答了“哪些直觉上合理的方法在当前任务里没有跑通”。这种负结果既能体现实验设计的完整性，也能防止读者误以为作者只挑有利结果汇报。对应证据是 `m02 -> m05` 基本不变、`m07` 和 `m09` 也未产生净增益，以及 `m11` 到 `m15` 中 coverage 与 EM 的系统性背离。（证据：`TABLE_MAIN` 第4行、第7行；`TABLE_ABLATION` 第4、6行；`TABLE_NUMERIC` 第13-17行；run_id=`...m02`、`...m05`、`...m07`、`...m09`、`...m11`、`...m12`、`...m13`、`...m15`）

第三层是只能进入讨论与后续工作的内容，即组合模块 C。原因不是它完全没有信号，而是它目前只有交互信号，没有闭环信号。`m12 -> m20` 的 coverage 上升是真实现象，但 EM 下降同样是真实现象；supplemental comboC 审计还进一步表明，A-only 与 C-full 都没有转化成更高质量的数值答案。因此，这部分最适合被写成“下一阶段应重点修复的接口”，而不是“当前阶段已完成的创新”。（证据：`TABLE_NUMERIC` 第14、22行；`docs/SEAL_CHECK_comboC.md`；run_id=`...m12`、`...m20`）

## 6. 组合模块 C 与“不是叠加幻觉”的判定

组合模块 C 在当前报告里的定义是：A = PQE，B = calculator，C = PQE + calculator。需要强调的是，这里讨论的不是“理论上 A+B 应该更强”，而是“在当前 seal 与 supplemental audit 下，A、B、C 是否形成了可验证的闭环结果”。结论很明确：当前只有交互，没有闭环。

先看当前 seal 里的 `m12 -> m20`。`m12` 是 calculator 主 baseline，`m20` 是 PQE + calculator。结果上，`num_cov` 从 `0.6695` 升到 `0.6867`，说明 retrieval-side 的改进确实让更多 numeric queries 拿到了可覆盖答案；但 `num_em` 从 `0.3197` 降到 `0.3079`，说明这部分新增覆盖并没有转化为更可靠的最终数值结果。也就是说，A 的确把更多样本送到了 answer-side，但 B 还没有把这些新增样本处理好，所以 C 只呈现出“coverage 上升”的交互，而没有形成“EM 与 coverage 同步受益”的闭环。（证据：`TABLE_NUMERIC` 第14行与第22行；run_id=`...m12`、`...m20`）

如果只看这一步，读者可能会怀疑：是不是 A 与 B 的叠加方式不对，或者当前 C 只是没有调好？为避免这种“叠加幻觉”，仓库还保留了本地 supplemental `comboC` 审计矩阵。这个 mini-matrix 把 A-only、B-only、C-full 明确拆开：baseline `num_em=0.3079 / cov=0.6867`，A-only 变成 `0.1416 / 0.7597`，B-only 与 baseline 基本一致，C-full 则是 `0.1329 / 0.7554`。换言之，A-only 与 C-full 都出现了“coverage 换 EM”的结构，而 B-only 没有带来额外收益。这一补充证据说明：当前 C 的问题不是“叠加后被别的模块掩盖”，而是 A 和 B 之间的接口本身还不能稳定收敛到更高质量的 numeric answer。（补充证据：`docs/SEAL_CHECK_comboC.md`；`outputs/20260228_012006_b44483/.../summary.json`，本地审计补充）

因此，本报告对组合模块 C 的写法必须非常明确：当前不存在正向闭环证据。更准确的说法是，“本轮 seal 已证明 retrieval-side 改进会改变 numeric coverage，但尚未证明该交互能形成稳定的最终数值质量提升”。这并不是坏消息，而是一个很具体的后续研究入口：如果下一轮要继续做 C，重点不该再放在“是否增加更多 calculator task types”，而应放在 route policy、fact filtering、task parsing 与 calculator-used path 的质量 gap 上。

## 7. Baseline 文献对齐

文献映射的作用不是装饰相关工作，而是把仓库中的每个 baseline family 放回公开研究语境里，说明它为何是合理对照、为何不是拍脑袋加的模块。

### 表 3 Baseline 文献映射表

| 模块 family | 代表文献 | DOI | 仓库绑定 |
| --- | --- | --- | --- |
| RAG 基础 | Lewis et al., 2020, NeurIPS | 官方 proceedings 未列 DOI | `m02`、`m18`、`m20` |
| RAG Survey | Chen et al., 2024, KnowLLM | `10.18653/v1/2024.knowllm-1.5` | 全链路 |
| BM25 | Robertson & Zaragoza, 2009 | `10.1561/1500000019` | `m03` |
| PRF / query expansion | Li et al., 2018, SIGIR | `10.1145/3209978.3210063` | `m18`、`m19` |
| Dense dual-encoder | Karpukhin et al., 2020, EMNLP | `10.18653/v1/2020.emnlp-main.550` | `m01`、`m02` |
| Sentence-BERT | Reimers & Gurevych, 2019 | `10.18653/v1/D19-1410` | `m01`、`configs/train_retriever.yaml` |
| Hybrid retrieval | Cormack et al., 2009 / Dikkala et al., 2023 | `10.1145/1571941.1572114` / `10.18653/v1/2023.findings-acl.679` | `m04` |
| Multi-step retrieval | Feldman & El-Yaniv, 2019 | `10.18653/v1/P19-1222` | `m05`、`m07`、`m09` |
| Numeric QA | Ran et al., 2019 | `10.18653/v1/D19-1251` | `m11`-`m15` |
| Finance numeric QA | Zhu et al., 2021 | `10.18653/v1/2021.acl-long.254` | `m12`、`m20` |
| Tool-augmented QA | Gemmell et al., 2023 | `10.18653/v1/2023.findings-emnlp.281` | `m20` |

这张映射表的核心价值在于，它把“为什么有 `m03`、为什么有 `m04`、为什么还要保留 multistep baseline、为什么 PQE 可以视为 query expansion family、为什么 calculator 可以借 numeric QA / tool-augmented QA 家族来定位”一次性说清楚。这样，论文方法章与实验章就不需要重复证明“这个 baseline 合理吗”，而是可以直接讨论“这个 baseline 在本任务中效果如何”。

## 8. 复现与封装

当前仓库已经具备可冻结的封装边界。标准 seal 入口固定为四个命令：先 `smoke`，再 `run_matrix_step6`，再 `make_tables`，最后 `plot_all`。这四步的输出分别承担不同职责：`smoke` 证明环境可运行；`matrix` 产出 run 级结果；`make_tables` 把 run 汇总成 commit-safe 表；`plot_all` 把 seal 结果转成论文图表。封条规则要求不要把 Makefile 的非 seal 默认目标误当成唯一事实源，因此论文复现章节应直接写 canonical seal commands，而不是笼统写“执行 Makefile”。

### 表 4 复现 / 封装清单表

| 命令 | 产物 | 路径 | 用途 |
| --- | --- | --- | --- |
| `python scripts/smoke.py --config configs/smoke.yaml --run-id seal_final_smoke` | smoke metrics / logs | `outputs/seal_final_smoke/**` | 环境自检 |
| `python scripts/run_matrix_step6.py --base-config configs/step6_base.yaml --matrix configs/step6_matrix_seal.yaml` | 20 个 seal runs | `outputs/20260228_055920_06d6bb/**` | 主实验 |
| `python scripts/make_tables.py --experiments configs/step6_experiments_seal.yaml` | 主表、数值表、消融表 | `docs/TABLE_MAIN.md`、`docs/TABLE_NUMERIC.md`、`docs/TABLE_ABLATION.md` | commit-safe 汇总 |
| `python scripts/plot_all.py --config scripts/plot_config.yaml` | seal 图表 | `thesis/figures_seal/**` | 论文图表 |

需要特别披露的是：`outputs/` 不入仓，因此本地审计文件不能替代 commit-safe 文档。正确的复现叙事应当是：先用 `docs/TABLE_*` 与 `docs/SEAL_*` 锁定正式结论，再根据需要下钻到 `outputs/**` 日志与 per-run summary。对论文来说，这种设计反而是优势，因为它区分了“正式发表表面”和“本地运行现场”。

图表封装方面，当前启用图只有 `main_results` 和 `ablation_breakdown`，并且 `plot_has_data_false_count=0`。这意味着图表流程已经达到“可以随 freeze 一起交付”的程度，但也意味着很多更适合论文叙事的图还需要基于现有 `TABLE_*` 与本地 JSON 再规划，而不是直接依赖当前 `plot_all.py` 的默认输出。

从复现哲学上看，当前仓库采用的是一种“文档先于大目录产物”的封装方式。传统实验仓库往往把可信度寄托在完整的 `outputs/` 目录上，但这会导致远端仓库臃肿、难以审阅，也不利于长期冻结。当前项目反过来做：正式结论先被压缩成 `docs/TABLE_*`、`docs/SEAL_*` 与 `thesis/figures_seal/**`，而 `outputs/**` 只在本地作为现场审计材料存在。这样一来，读者先看到的是已经冻结、可提交、可引用的表面；只有在需要核查细节时，才下钻到本地 artifacts。对论文写作而言，这种分层正好匹配“正文展示结论、附录展示审计”的结构。

Makefile 对齐也是封装里容易被忽视的一环。由于默认 target 历史上可能仍指向非 seal 配置，因此本轮 freeze 特别强调 canonical seal commands 与 seal targets 的存在。它的意义不是“多写几个命令别名”，而是防止未来复现实验时误用旧矩阵、旧 experiments 或旧 plot 配置，导致表格和图表虽然能生成，但不再对应当前冻结结论。也就是说，封装不仅是把结果保存下来，更是把“正确的再生产路径”一并固定下来。

## 9. 讨论、局限与后续工作

第一，当前项目最强的部分是 retrieval side，而不是 answer-side reasoning。Retriever FT 与 PQE replacement 说明，复杂金融查询在本轮首先受益于“更好的召回”和“更好的 query reformulation”，而不是“更复杂的 answer tool”。这与许多金融场景的直觉相符：在回答之前，先把对的年份、对的公司、对的段落找回来，收益往往大于在错误证据上做更复杂计算。

第二，multistep 的负结论不应被误解为“多步检索理论无效”。更准确的解释是：在当前实现、当前 query 分布和当前 gate 设计下，它没有带来可观测的净收益。它依然是合理 baseline，因为它帮助我们证明“不是所有看上去更复杂的检索策略都会自动变好”，并为 PQE 的替代价值提供了明确背景。

第三，calculator 的失败不是因为数值问答本身不重要，而是因为当前 answer-side route 质量还不足以支撑闭环。现有 evidence 已经把问题收敛到两个方向：task dispatch 与 fact selection。如果后续还有一个里程碑，我认为最值得做的不是继续给 calculator 加更多 task types，而是针对 `gate_task`、`calc_used`、`fallback` 三条路径重新设计路由质量控制。

第四，子集口径仍有一项工程尾巴。`subsets_v2` 已形成统计与文档，但当前 resolved config 还没有完全切换。这个问题目前还不足以推翻 `m01 -> m02`、`m02 -> m18` 等相对改善结论，但如果论文答辩阶段要进一步强调复杂子集的定义，就应该优先完成这一步路径对齐。

第五，里程碑报告的写作策略也需要与证据状态对齐。当前最适合被突出为“方法贡献”的，其实不是“我们做了很多模块”，而是“我们把复杂金融查询的有效增益稳定收敛到了 retrieval side，并用系统消融把无效路径排除掉”。这种写法比逐个罗列模块更强，因为它呈现的是一个经过实验筛选后的系统认识：先做领域适配检索器，再做对复杂 query 有针对性的扩展，最后才讨论数值链路。对于读者而言，这比“多步检索 + calculator + 组合模块”并列陈述更容易理解，也更符合现有证据强弱。

第六，下一阶段如果资源有限，优先级其实已经很清楚。第一优先级是把 `subsets_v2` 路径正式接入 seal base config，消除 complex/abbrev/numeric 的口径漂移风险；第二优先级是在 numeric route 上补更细的 path diagnostics，尤其是 `calc_used` 与 `fallback` 的事实质量差异；第三优先级才是决定是否继续投资组合模块 C。因为没有前两步，C 即使继续调参，也大概率仍然停留在“coverage 改善但 EM 不闭环”的状态。换言之，当前证据已经不仅告诉我们“哪里有效”，也告诉我们“下一轮最该把时间花在哪里”。

## 10. 结论

如果把本轮项目压缩成一句话，可以这样写：当前工程已经把复杂金融查询的主增益稳定地封装在 retrieval 侧，其中 Retriever FT 是强结论，dense mode 是唯一稳定模式，PQE 是对 multistep 的有效替代；而 calculator 与组合模块 C 目前只形成了诊断与交互证据，尚未形成可写成正向主结论的数值闭环。

如果把它再展开一点，则是：第一，系统已经具备冻结所需的工程条件，包括 canonical seal commands、commit-safe 表格、可交付图表与完整的 run 级审计；第二，retrieval FT 和 PQE 共同构成当前论文最可靠的方法主线；第三，multistep 与 calculator 的负结论同样有价值，因为它们把“什么有效、什么暂时无效”划分得足够清楚，使后续论文陈述能够站在真实证据上，而不是站在初始设想上。

## 11. 缺证据项清单

无。
