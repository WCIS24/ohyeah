### 5.4 典型复杂查询案例（3个）

**案例1（qid=8c8c8c34）**
- Query：Hasbro (HAS) 2023 one-time charges impact on operating profitability vs historical trends and cap allocation implications.
- Gold Answer（摘要）：In 2023, Hasbro’s operating result turned from a profit in prior years (407.7 million in 2022 and 763.3 million in 2021) to an operating loss of 1,538.8 million…
- Step0 Top3：008beea7_e0_c0，8c8c8c34_e0_c2，f8aec91a_e0_c1
- Step1 Top3：008beea7_e0_c0，f8aec91a_e0_c1，8c8c8c34_e0_c2
- gap/stop：MISSING_ENTITY / MAX_STEPS，final_topk_size=10
- 分析：该问题包含对比关系与年份信息，多步检索识别到 gap，但 refined query 与原查询高度相似，导致新增证据有限。

**案例2（qid=52e25ec7）**
- Query：Impact on net investing cash flows from EUC sale cash inflow offsets vs acquisition outflows, AVGO.
- Gold Answer（摘要）：The $3,485 million inflow from the sale of the EUC business helped to partially offset the significantly higher cash expenditures related to acquisitions…
- Step0 Top3：506e7d1e_e0_c0，52e25ec7_e0_c0，e4661352_e0_c3
- Step1 Top3：506e7d1e_e0_c0，52e25ec7_e0_c0，1c47856d_e0_c1
- gap/stop：MISSING_ENTITY / MAX_STEPS，final_topk_size=10
- 分析：问题涉及“出售现金流入 vs 并购现金流出”的对比，多步检索能够维持证据覆盖但未显著扩展证据范围。

**案例3（qid=ed746c33）**
- Query：Cash flow & cap alloc implications of IRM's ASC 842 storage rev rec vs other lines.
- Gold Answer（摘要）：For its Global Data Center Business, Iron Mountain recognizes storage revenues under ASC 842…
- Step0 Top3：ed746c33_e0_c0，2a8785e8_e0_c15，a68b8600_e0_c5
- gap/stop：NO_GAP / NO_GAP，final_topk_size=10
- 分析：该类问题实体明确、语义集中，单步检索即可覆盖核心证据，多步检索不引入额外噪声。
