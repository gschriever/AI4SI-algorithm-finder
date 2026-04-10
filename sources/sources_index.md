# AI4SI Sources Index

This file serves as the annotated index for all papers accepted into the AI4SI project's sources library.

---

## Inclusion Criteria

Papers are accepted into this library if and only if they meet **all** of the following criteria:

### 1. Venue
The paper must be either:
- A **preprint** (e.g., arXiv), OR
- **Accepted** at an accredited top AI/CS conference or journal (e.g., NeurIPS, ICML, ICLR, AAAI, IJCAI, AAMAS, ACL, EMNLP, IEEE, etc.)

### 2. Strong Methodological Component
- Must contain **novel algorithms, theoretical guarantees, or rigorous empirical contributions**
- **Position papers, blue-sky papers, and survey papers are excluded** — even if accepted at a top venue

### 3. Optimization Problem
- The paper must **solve, directly enable, or substantially contribute to solving an optimization problem**
- It does NOT need to apply the method to a social problem directly, but it must give **concrete examples** of where the method could be applied
- Papers whose contribution is purely predictive/generative modeling (with optimization left entirely to downstream systems) are **excluded**
- Two papers (#11 and #14) are noted with ⚠️ as **soft fits** for this criterion and should be used with awareness of that limitation

### 4. Social Impact
- The paper must **demonstrate or explicitly discuss social impact applications**
- Papers grounding methods entirely in commercial or generic engineering contexts (e.g., consumer LLM personalization) are **excluded**

### 5. Recency
- Must be published **post-2000**
- Preference for 2022–2026; earlier papers included where they are foundational

---

> [!NOTE]
> Papers marked ⚠️ have a softer connection to the optimization framing and should be used with awareness of that limitation.

---

## Paper 1: Balancing Act — Prioritization Strategies for LLM-Designed Restless Bandit Rewards

- **Authors:** Shresth Verma, Niclas Boehmer, Lingkai Kong, Milind Tambe
- **Venue:** NeurIPS 2024
- **arXiv:** [2408.12112](https://arxiv.org/abs/2408.12112)
- **Local File:** `2408.12112v6.pdf`
- **Social Problem(s):** Public health resource allocation — optimally scheduling limited healthcare worker outreach for beneficiaries in maternal health programs
- **Optimization Type:** Multi-objective reward function optimization for Restless Multi-Armed Bandits (RMAB)
- **Key Method:** "Social Choice Language Model" — an LLM generates candidate reward functions, and an external mathematical adjudicator selects the best one using a social welfare function

---

## Paper 2: Preference Robustness for DPO with Applications to Public Health

- **Authors:** Cheol Woo Kim, Shresth Verma, Mauricio Tec, Milind Tambe
- **Venue:** AAAI 2025
- **arXiv:** [2509.02709](https://arxiv.org/abs/2509.02709)
- **Local File:** `2509.02709v2.pdf`
- **Social Problem(s):** Maternal mobile health — aligning LLMs to design robust reward functions under noisy preference signals for sequential public health resource allocation
- **Optimization Type:** Distributionally Robust Optimization (DRO) applied to LLM fine-tuning via Direct Preference Optimization (DPO-PRO)
- **Key Method:** Lightweight DRO formulation that accounts for uncertainty in preference distributions without excessive conservatism

---

## Paper 3: Navigating the Social Welfare Frontier — Portfolios for Multi-objective Reinforcement Learning

- **Authors:** Cheol Woo Kim, Jai Moondra, Shresth Verma, Madeleine Pollack, Lingkai Kong, Milind Tambe, Swati Gupta
- **Venue:** ICML 2025
- **arXiv:** [2502.09724](https://arxiv.org/abs/2502.09724)
- **Local File:** `2502.09724v2.pdf`
- **Social Problem(s):** Multi-stakeholder resource allocation — fairly distributing resources across heterogeneous populations with conflicting priorities (e.g., public health, conservation, infrastructure)
- **Optimization Type:** Multi-objective RL optimization over generalized p-means (Egalitarian, Nash, Utilitarian welfare functions)
- **Key Method:** α-approximate portfolio of policies — a small set of policies provably near-optimal across all p-mean welfare functions for all p ≤ 1

---

## Paper 4: Decision-Focused Learning in Restless Multi-Armed Bandits with Application to Maternal and Child Health

- **Authors:** Kai Wang, Shresth Verma, Aditya Mate, Sanket Shah, Aparna Taneja, Neha Madhiwalla, Aparna Hegde, Milind Tambe
- **Venue:** AAAI 2023
- **arXiv:** [2202.00916](https://arxiv.org/abs/2202.00916)
- **Local File:** `2202.00916v1.pdf`
- **Social Problem(s):** Maternal and child health — optimally sequencing limited live healthcare worker calls to maximize long-term beneficiary engagement (ARMMAN program)
- **Optimization Type:** Whittle index optimization for RMAB; end-to-end differentiable optimization replacing the standard two-stage predict-then-optimize pipeline
- **Key Method:** Decision-Focused Learning (DFL) — trains the predictive model directly to maximize downstream Whittle index solution quality

---

## Paper 5: Field Study in Deploying Restless Multi-Armed Bandits — Assisting Non-Profits in Improving Maternal and Child Health

- **Authors:** Aditya Mate, Lovish Madaan, Aparna Taneja, Neha Madhiwalla, Shresth Verma, Gargi Singh, Aparna Hegde, Pradeep Varakantham, Milind Tambe
- **Venue:** AAAI 2022
- **arXiv:** [2109.08075](https://arxiv.org/abs/2109.08075)
- **Local File:** `2109.08075v1.pdf`
- **Social Problem(s):** Maternal health — optimizing automated health service call scheduling under strict capacity constraints (ARMMAN program in India)
- **Optimization Type:** Sequential resource scheduling under capacity constraints using RMAB / Whittle index
- **Key Method:** Real-world RMAB deployment with field validation; significantly outperforms rule-based baselines

---

## Paper 6: End-to-End Learning and Optimization on Graphs (ClusterNet)

- **Authors:** Bryan Wilder, Eric Ewing, Bistra Dilkina, Milind Tambe
- **Venue:** NeurIPS 2019
- **arXiv:** [1905.13732](https://arxiv.org/abs/1905.13732)
- **Local File:** `1905.13732v1.pdf`
- **Social Problem(s):** General combinatorial resource allocation on social/infrastructure networks (e.g., community detection, facility location, intervention targeting)
- **Optimization Type:** Combinatorial graph optimization (clustering, max-cut, facility location) via differentiable proxy problem
- **Key Method:** ClusterNet — maps hard graph optimization into a differentiable k-means proxy, enabling end-to-end training of representations for decision quality

---

## Paper 7: Deploying PAWS — Protection Assistant for Wildlife Security

- **Authors:** Fei Fang, Thanh H. Nguyen, Rob Pickles, Wai Y. Lam, Gopalasamy R. Clements, Bo An, Amandeep Singh, Brian C. Schwedock, Milind Tambe, Andrew Lemieux
- **Venue:** IAAI / AAAI 2016
- **Link:** [AAAI/IAAI Proceedings](https://ojs.aaai.org/index.php/AAAI/article/view/19070)
- **Local File:** `19070_paws.pdf`
- **Social Problem(s):** Wildlife conservation — optimizing anti-poaching patrol routes in national parks under limited ranger resources against strategic adversaries
- **Optimization Type:** Mixed-Integer Linear Programming (MILP) within a Stackelberg Security Game framework
- **Key Method:** PAWS system — randomized patrol scheduling using game-theoretic deterrence, deployed in real national parks

---

## Paper 8: HEALER — POMDP Planning for Scheduling Information Gathering in Social Networks

- **Authors:** Amulya Yadav, Hau Chan, Albert Xin Jiang, Haifeng Xu, Eric Rice, Milind Tambe
- **Venue:** IJCAI / AAAI (2015–2017)
- **arXiv:** [1602.00165](https://arxiv.org/abs/1602.00165)
- **Local File:** `1602.00165v1.pdf`
- **Social Problem(s):** Youth homelessness and HIV prevention — maximizing HIV awareness spread through peer social networks of homeless youth under budget and observation constraints
- **Optimization Type:** Partially Observable Markov Decision Process (POMDP) / Influence Maximization under uncertainty
- **Key Method:** HEALER — balances information gathering (exploring network structure) and exploitation (spreading awareness) under a sequential decision-making framework

---

## Paper 9: Fairness in Influence Maximization through Randomization

- **Authors:** Juba Ziani, Ali Kebarighotbi, Bryan Wilder
- **Venue:** AAAI 2020
- **arXiv:** [2010.03438](https://arxiv.org/abs/2010.03438)
- **Local File:** `2010.03438v4.pdf`
- **Social Problem(s):** Equitable public health information spread — ensuring information about health interventions reaches underrepresented demographic groups in social networks, not just the majority
- **Optimization Type:** Max-min group fairness optimization over randomized (probabilistic) seed sets for Influence Maximization
- **Key Method:** Randomized strategies over nodes and sets of nodes; multiplicative-weight routines achieving 1−1/e approximation guarantee for both variants

---

## Paper 10: The SAHELI Project (2020–2025) — Five Years of RMABs for Maternal and Child Health

- **Authors:** Shresth Verma, Arpan Dasgupta, Neha Madhiwalla, Aparna Taneja, Milind Tambe
- **Venue:** arXiv preprint (April 2026)
- **arXiv:** [2604.07384](https://arxiv.org/abs/2604.07384)
- **Local File:** `2604.07384v1.pdf`
- **Social Problem(s):** Maternal and child health — longitudinal deployment of AI-optimized resource scheduling for a health program in India; demonstrated real-world behavioral health improvements
- **Optimization Type:** Sequential RMAB resource allocation; Decision-Focused Learning (DFL) replacing Two-Stage predict-then-optimize
- **Key Method:** Multi-year transition from Two-Stage to DFL; validated via large-scale randomized controlled trials showing 31% reduction in engagement drops

---

## Paper 11: LLM Active Alignment — A Nash Equilibrium Perspective ⚠️

- **Authors:** Tonghan Wang, Yuqi Pan, Xinyi Yang, Yanchen Jiang, Milind Tambe, David C. Parkes
- **Venue:** arXiv preprint (February 2026)
- **arXiv:** [2602.06836](https://arxiv.org/abs/2602.06836)
- **Local File:** `2602.06836v1.pdf`
- **Social Problem(s):** Socially equitable AI alignment — preventing political exclusion (entire subpopulations being ignored by LLM agents) in social media and multi-agent LLM deployments
- **Optimization Type:** ⚠️ **Soft optimization** — game-theoretic Nash Equilibrium computation rather than a traditional minimize/maximize objective. Finding NE involves optimization, but the framing centers on "mutually best responses" rather than an explicit objective function. Still relevant but the optimization formulation is less direct than other papers.
- **Key Method:** Closed-form Nash Equilibrium characterizations with interpretable mixture policies; "active alignment" layer applicable on top of RLHF pipelines

---

## Paper 12: Policy-Embedded Graph Expansion — Networked HIV Testing (PEGE)

- **Authors:** Akseli Kangaslahti, Davin Choo, Lingkai Kong, Milind Tambe, Alastair van Heerden, Cheryl Johnson
- **Venue:** arXiv preprint (January 2026)
- **arXiv:** [2601.16233](https://arxiv.org/abs/2601.16233)
- **Local File:** `2601.16233v1.pdf`
- **Social Problem(s):** HIV epidemic control — improving efficiency of HIV testing by sequentially identifying high-risk individuals through incrementally revealed transmission networks (in collaboration with WHO and Wits University)
- **Optimization Type:** Sequential decision optimization over incrementally revealed networks; maximizing discounted reward (HIV detections) under testing budget
- **Key Method:** PEGE (Policy-Embedded Graph Expansion) + DDB (Dynamics-Driven Branching diffusion model); 13% improvement in discounted reward and 9% more HIV detections

---

## Paper 13: Health Facility Location in Ethiopia — The LEG Framework

- **Authors:** Yohai Trabelsi, Guojun Xiong, Fentabil Getnet, Stéphane Verguet, Milind Tambe
- **Venue:** arXiv preprint (January 2026)
- **arXiv:** [2601.11479](https://arxiv.org/abs/2601.11479)
- **Local File:** `2601.11479v2.pdf`
- **Social Problem(s):** Rural healthcare access in Ethiopia — prioritizing which health posts to upgrade to maximize population coverage, in collaboration with Ethiopia's Ministry of Health
- **Optimization Type:** Population coverage optimization with provable approximation guarantees; multi-objective optimization integrating qualitative stakeholder preferences via LLM
- **Key Method:** LEG (LLM + Extended Greedy) — combines a provable approximation algorithm for coverage maximization with LLM-driven iterative refinement of qualitative expert guidance

---

## Paper 14: Beyond Majority Voting — LLM Aggregation by Leveraging Higher-Order Information ⚠️

- **Authors:** Rui Ai, Yuqi Pan, David Simchi-Levi, Milind Tambe, Haifeng Xu
- **Venue:** arXiv preprint (October 2025)
- **arXiv:** [2510.01499](https://arxiv.org/abs/2510.01499)
- **Local File:** `2510.01499v1.pdf`
- **Social Problem(s):** Healthcare decision-making — improving reliability of multi-agent LLM outputs in real-world settings like ARMMAN maternal health program
- **Optimization Type:** ⚠️ **Soft optimization** — the Optimal Weight (OW) algorithm solves an optimization problem (computing optimal aggregation weights), but the paper is primarily framed as an estimation/aggregation problem rather than a social resource allocation problem. The weakest link in terms of optimization framing. Its key qualification is empirical validation on ARMMAN.
- **Key Method:** OW (Optimal Weight) and ISP (Inverse Surprising Popularity) algorithms; provably mitigate limitations of majority voting under mild theoretical assumptions

---

## Paper 15: VORTEX — Aligning Task Utility and Human Preferences through LLM-Guided Reward Shaping

- **Authors:** Guojun Xiong, Milind Tambe
- **Venue:** arXiv preprint (September 2025)
- **arXiv:** [2509.16399](https://arxiv.org/abs/2509.16399)
- **Local File:** `2509.16399v1.pdf`
- **Social Problem(s):** Social impact optimization broadly — enabling stakeholders to steer AI allocation decisions (e.g., healthcare coverage, conservation interventions) via natural language without modifying the underlying solver
- **Optimization Type:** Multi-objective Pareto optimization; LLM generates shaping rewards that are composited with existing solver objectives to converge to Pareto-optimal trade-offs
- **Key Method:** VORTEX — text-gradient prompt updates + verbal reinforcement; theoretical convergence guarantees to Pareto-optimal utility/preference trade-offs

---

## Paper 16: Optimizing Health Coverage in Ethiopia — HARP

- **Authors:** Davin Choo, Yohai Trabelsi, Fentabil Getnet, Samson Warkaye Lamma, Wondesen Nigatu, Kasahun Sime, Lisa Matay, Milind Tambe, Stéphane Verguet
- **Venue:** arXiv preprint (September 2025)
- **arXiv:** [2509.00135](https://arxiv.org/abs/2509.00135)
- **Local File:** `2509.00135v1.pdf`
- **Social Problem(s):** Universal health coverage in Ethiopia — sequential prioritization of health post upgrades to maximize population coverage under annual budget uncertainty and regional proportionality constraints (UN SDG 3)
- **Optimization Type:** Sequential facility planning optimization under budget uncertainty; worst-case approximation algorithms with theoretical guarantees
- **Key Method:** HARP (Health Access Resource Planner) — (i) learning-augmented algorithm for single-step planning; (ii) greedy algorithm for multi-step planning; both with strong approximation guarantees

> [!NOTE]
> Topically related to Paper #13 (Ethiopia LEG) from the same collaboration, but methodologically distinct — HARP focuses on sequential/online budget uncertainty, while LEG focuses on integrating qualitative LLM guidance with optimization.

---

## Paper 17: Learning to Call — Collaborative Bandit Algorithm for Mobile Maternal Health (Kilkari)

- **Authors:** Arpan Dasgupta, Mizhaan Maniyar, Awadhesh Srivastava, Sanat Kumar, Amrita Mahale, Aparna Hegde, Arun Suggala, Karthikeyan Shanmugam, Aparna Taneja, Milind Tambe
- **Venue:** arXiv preprint (November 2025, original July 2025)
- **arXiv:** [2507.16356](https://arxiv.org/abs/2507.16356)
- **Local File:** `2507.16356v2.pdf`
- **Social Problem(s):** Maternal health at scale — optimizing call timing for India's Kilkari program to improve health message delivery rates to millions of mothers
- **Optimization Type:** Multi-Armed Bandit (MAB) optimization for personalized call timing; maximizes call pick-up rates by learning individual mothers' preferred time windows
- **Key Method:** Collaborative bandit algorithm for call scheduling; statistically significant improvement in pick-up rates in field trial

> [!NOTE]
> Topically related to Papers #4, #5, #10 (all RMAB/maternal health), but distinct — this optimizes *when* to call (timing), whereas the others optimize *whom* to prioritize for intervention. Different program (Kilkari vs. ARMMAN).

---

---

## Paper 18: Adaptive Frontier Exploration on Graphs with Applications to Network-Based Disease Testing

- **Authors:** Davin Choo, Yuqi Pan, Tonghan Wang, Milind Tambe, Alastair van Heerden, Cheryl Johnson
- **Venue:** NeurIPS 2025
- **arXiv:** [2505.21671](https://arxiv.org/abs/2505.21671)
- **Local File:** `2505.21671v1.pdf`
- **Social Problem(s):** HIV epidemic control — sequential node selection on disease transmission networks to maximize HIV case detection under a frontier exploration constraint (contact tracing); demonstrated on real-world sexual interaction networks
- **Optimization Type:** Sequential reward maximization via a Gittins index-based policy; provably optimal on forests/trees; O(n log n) time implementation
- **Key Method:** Gittins index policy under frontier-exploration constraint — detects nearly all HIV-positive cases with only half the population tested, substantially outperforming baselines

> [!NOTE]
> Topically related to Paper #12 (HIV PEGE) — same HIV testing domain, but different algorithmic approach (Gittins index vs. generative graph expansion).

---

## Paper 19: Robust Optimization with Diffusion Models for Green Security

- **Authors:** Lingkai Kong, Haichuan Wang, Yuqi Pan, Cheol Woo Kim, Mingxiao Song, Alayna Nguyen, Tonghan Wang, Haifeng Xu, Milind Tambe
- **Venue:** UAI 2025
- **arXiv:** [2503.05730](https://arxiv.org/abs/2503.05730)
- **Local File:** `2503.05730v1.pdf`
- **Social Problem(s):** Wildlife conservation (green security) — forecasting highly uncertain adversarial behavior (poaching, illegal logging) to plan effective patrols
- **Optimization Type:** Game-theoretic robust optimization / Stackelberg setting
- **Key Method:** Conditional diffusion model for adversary behavior modeling; twisted Sequential Monte Carlo (SMC) sampler to compute utility; converges to epsilon equilibrium

---

## Paper 20: Reinforcement learning with combinatorial actions for coupled restless bandits (SEQUOIA)

- **Authors:** Lily Xu, Bryan Wilder, Elias B. Khalil, Milind Tambe
- **Venue:** ICLR 2025
- **arXiv:** [2503.01919](https://arxiv.org/abs/2503.01919)
- **Local File:** `2503.01919v1.pdf`
- **Social Problem(s):** Sequential decision-making with combinatorial constraints—directly relevant for applying capacity-constrained public health interventions across coupled arms
- **Optimization Type:** Deep Reinforcement Learning with Mixed-Integer Programming (RL + MIP) for coupled Restless Multi-Armed Bandits (coRMAB)
- **Key Method:** SEQUOIA directly optimizes long-term reward over the feasible combinatorially structured action space by embedding a Q-network into a mixed-integer program

---

## Paper 21: Rule-Bottleneck Reinforcement Learning: Joint Explanation and Decision Optimization

- **Authors:** Mauricio Tec, Guojun Xiong, Haichuan Wang, Francesca Dominici, Milind Tambe
- **Venue:** arXiv preprint (February 2025)
- **arXiv:** [2502.10732](https://arxiv.org/abs/2502.10732)
- **Local File:** `2502.10732v1.pdf`
- **Social Problem(s):** Healthcare, public policy, and resource allocation — balancing optimization performance with human-understandable reasoning for decision-makers
- **Optimization Type:** Reinforcement Learning (Rule-Bottleneck Reinforcement Learning) joint optimization of decisions and explanations
- **Key Method:** RBRL generates candidate rules via LLM and applies an attention-based RL policy to select explainable rules, matching deep RL utility while beating LLMs

---

## Paper 22: On Sequential Fault-Intolerant Process Planning

- **Authors:** Andrzej Kaczmarczyk, Davin Choo, Niclas Boehmer, Milind Tambe, Haifeng Xu
- **Venue:** arXiv preprint (February 2025)
- **arXiv:** [2502.04998](https://arxiv.org/abs/2502.04998)
- **Local File:** `2502.04998v1.pdf`
- **Social Problem(s):** Process planning where all stages must succeed — quality-critical security, process design, and drug/material discovery
- **Optimization Type:** Online multi-stage sequential decision optimization / Multi-Armed Bandits
- **Key Method:** Provably tight online algorithms for sequential fault-intolerant planning with unknown action success probabilities

---

## Paper 23: Finite-Horizon Single-Pull Restless Bandits: An Efficient Index Policy

- **Authors:** Guojun Xiong, Haichuan Wang, Yuqi Pan, Saptarshi Mandal, Sanket Shah, Niclas Boehmer, Milind Tambe
- **Venue:** AAMAS 2025
- **arXiv:** [2501.06103](https://arxiv.org/abs/2501.06103)
- **Local File:** `2501.06103v1.pdf`
- **Social Problem(s):** Highly scarce resource allocation — e.g. scarce healthcare intervention programs where agents can only receive the resource/intervention exactly once
- **Optimization Type:** Finite-Horizon Single-Pull Restless Multi-Armed Bandits (SPRMABs) / Index Policy Optimization
- **Key Method:** Uses dummy states to handle the strict one-pull constraint and designs an index policy delivering a sub-linearly decaying average optimality gap

---

## Paper 24: IRL for Restless Multi-Armed Bandits with Applications in Maternal and Child Health

- **Authors:** Gauri Jain, Pradeep Varakantham, Haifeng Xu, Aparna Taneja, Prashant Doshi, Milind Tambe
- **Venue:** PRICAI 2024
- **arXiv:** [2412.08463](https://arxiv.org/abs/2412.08463)
- **Local File:** `2412.08463v1.pdf`
- **Social Problem(s):** Maternal and child health (ARMMAN) — overcoming the challenge of unknown underlying reward functions in managing limited resources over large patient cohorts
- **Optimization Type:** Inverse Reinforcement Learning (IRL) for Restless Multi-Armed Bandits
- **Key Method:** WHIRL algorithm uses population-level expert trajectories and gradient updates to learn accurate RMAB rewards directly from field practitioners

---

## Paper 25: Bayesian Collaborative Bandits with Thompson Sampling for Improved Outreach in Maternal Health Program

- **Authors:** Arpan Dasgupta, Gagan Jain, Arun Suggala, Karthikeyan Shanmugam, Milind Tambe, Aparna Taneja
- **Venue:** arXiv preprint (October 2024)
- **arXiv:** [2410.21405](https://arxiv.org/abs/2410.21405)
- **Local File:** `2410.21405v1.pdf`
- **Social Problem(s):** Maternal health mHealth programs — optimizing the timing of automated health information calls to beneficiaries to maximize engagement
- **Optimization Type:** Collaborative Multi-Armed Bandit (MAB) optimization / Thompson Sampling
- **Key Method:** Principled Bayesian approach using Thompson Sampling with Gibbs sampling for posterior inference over low-rank matrix factors for collaborative bandits

---

## Paper 26: Optimizing Vital Sign Monitoring in Resource-Constrained Maternal Care: An RL-Based Restless Bandit Approach

- **Authors:** Niclas Boehmer, Yunfan Zhao, Guojun Xiong, Paula Rodriguez-Diaz, Paola Del Cueto Cibrian, Joseph Ngonzi, Adeline Boatin, Milind Tambe
- **Venue:** arXiv preprint (October 2024)
- **arXiv:** [2410.08377](https://arxiv.org/abs/2410.08377)
- **Local File:** `2410.08377v1.pdf`
- **Social Problem(s):** Maternal mortality — sequential allocation of scarce wireless vital sign monitoring devices to mothers after childbirth
- **Optimization Type:** Restless Multi-Armed Bandit (RMAB) optimization under novel operational constraints via Deep Reinforcement Learning
- **Key Method:** Proximal Policy Optimization (PPO) trains a policy and value function network to navigate domain-unique constraints unsuitable for traditional RMAB index policies

---

## Paper 27: Combining Diverse Information for Coordinated Action: Stochastic Bandit Algorithms for Heterogeneous Agents

- **Authors:** Lucia Gordon, Esther Rolf, Milind Tambe
- **Venue:** ECAI 2024
- **arXiv:** [2408.03405](https://arxiv.org/abs/2408.03405)
- **Local File:** `2408.03405v1.pdf`
- **Social Problem(s):** Multi-agent coordinated resource allocation — coordinating heterogeneous agents with different sensing/detection sensitivities in domains like medical screening (where disease detection rates vary by test type) and environmental sensing
- **Optimization Type:** Stochastic multi-agent multi-armed bandits / UCB algorithm design
- **Key Method:** Min-Width algorithm, a UCB-style coordination algorithm prioritizing information aggregation across agents to exploit known structure in reward functions

---

## Paper 28: Escape Sensing Games: Detection-vs-Evasion in Security Applications

- **Authors:** Niclas Boehmer, Minbiao Han, Haifeng Xu, Milind Tambe
- **Venue:** arXiv preprint (October 2024)
- **arXiv:** [2407.20981](https://arxiv.org/abs/2407.20981)
- **Local File:** `2407.20981v1.pdf`
- **Social Problem(s):** Peacekeeping resource transit and cybersecurity
- **Optimization Type:** Game-theoretic security optimization / Escape Sensing Games
- **Key Method:** Novel class of security games centered around strategically arranging targets to protect them against constrained adversaries; NP-hardness proofs and effective heuristic algorithms

---

## Paper 29: Improving Health Information Access in the World's Largest Maternal Mobile Health Program via Bandit Algorithms

- **Authors:** Arshika Lalan, Shresth Verma, Paula Rodriguez Diaz, Panayiotis Danassis, Amrita Mahale, Kumar Madhu Sudan, Aparna Hegde, Milind Tambe, Aparna Taneja
- **Venue:** IAAI 2024
- **arXiv:** [2407.12131](https://arxiv.org/abs/2407.12131)
- **Local File:** `2407.12131v1.pdf`
- **Social Problem(s):** Maternal health mHealth programs — optimizing allocation of multiple live interventions to reduce automated dropouts in India's Kilkari program
- **Optimization Type:** Non-Markovian time-series Restless Multi-Armed Bandits
- **Key Method:** CHAHAK system optimizes multiple interventions using non-markovian RMABs to handle domain complexities unsuitable for traditional markovian solutions

---

## Paper 30: Efficient Public Health Intervention Planning Using Decomposition-Based Decision-Focused Learning

- **Authors:** Sanket Shah, Arun Suggala, Milind Tambe, Aparna Taneja
- **Venue:** arXiv preprint (March 2024)
- **arXiv:** [2403.05683](https://arxiv.org/abs/2403.05683)
- **Local File:** `2403.05683v1.pdf`
- **Social Problem(s):** Maternal and child health — accelerating intervention targeting models to scale up to millions of mothers for ARMMAN
- **Optimization Type:** Decision-Focused Learning (DFL) coupled with Restless Multi-Armed Bandits
- **Key Method:** Mathematically decoupling planning across different beneficiaries to speed up the nested RMAB evaluation in DFL training by up to 100x while yielding superior performance

---

## Paper 31: A Decision-Language Model (DLM) for Dynamic Restless Multi-Armed Bandit Tasks in Public Health

- **Authors:** Nikhil Behari, Edwin Zhang, Yunfan Zhao, Aparna Taneja, Dheeraj Nagaraj, Milind Tambe
- **Venue:** NeurIPS 2024
- **arXiv:** [2402.14807](https://arxiv.org/abs/2402.14807)
- **Local File:** `2402.14807v1.pdf`
- **Social Problem(s):** Public health policy — allowing grassroots organizers and domain experts to dynamically adjust resource allocation parameters via natural language
- **Optimization Type:** Automated planner for Multi-agent RMAB reward function specification
- **Key Method:** The Decision Language Model (DLM) framework uses LLMs to interpret human policy preference prompts, generate reward functions as code, and iterate via feedback from grounded RMAB simulations

---

## Files in /sources Not Yet Evaluated

All files in this directory have been evaluated and mapped to an accepted paper above.

## Download Status

All 31 accepted papers have been downloaded and verified. ✅
