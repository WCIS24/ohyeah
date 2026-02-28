# Baseline Literature Map

- Verified on: `2026-02-28`
- Verification policy: DOI and access links were checked against official venue pages when available (`ACL Anthology`, `NeurIPS Proceedings`, `DOI resolver`, `Now Publishers`, `ACM DL`/official DOI pages).
- Scope: this file maps baseline-paper families to the current seal matrix, so later thesis text can cite both literature and repository evidence together.
- Important note: some seminal papers, especially `NeurIPS` proceedings entries, do not expose a DOI on the official proceedings page. In those cases the entry is marked as `no DOI listed on official page`, not as a network failure.

## Seal Run Shorthand

| Short | Label | Full run_id | Main use in this map |
| --- | --- | --- | --- |
| `m01` | `seal_mvp01_preft_dense_singlestep` | `20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m01` | pre-FT dense baseline |
| `m02` | `seal_mvp02_dense_singlestep` | `20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m02` | post-FT dense baseline |
| `m03` | `seal_mvp03_bm25_singlestep` | `20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m03` | lexical BM25 baseline |
| `m04` | `seal_mvp04_hybrid_singlestep` | `20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m04` | hybrid retrieval baseline |
| `m05` | `seal_mvp05_dense_multistep` | `20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m05` | multistep baseline |
| `m07` | `seal_mvp05b_dense_multistep_gate_open` | `20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m07` | multistep gate-open ablation |
| `m09` | `seal_mvp05c_dense_multistep_gate_disabled` | `20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m09` | multistep gate-disabled ablation |
| `m12` | `seal_mvp08_dense_calc_allow_yoy_diff` | `20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m12` | main calculator baseline |
| `m18` | `seal_mvp11_dense_pqe` | `20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m18` | PQE replacement |
| `m19` | `seal_mvp12_dense_pqe_abbrev_only` | `20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m19` | PQE ablation |
| `m20` | `seal_mvp13_dense_pqe_calc` | `20260228_055920_06d6bb/runs/20260228_055920_06d6bb_m20` | PQE + calculator combination |

## 1. RAG Foundation

