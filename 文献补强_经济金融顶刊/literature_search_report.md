# 经济金融文献补强检索报告

## 检索目标

本次检索服务于本科毕业论文开题报告《面向复杂金融查询的检索增强问答系统研究——基于领域化稠密检索与年份感知查询扩展的协同优化》。阶段目标不是修改论文正文，而是在不改变 RAG、领域化稠密检索、年份感知查询扩展和数值工具链这一技术主线的前提下，补充经济学、金融学、管理学、会计学和统计学方向的文献依据。

重点回答三个问题：

1. 为什么 10-K、年报、MD&A、风险因素、财务报表和财经新闻等金融文本在金融学中重要。
2. 为什么金融文本处理存在信息获取成本、注意力约束、披露复杂性、年份口径和数值可靠性问题。
3. 为什么 RAG、领域化检索、年份对齐和可审计答案可以被表述为金融信息处理基础设施，而不只是一个技术系统。

## 已读取的论文材料

已读取并提炼以下本地材料：

- `报告/开题报告_石延斌_U202216405_题目_2026年3月11日.pdf`
- `docs/TABLE_MAIN.md`
- `docs/TABLE_NUMERIC.md`
- `docs/BASELINE_LITERATURE_MAP.md`

从开题报告和工程文件中提炼出的研究对象为：面向复杂金融查询的检索增强问答系统，主要处理长篇金融披露文本和金融 QA 场景。论文关注短查询、缩写、金融术语、跨年份比较、同比/差额计算、单位口径、证据定位和答案可审计性。实验主线包括领域化稠密检索、BM25/混合检索、年份感知查询扩展、多步检索和数值计算门控。

## 检索时间

- 检索日期：2026-04-26
- 时区：Asia/Shanghai
- 检索范围：公开可访问的期刊官网、出版社页面、SSRN、NBER/作者主页、高校主页、OpenAlex/CoLab、RePEc/IDEAS/EconPapers、期刊目录页和可公开访问的中文期刊页面。

## 检索关键词

### 中文关键词

金融文本分析、年报文本分析、信息披露质量、管理层讨论与分析、风险因素披露、金融科技、人工智能与金融、大语言模型与金融、生成式人工智能与金融、智能投研、金融信息处理、信息不对称、投资者注意力、文本复杂性、资本市场信息效率、企业公告文本、监管科技、机器学习与金融、自然语言处理与金融、金融问答、数值推理、财务报表文本、中文金融文本情绪、年报大数据应用。

### 英文关键词

financial textual analysis, annual report textual analysis, 10-K textual analysis, MD&A disclosure, risk factor disclosure, corporate disclosure, disclosure quality, financial information processing, investor attention, information acquisition cost, information asymmetry, market efficiency, fintech, AI in finance, machine learning in finance, natural language processing in finance, large language models in finance, generative AI in finance, financial question answering, financial document analysis, financial statement analysis, numerical reasoning in finance, retrieval augmented generation finance, financial disclosure and AI, automated financial analysis, analyst information processing, SEC filings machine learning, textual complexity finance.

### 期刊名组合检索

使用了“期刊名 + 关键词”的组合检索，包括但不限于：

- Review of Financial Studies + corporate disclosure + AI
- Journal of Finance + 10-K + textual analysis
- Journal of Financial Economics + artificial intelligence + finance
- Management Science + disclosure sentiment + machine learning
- Contemporary Accounting Research + FinBERT / textual analysis
- The Accounting Review + risk factor disclosure
- 管理世界 + 金融文本 + 文本情绪 + 机器学习
- 经济研究 + 年报文本分析 + 大数据应用
- 经济学（季刊）+ 文本大数据 + 金融学

## 检索数据库 / 网站

已使用或核验过的主要来源：

- Oxford Academic / Society for Financial Studies
- Wiley Online Library / American Finance Association
- Elsevier ScienceDirect
- INFORMS PubsOnline
- Springer Link
- American Accounting Association 页面及 Crossref/二级索引
- SSRN
- RePEc / IDEAS / EconPapers
- CoLab / OpenAlex 衍生页面
- Semantic Scholar / CiNii / 高校研究门户
- 《管理世界》中国知网页面
- 北京大学国家发展研究院、北京大学数字金融研究中心页面
- 南开大学金融学院新闻页面

未使用盗版数据库，未绕过数据库权限，未下载受限全文。