| Role | Verified reference | DOI + accessible link | Repo binding | Thesis-ready wording |
| --- | --- | --- | --- | --- |
| Classic | Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Kuttler, Mike Lewis, Wen-tau Yih, Tim Rocktaschel, Sebastian Riedel, Douwe Kiela (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks*. NeurIPS 2020. | DOI: no DOI listed on official NeurIPS proceedings page. Link: <https://proceedings.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html> | Family-level mapping for the whole retrieve-then-answer pipeline. In this repo the closest seal realizations are `m02` (retrieval baseline), `m18` (retrieval-side replacement), and `m20` (retrieval + answer module). Module keys: `retriever.*`, `qexpand.*`, `calculator.*`. | 中文：本文整体采用 retrieval-augmented 的系统范式，seal 主链可视为面向金融查询的 retrieve-then-answer 实现；其中 `m02/m18/m20` 分别对应基础检索、检索增强和检索+工具交互三种层级。 English: Our system follows a retrieval-augmented pipeline, with `m02/m18/m20` instantiating baseline retrieval, retrieval-side enhancement, and retrieval-plus-tool interaction. |
| Recent | Wenhu Chen, Hexuan Hu, Xi Chen, Pat Verga, William W. Cohen (2024). *Retrieval-Augmented Knowledge Integration into Language Models: A Survey*. Proceedings of the 1st Workshop on Knowledgeable Language Models (KnowLLM 2024). | DOI: `10.18653/v1/2024.knowllm-1.5`. DOI link: <https://doi.org/10.18653/v1/2024.knowllm-1.5>. Official link: <https://aclanthology.org/2024.knowllm-1.5/> | Same family-level mapping as above; use when describing the architecture as a modular retrieval-augmented pipeline rather than a single model. Best tied to `m02`, `m18`, `m20` and `docs/MILESTONE_EVIDENCE_MAP.md`. | 中文：后文将该系统表述为模块化 retrieval-augmented pipeline，而非单一生成模型；这一写法与 Chen et al. (2024) 对 RAG 组件化结构的总结一致。 English: We describe the system as a modular retrieval-augmented pipeline, following the componentized view summarized by Chen et al. (2024). |

## 2. BM25 / PRF / Query Expansion

| Role | Verified reference | DOI + accessible link | Repo binding | Thesis-ready wording |
| --- | --- | --- | --- | --- |
| Classic | Stephen Robertson, Hugo Zaragoza (2009). *The Probabilistic Relevance Framework: BM25 and Beyond*. Foundations and Trends in Information Retrieval, 3(4):333-389. | DOI: `10.1561/1500000019`. DOI link: <https://doi.org/10.1561/1500000019> | Lexical baseline family. In this repo, direct binding is `m03` (`retriever.mode=bm25`) against `m02` dense and `m04` hybrid. Also serves as the classical lexical anchor for later PQE discussion. | 中文：我们将 `m03` 作为标准 BM25 词法检索基线，其理论背景可追溯到 Robertson and Zaragoza (2009) 所总结的 BM25 概率相关性框架。 English: We treat `m03` as the lexical BM25 baseline, grounded in the probabilistic relevance framework summarized by Robertson and Zaragoza (2009). |
| Recent PRF | Canjia Li, Andrew Yates, Sean MacAvaney, Ben He, Nazli Goharian (2018). *NPRF: A Neural Pseudo Relevance Feedback Framework for Ad-hoc Information Retrieval*. SIGIR 2018, pages 879-882. | DOI: `10.1145/3209978.3210063`. DOI link: <https://doi.org/10.1145/3209978.3210063> | Family-level justification for feedback-style query reformulation. In this repo, the closest mapping is PQE: `m02` -> `m18`, with `m19` isolating `qexpand.abbrev.enabled=true` and `qexpand.prf_year.enabled=false`. | 中文：虽然本仓库没有直接复现 neural PRF，但 `m18` 的 `qexpand.prf_year` 逻辑属于“由初始检索结果反哺查询”的轻量反馈式扩展，和 PRF 家族在思想上同源。 English: While we do not directly reproduce neural PRF, the `qexpand.prf_year` path in `m18` is a lightweight feedback-style query reformulation in the same family. |

## 3. Dense Retrieval / Dual-Encoder

| Role | Verified reference | DOI + accessible link | Repo binding | Thesis-ready wording |
| --- | --- | --- | --- | --- |
| Classic | Vladimir Karpukhin, Barlas Oguz, Sewon Min, Patrick Lewis, Ledell Wu, Sergey Edunov, Danqi Chen, Wen-tau Yih (2020). *Dense Passage Retrieval for Open-Domain Question Answering*. EMNLP 2020, pages 6769-6781. | DOI: `10.18653/v1/2020.emnlp-main.550`. DOI link: <https://doi.org/10.18653/v1/2020.emnlp-main.550>. Official link: <https://aclanthology.org/2020.emnlp-main.550/> | Direct mapping to the dense retriever family. In the seal matrix this is `m01` (pre-FT dense) vs `m02` (post-FT dense), both under `retriever.mode=dense`. | 中文：`m01 -> m02` 的主对照可以视为标准 dual-encoder dense retrieval 在领域数据上的微调增益，对应 DPR 一类方法的实验范式。 English: The `m01 -> m02` contrast instantiates the standard dual-encoder dense retrieval recipe, analogous to DPR-style fine-tuning. |
| Recent | Luyu Gao, Jamie Callan (2022). *Unsupervised Corpus Aware Language Model Pre-training for Dense Passage Retrieval*. ACL 2022, pages 2843-2853. | DOI: `10.18653/v1/2022.acl-long.199`. DOI link: <https://doi.org/10.18653/v1/2022.acl-long.199>. Official link: <https://aclanthology.org/2022.acl-long.199/> | Use as a recent dense-retrieval reference when explaining why domain-sensitive pretraining / fine-tuning matters for `m02`. Repo binding remains `m01` vs `m02` and the FT model path `models/retriever_ft/20260203_005729_cd195e`. | 中文：本文不重新设计 dense encoder 结构，而是在既有句向量模型上做领域适配；这一写法可与 Gao and Callan (2022) 所强调的 corpus-aware dense retrieval 改进并列讨论。 English: Rather than inventing a new dense encoder, we perform domain adaptation on top of an existing sentence encoder, in line with corpus-aware dense retrieval improvements such as Gao and Callan (2022). |

## 4. Sentence-BERT / Sentence-Transformers Family

| Role | Verified reference | DOI + accessible link | Repo binding | Thesis-ready wording |
| --- | --- | --- | --- | --- |
| Classic | Nils Reimers, Iryna Gurevych (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks*. EMNLP-IJCNLP 2019, pages 3982-3992. | DOI: `10.18653/v1/D19-1410`. DOI link: <https://doi.org/10.18653/v1/D19-1410>. Official link: <https://aclanthology.org/D19-1410/> | Direct mapping to the base encoder family used in the repo. `configs/train_retriever.yaml` starts from `sentence-transformers/all-MiniLM-L6-v2`; seal `m01` also explicitly uses `sentence-transformers/all-MiniLM-L6-v2` before FT. | 中文：本文的检索器并非从零训练，而是建立在 sentence-transformers 生态的句向量编码器之上，这与 Sentence-BERT 的双塔句向量范式一致。 English: Our retriever is built on a sentence-transformers encoder rather than trained from scratch, matching the Siamese sentence-embedding paradigm introduced by Sentence-BERT. |
| Recent | Kexin Wang, Nils Reimers, Iryna Gurevych (2021). *TSDAE: Using Transformer-based Sequential Denoising Auto-Encoder for Unsupervised Sentence Embedding Learning*. Findings of EMNLP 2021, pages 671-688. | DOI: `10.18653/v1/2021.findings-emnlp.59`. DOI link: <https://doi.org/10.18653/v1/2021.findings-emnlp.59>. Official link: <https://aclanthology.org/2021.findings-emnlp.59/> | Use as a recent sentence-transformers-family reference when explaining why a pre-existing sentence encoder can be a reasonable starting point before domain FT. Repo binding: `configs/train_retriever.yaml`, `m01`, and the `m01 -> m02` FT jump. | 中文：在实现层面，我们采用“先用通用句向量模型初始化，再做领域微调”的路线；TSDAE 提供了这一句向量预训练路线的近年代表。 English: Implementation-wise, we initialize from a general-purpose sentence encoder and then fine-tune in-domain; TSDAE is a representative recent reference for this sentence-embedding pretraining line. |

## 5. Hybrid Retrieval / Fusion

| Role | Verified reference | DOI + accessible link | Repo binding | Thesis-ready wording |
| --- | --- | --- | --- | --- |
| Classic | Gordon V. Cormack, Charles L. A. Clarke, Stefan Buettcher (2009). *Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods*. SIGIR 2009, pages 758-759. | DOI: `10.1145/1571941.1572114`. DOI link: <https://doi.org/10.1145/1571941.1572114> | Family-level fusion background. In this repo, direct experimental binding is `m04` (`retriever.mode=hybrid`, `retriever.hybrid.alpha=0.5`) against `m02` dense and `m03` bm25. | 中文：`m04` 的 hybrid 检索属于“融合词法与稠密信号”的 family；虽然实现上是 alpha 加权而不是 RRF，但其研究问题与经典 fusion 文献一致。 English: `m04` belongs to the family of methods that combine sparse and dense signals; our implementation uses alpha-weighted fusion rather than RRF, but the research question is the same. |
| Recent | Nishanth Dikkala, Nikhil Gollapudi, Sri Harsha Dumpala, Chandra Khatri, Siva Reddy (2023). *Hybrid Hierarchical Retrieval for Open-Domain Question Answering*. Findings of ACL 2023, pages 7791-7801. | DOI: `10.18653/v1/2023.findings-acl.679`. DOI link: <https://doi.org/10.18653/v1/2023.findings-acl.679>. Official link: <https://aclanthology.org/2023.findings-acl.679/> | Use when motivating the hybrid family even though the current seal result is negative relative to dense. Repo binding: `m04` vs `m02` and `m03`. | 中文：尽管本仓库中 `m04` 未超过纯 dense 的 `m02`，但 hybrid retrieval 仍然是有充分文献依据的标准对照 family，因此应保留为消融基线。 English: Even though `m04` does not beat pure dense `m02` in our seal matrix, hybrid retrieval remains a literature-backed baseline family and should be retained as an ablation. |

## 6. Multi-step / Iterative Retrieval

| Role | Verified reference | DOI + accessible link | Repo binding | Thesis-ready wording |
| --- | --- | --- | --- | --- |
| Classic | Matthew Feldman, Ran El-Yaniv (2019). *Multi-Hop Paragraph Retrieval for Open-Domain Question Answering*. ACL 2019, pages 2296-2309. | DOI: `10.18653/v1/P19-1222`. DOI link: <https://doi.org/10.18653/v1/P19-1222>. Official link: <https://aclanthology.org/P19-1222/> | Direct baseline-family reference for the multistep branch. Repo binding: `m05` vs `m02`, plus `m07` and `m09` as gate ablations under `multistep.*`. | 中文：`m05/m07/m09` 所代表的是典型 iterative retrieval family，即通过多轮检索逐步补齐证据链。 English: `m05/m07/m09` instantiate a standard iterative retrieval family, where evidence is accumulated through multiple retrieval rounds. |
| Companion classic | Haitian Sun, Tania Bedrax-Weiss, William W. Cohen (2019). *PullNet: Open Domain Question Answering with Iterative Retrieval on Knowledge Bases and Text*. EMNLP-IJCNLP 2019, pages 2380-2390. | DOI: `10.18653/v1/D19-1242`. DOI link: <https://doi.org/10.18653/v1/D19-1242>. Official link: <https://aclanthology.org/D19-1242/> | Use when discussing why multistep was initially included as a reasonable baseline. Repo binding remains the same: `m05` primary multistep, `m07` gate-open, `m09` gate-disabled. | 中文：即便本轮 seal 中 multistep 未产生净增益，它最初仍是合理的 baseline，因为 PullNet 一类工作已经证明 iterative retrieval 在复杂 QA 中有代表性。 English: Even though multistep is not a net-positive module in this seal cycle, it was a reasonable baseline choice because PullNet-style work established iterative retrieval as a representative QA strategy. |

## 7. Numeric QA / Tool-Augmented QA

| Role | Verified reference | DOI + accessible link | Repo binding | Thesis-ready wording |
| --- | --- | --- | --- | --- |
| Classic numeric QA | Qiu Ran, Yankai Lin, Peng Li, Jie Zhou, Zhiyuan Liu (2019). *NumNet: Machine Reading Comprehension with Numerical Reasoning*. EMNLP-IJCNLP 2019, pages 2474-2484. | DOI: `10.18653/v1/D19-1251`. DOI link: <https://doi.org/10.18653/v1/D19-1251>. Official link: <https://aclanthology.org/D19-1251/> | Numeric reasoning family reference for the calculator path. Repo binding: `m11`, `m12`, `m13`, `m15`, and the combination run `m20`. | 中文：calculator 分支属于 numerical reasoning / numeric QA family；从 `m11` 到 `m15` 的对照，可被理解为在真实系统中测试数值推理模块的可用性边界。 English: The calculator branch belongs to the numerical reasoning / numeric QA family; runs `m11` to `m15` test the practical operating boundary of such a module in a live pipeline. |
| Finance-oriented benchmark | Fengbin Zhu, Wenhao Jiao, Yichi Zhang, Dian Yu, Sira Ispir, Yu Li, Yang Wang, Xipeng Qiu, Ming Zhou, Jie Tang (2021). *TAT-QA: A Question Answering Benchmark on a Hybrid of Tabular and Textual Content in Finance*. ACL-IJCNLP 2021, pages 3277-3287. | DOI: `10.18653/v1/2021.acl-long.254`. DOI link: <https://doi.org/10.18653/v1/2021.acl-long.254>. Official link: <https://aclanthology.org/2021.acl-long.254/> | Strong topical match for the repo's finance-oriented numeric questions. Bind to `m12` as the main calculator baseline and `m20` as the retrieval-plus-calculator interaction run. | 中文：由于本文任务场景本身带有金融数值问答特征，TAT-QA 可以作为 calculator 与组合模块 `m20` 的最近邻 benchmark family。 English: Because our task has a finance-oriented numerical QA flavor, TAT-QA is a close benchmark family for discussing the calculator baseline `m12` and the combination run `m20`. |
| Recent tool-augmented QA | Nicholas Gemmell, Ben Heald, Binjie Wang, Hamish Ivison, Kristian Georgiev, Jakob Uszkoreit, Maarten Sap, Yejin Choi (2023). *ToolWriter: Connecting Large Language Models to Tools via Reinforcement Learning*. Findings of EMNLP 2023, pages 4186-4199. | DOI: `10.18653/v1/2023.findings-emnlp.281`. DOI link: <https://doi.org/10.18653/v1/2023.findings-emnlp.281>. Official link: <https://aclanthology.org/2023.findings-emnlp.281/> | Tool-use family reference for `calculator.*` and the combination path `m20`. The implementation differs: this repo uses a symbolic numeric tool rather than RL-trained tool selection, but the family-level question is the same. | 中文：尽管本仓库中的 calculator 不是通过 RL 训练的工具选择器，它仍属于“外部工具被条件触发以辅助回答”的 tool-augmented QA family，尤其对应 `m20`。 English: Although our calculator is not an RL-trained tool selector, it still belongs to the tool-augmented QA family in which an external tool is conditionally invoked, especially in `m20`. |

## Repository Anchor Summary

- Base sentence encoder:
  `configs/train_retriever.yaml:3` -> `sentence-transformers/all-MiniLM-L6-v2`
- Pre-FT dense baseline:
  `configs/step6_matrix_seal.yaml:5`
- Post-FT dense retriever:
  `configs/step6_matrix_seal.yaml:14`
- BM25 baseline:
  `configs/step6_matrix_seal.yaml:24`
- Hybrid baseline:
  `configs/step6_matrix_seal.yaml:33`
- Multistep branch:
  `configs/step6_matrix_seal.yaml:43`, `57`, `71`, `85`, `99`, `114`
- Calculator branch:
  `configs/step6_matrix_seal.yaml:130`, `140`, `150`, `161`, `171`
- PQE replacement:
  `configs/step6_matrix_seal.yaml:214`, `228`, `244`

## Writing Guidance

- When writing the method section, use the family references above to justify why each branch is a valid baseline family even when the final seal conclusion is negative.
- When writing the results section, always tie the literature family back to the exact local run comparison:
  `m01 -> m02` for dense retriever FT,
  `m02 vs m03 vs m04` for retrieval-mode ablation,
  `m02 -> m05` plus `m07/m09` for multistep,
  `m02 -> m18` and `m19 -> m18` for PQE,
  `m11/m12/m13/m15` for calculator standalone,
  `m12 -> m20` for PQE + calculator interaction.