## 已覆盖的指定期刊

### 中文指定期刊

- 《经济研究》：发现并核验到与年报文本和大数据应用相关文献。
- 《经济学（季刊）》：发现并核验到中文文本大数据在经济学和金融学中的综述文献。
- 《管理世界》：发现并核验到中文金融文本信息含量与混合式情绪测度文献。
- 《中国社会科学》：公开检索中未发现与本文主题直接匹配、且可核验到题录细节的近 3-5 年文献。

### 英文指定期刊

已覆盖并纳入候选的指定期刊包括：

- Review of Financial Studies
- Journal of Finance
- Journal of Financial Economics
- Quarterly Journal of Economics

未发现与本文主题直接高度相关、且近 3-5 年公开可核验的候选文献的指定期刊包括：American Economic Review、Econometrica、Journal of Political Economy、Review of Economic Studies、AEJ 系列、Annals of Statistics、Journal of Econometrics、Journal of Economic Theory、Journal of the Royal Statistical Society: Series B 等。这些期刊更多提供一般经济理论、统计方法或 AI 劳动经济学背景，直接涉及金融披露文本、10-K、金融文本问答和可审计金融 AI 的文献较少。

## 检索策略

1. 先从开题报告中提取金融场景：10-K、年报、MD&A、风险因素、财务指标、年份约束、数值计算、证据定位。
2. 再按“金融文本是否具有资本市场信息含量”“披露文本是否增加信息处理成本”“AI/ML/NLP 是否能降低信息处理成本”“LLM 是否改变金融分析”的逻辑线索检索。
3. 对候选文献核验作者、年份、题名、期刊、卷期页码、DOI 或官方链接。
4. 优先保留能直接支撑论文研究意义、文献综述、理论依据和方法合理性的文献。
5. 对中文文献中 DOI、页码或官网记录不完整的条目，在表格中标注“待核验”或“不建议直接加入最终参考文献”。

## 发现的主要文献方向

1. **金融披露文本具有信息含量**：10-K 语调、可读性、措辞变化、风险因素披露、MD&A 修改、财经新闻文本均能影响或预测市场反应。
2. **披露复杂性与信息处理成本**：年报和 10-K 的文本长度、可读性、样板化风险因素会影响投资者尤其是中小投资者的信息处理和交易行为。
3. **金融领域 NLP/ML 的必要性**：通用词典和通用语言模型在金融文本中存在误分类或领域语义偏差，领域化模型和机器学习方法能提升披露情绪、风险类型和文本信息提取质量。
4. **AI 读者正在改变公司披露**：机器下载、AI 投资者和算法读者会改变公司披露文本的可机器读取性与语言策略。
5. **LLM 与生成式 AI 正在进入金融分析**：LLM 可用于新闻回报预测、财务报表分析和金融文本理解，但需要透明、可解释、可审计和可追溯机制。
6. **中文金融文本研究已有经管基础**：中文金融文本情绪、年报文本大数据应用和文本大数据综述可支撑本论文的中文经管学科归属。

## 文献筛选原则

- A 级：直接涉及金融文本、公司披露、10-K/年报/风险因素、金融 NLP/ML/LLM、文本信息含量、投资者信息处理或可审计金融分析，建议优先引用。
- B 级：能支撑金融信息不对称、披露监管、金融科技、AI 改变知识生产或市场效率等背景，建议选择性引用。
- C 级：权威但与本文主题连接较弱，只作为备选或方法背景，不建议大量加入。

## 不确定项说明

1. 中文期刊官网公开检索能力有限，部分《经济研究》条目主要通过作者主页、数据平台引用和第三方题录核验。最终写入正文参考文献前，建议再用 CNKI、万方、维普或学校图书馆核验 DOI、页码和题名标点。
2. Kim, Muhn and Nikolaev (2024) 与 Lopez-Lira and Tang (2023/2025) 属于 SSRN/working paper，不应写成经管顶刊论文；可作为“扩展参考”引用。
3. 2021 年以来直接研究“RAG + 金融披露问答”的经管顶刊论文非常少，因此本文应把 RAG 表述为解决金融披露文本信息处理成本和可审计性问题的技术路径，而不是声称经管顶刊已有相同技术路线。
4. 部分基础经典文献早于 2021 年，但它们是金融文本分析、披露复杂性和 10-K 信息含量研究的基础，不宜完全排除。

