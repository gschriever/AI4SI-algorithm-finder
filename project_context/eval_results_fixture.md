# AI4SI Algorithm Selector — Evaluation Results

**Evaluated**: 31 papers
**Date**: 2026-04-17 12:08

## Summary

| Metric | Count | Rate |
|--------|-------|------|
| ✅ Exact match | 0 | 0.0% |
| 🟡 Partial match | 0 | 0.0% |
| ❌ Miss | 31 | 100.0% |
| ⚠️ Error | 0 | 0.0% |
| **Exact + Partial** | **0** | **0.0%** |

## Detailed Results

| # | Verdict | Paper | Predicted | Ground Truth (abbrev.) | Rounds |
|---|---------|-------|-----------|----------------------|--------|
| 1 | ❌ | Balancing Act — Prioritization Strategies for LLM-… | logistic_regression | Multi-objective reward function optimization for Restless Mu… | 1 |
| 2 | ❌ | Preference Robustness for DPO with Applications to… | logistic_regression | Distributionally Robust Optimization (DRO) applied to LLM fi… | 1 |
| 3 | ❌ | Navigating the Social Welfare Frontier — Portfolio… | logistic_regression | Multi-objective RL optimization over generalized p-means (Eg… | 1 |
| 4 | ❌ | Decision-Focused Learning in Restless Multi-Armed … | logistic_regression | Whittle index optimization for RMAB; end-to-end differentiab… | 1 |
| 5 | ❌ | Field Study in Deploying Restless Multi-Armed Band… | logistic_regression | Sequential resource scheduling under capacity constraints us… | 1 |
| 6 | ❌ | End-to-End Learning and Optimization on Graphs (Cl… | logistic_regression | Combinatorial graph optimization (clustering, max-cut, facil… | 1 |
| 7 | ❌ | Deploying PAWS — Protection Assistant for Wildlife… | logistic_regression | Mixed-Integer Linear Programming (MILP) within a Stackelberg… | 1 |
| 8 | ❌ | HEALER — POMDP Planning for Scheduling Information… | logistic_regression | Partially Observable Markov Decision Process (POMDP) / Influ… | 1 |
| 9 | ❌ | Fairness in Influence Maximization through Randomi… | logistic_regression | Max-min group fairness optimization over randomized (probabi… | 1 |
| 10 | ❌ | The SAHELI Project (2020–2025) — Five Years of RMA… | logistic_regression | Sequential RMAB resource allocation; Decision-Focused Learni… | 1 |
| 11 | ❌ | LLM Active Alignment — A Nash Equilibrium Perspect… | logistic_regression | ⚠️ **Soft optimization** — game-theoretic Nash Equilibrium c… | 1 |
| 12 | ❌ | Policy-Embedded Graph Expansion — Networked HIV Te… | logistic_regression | Sequential decision optimization over incrementally revealed… | 1 |
| 13 | ❌ | Health Facility Location in Ethiopia — The LEG Fra… | logistic_regression | Population coverage optimization with provable approximation… | 1 |
| 14 | ❌ | Beyond Majority Voting — LLM Aggregation by Levera… | logistic_regression | ⚠️ **Soft optimization** — the Optimal Weight (OW) algorithm… | 1 |
| 15 | ❌ | VORTEX — Aligning Task Utility and Human Preferenc… | logistic_regression | Multi-objective Pareto optimization; LLM generates shaping r… | 1 |
| 16 | ❌ | Optimizing Health Coverage in Ethiopia — HARP | logistic_regression | Sequential facility planning optimization under budget uncer… | 1 |
| 17 | ❌ | Learning to Call — Collaborative Bandit Algorithm … | linear_programming | Multi-Armed Bandit (MAB) optimization for personalized call … | 1 |
| 18 | ❌ | Adaptive Frontier Exploration on Graphs with Appli… | logistic_regression | Sequential reward maximization via a Gittins index-based pol… | 1 |
| 19 | ❌ | Robust Optimization with Diffusion Models for Gree… | linear_programming | Game-theoretic robust optimization / Stackelberg setting ---… | 1 |
| 20 | ❌ | Reinforcement learning with combinatorial actions … | logistic_regression | Deep Reinforcement Learning with Mixed-Integer Programming (… | 1 |
| 21 | ❌ | Rule-Bottleneck Reinforcement Learning: Joint Expl… | logistic_regression | Reinforcement Learning (Rule-Bottleneck Reinforcement Learni… | 1 |
| 22 | ❌ | On Sequential Fault-Intolerant Process Planning | logistic_regression | Online multi-stage sequential decision optimization / Multi-… | 1 |
| 23 | ❌ | Finite-Horizon Single-Pull Restless Bandits: An Ef… | logistic_regression | Finite-Horizon Single-Pull Restless Multi-Armed Bandits (SPR… | 1 |
| 24 | ❌ | IRL for Restless Multi-Armed Bandits with Applicat… | logistic_regression | Inverse Reinforcement Learning (IRL) for Restless Multi-Arme… | 1 |
| 25 | ❌ | Bayesian Collaborative Bandits with Thompson Sampl… | logistic_regression | Collaborative Multi-Armed Bandit (MAB) optimization / Thomps… | 1 |
| 26 | ❌ | Optimizing Vital Sign Monitoring in Resource-Const… | logistic_regression | Restless Multi-Armed Bandit (RMAB) optimization under novel … | 1 |
| 27 | ❌ | Combining Diverse Information for Coordinated Acti… | logistic_regression | Stochastic multi-agent multi-armed bandits / UCB algorithm d… | 1 |
| 28 | ❌ | Escape Sensing Games: Detection-vs-Evasion in Secu… | logistic_regression | Game-theoretic security optimization / Escape Sensing Games … | 1 |
| 29 | ❌ | Improving Health Information Access in the World's… | logistic_regression | Non-Markovian time-series Restless Multi-Armed Bandits --- C… | 1 |
| 30 | ❌ | Efficient Public Health Intervention Planning Usin… | logistic_regression | Decision-Focused Learning (DFL) coupled with Restless Multi-… | 1 |
| 31 | ❌ | A Decision-Language Model (DLM) for Dynamic Restle… | logistic_regression | Automated planner for Multi-agent RMAB reward function speci… | 1 |

## Misses and Errors — Detail

### Balancing Act — Prioritization Strategies for LLM-Designed Restless Bandit Rewards
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Multi-objective reward function optimization for Restless Multi-Armed Bandits (RMAB) --- "Social Choice Language Model" — an LLM generates candidate reward functions, and an external mathematical adjudicator selects the best one using a social welfare function
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### Preference Robustness for DPO with Applications to Public Health
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Distributionally Robust Optimization (DRO) applied to LLM fine-tuning via Direct Preference Optimization (DPO-PRO) --- Lightweight DRO formulation that accounts for uncertainty in preference distributions without excessive conservatism
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### Navigating the Social Welfare Frontier — Portfolios for Multi-objective Reinforcement Learning
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Multi-objective RL optimization over generalized p-means (Egalitarian, Nash, Utilitarian welfare functions) --- α-approximate portfolio of policies — a small set of policies provably near-optimal across all p-mean welfare functions for all p ≤ 1
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### Decision-Focused Learning in Restless Multi-Armed Bandits with Application to Maternal and Child Health
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Whittle index optimization for RMAB; end-to-end differentiable optimization replacing the standard two-stage predict-then-optimize pipeline --- Decision-Focused Learning (DFL) — trains the predictive model directly to maximize downstream Whittle index solution quality
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### Field Study in Deploying Restless Multi-Armed Bandits — Assisting Non-Profits in Improving Maternal and Child Health
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Sequential resource scheduling under capacity constraints using RMAB / Whittle index --- Real-world RMAB deployment with field validation; significantly outperforms rule-based baselines
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### End-to-End Learning and Optimization on Graphs (ClusterNet)
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Combinatorial graph optimization (clustering, max-cut, facility location) via differentiable proxy problem --- ClusterNet — maps hard graph optimization into a differentiable k-means proxy, enabling end-to-end training of representations for decision quality
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### Deploying PAWS — Protection Assistant for Wildlife Security
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Mixed-Integer Linear Programming (MILP) within a Stackelberg Security Game framework --- PAWS system — randomized patrol scheduling using game-theoretic deterrence, deployed in real national parks
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### HEALER — POMDP Planning for Scheduling Information Gathering in Social Networks
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Partially Observable Markov Decision Process (POMDP) / Influence Maximization under uncertainty --- HEALER — balances information gathering (exploring network structure) and exploitation (spreading awareness) under a sequential decision-making framework
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### Fairness in Influence Maximization through Randomization
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Max-min group fairness optimization over randomized (probabilistic) seed sets for Influence Maximization --- Randomized strategies over nodes and sets of nodes; multiplicative-weight routines achieving 1−1/e approximation guarantee for both variants
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### The SAHELI Project (2020–2025) — Five Years of RMABs for Maternal and Child Health
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Sequential RMAB resource allocation; Decision-Focused Learning (DFL) replacing Two-Stage predict-then-optimize --- Multi-year transition from Two-Stage to DFL; validated via large-scale randomized controlled trials showing 31% reduction in engagement drops
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### LLM Active Alignment — A Nash Equilibrium Perspective ⚠️
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: ⚠️ **Soft optimization** — game-theoretic Nash Equilibrium computation rather than a traditional minimize/maximize objective. Finding NE involves optimization, but the framing centers on "mutually best responses" rather than an explicit objective function. Still relevant but the optimization formulation is less direct than other papers. --- Closed-form Nash Equilibrium characterizations with interpretable mixture policies; "active alignment" layer applicable on top of RLHF pipelines
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### Policy-Embedded Graph Expansion — Networked HIV Testing (PEGE)
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Sequential decision optimization over incrementally revealed networks; maximizing discounted reward (HIV detections) under testing budget --- PEGE (Policy-Embedded Graph Expansion) + DDB (Dynamics-Driven Branching diffusion model); 13% improvement in discounted reward and 9% more HIV detections
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### Health Facility Location in Ethiopia — The LEG Framework
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Population coverage optimization with provable approximation guarantees; multi-objective optimization integrating qualitative stakeholder preferences via LLM --- LEG (LLM + Extended Greedy) — combines a provable approximation algorithm for coverage maximization with LLM-driven iterative refinement of qualitative expert guidance
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### Beyond Majority Voting — LLM Aggregation by Leveraging Higher-Order Information ⚠️
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: ⚠️ **Soft optimization** — the Optimal Weight (OW) algorithm solves an optimization problem (computing optimal aggregation weights), but the paper is primarily framed as an estimation/aggregation problem rather than a social resource allocation problem. The weakest link in terms of optimization framing. Its key qualification is empirical validation on ARMMAN. --- OW (Optimal Weight) and ISP (Inverse Surprising Popularity) algorithms; provably mitigate limitations of majority voting under mild theoretical assumptions
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### VORTEX — Aligning Task Utility and Human Preferences through LLM-Guided Reward Shaping
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Multi-objective Pareto optimization; LLM generates shaping rewards that are composited with existing solver objectives to converge to Pareto-optimal trade-offs --- VORTEX — text-gradient prompt updates + verbal reinforcement; theoretical convergence guarantees to Pareto-optimal utility/preference trade-offs
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### Optimizing Health Coverage in Ethiopia — HARP
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Sequential facility planning optimization under budget uncertainty; worst-case approximation algorithms with theoretical guarantees --- HARP (Health Access Resource Planner) — (i) learning-augmented algorithm for single-step planning; (ii) greedy algorithm for multi-step planning; both with strong approximation guarantees
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### Learning to Call — Collaborative Bandit Algorithm for Mobile Maternal Health (Kilkari)
- **Status**: completed
- **Predicted**: linear_programming
- **Alternatives**: time_series_forecasting, deep_learning_forecast
- **Ground Truth**: Multi-Armed Bandit (MAB) optimization for personalized call timing; maximizes call pick-up rates by learning individual mothers' preferred time windows --- Collaborative bandit algorithm for call scheduling; statistically significant improvement in pick-up rates in field trial
- **Recommendation Summary**: Recommended family: linear_programming. This fits because the problem is structured as forecasting with explicit constraints and governance safeguards.

### Adaptive Frontier Exploration on Graphs with Applications to Network-Based Disease Testing
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Sequential reward maximization via a Gittins index-based policy; provably optimal on forests/trees; O(n log n) time implementation --- Gittins index policy under frontier-exploration constraint — detects nearly all HIV-positive cases with only half the population tested, substantially outperforming baselines
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### Robust Optimization with Diffusion Models for Green Security
- **Status**: completed
- **Predicted**: linear_programming
- **Alternatives**: time_series_forecasting, deep_learning_forecast
- **Ground Truth**: Game-theoretic robust optimization / Stackelberg setting --- Conditional diffusion model for adversary behavior modeling; twisted Sequential Monte Carlo (SMC) sampler to compute utility; converges to epsilon equilibrium
- **Recommendation Summary**: Recommended family: linear_programming. This fits because the problem is structured as forecasting with explicit constraints and governance safeguards.

### Reinforcement learning with combinatorial actions for coupled restless bandits (SEQUOIA)
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Deep Reinforcement Learning with Mixed-Integer Programming (RL + MIP) for coupled Restless Multi-Armed Bandits (coRMAB) --- SEQUOIA directly optimizes long-term reward over the feasible combinatorially structured action space by embedding a Q-network into a mixed-integer program
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### Rule-Bottleneck Reinforcement Learning: Joint Explanation and Decision Optimization
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Reinforcement Learning (Rule-Bottleneck Reinforcement Learning) joint optimization of decisions and explanations --- RBRL generates candidate rules via LLM and applies an attention-based RL policy to select explainable rules, matching deep RL utility while beating LLMs
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### On Sequential Fault-Intolerant Process Planning
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Online multi-stage sequential decision optimization / Multi-Armed Bandits --- Provably tight online algorithms for sequential fault-intolerant planning with unknown action success probabilities
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### Finite-Horizon Single-Pull Restless Bandits: An Efficient Index Policy
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Finite-Horizon Single-Pull Restless Multi-Armed Bandits (SPRMABs) / Index Policy Optimization --- Uses dummy states to handle the strict one-pull constraint and designs an index policy delivering a sub-linearly decaying average optimality gap
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### IRL for Restless Multi-Armed Bandits with Applications in Maternal and Child Health
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Inverse Reinforcement Learning (IRL) for Restless Multi-Armed Bandits --- WHIRL algorithm uses population-level expert trajectories and gradient updates to learn accurate RMAB rewards directly from field practitioners
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### Bayesian Collaborative Bandits with Thompson Sampling for Improved Outreach in Maternal Health Program
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Collaborative Multi-Armed Bandit (MAB) optimization / Thompson Sampling --- Principled Bayesian approach using Thompson Sampling with Gibbs sampling for posterior inference over low-rank matrix factors for collaborative bandits
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### Optimizing Vital Sign Monitoring in Resource-Constrained Maternal Care: An RL-Based Restless Bandit Approach
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Restless Multi-Armed Bandit (RMAB) optimization under novel operational constraints via Deep Reinforcement Learning --- Proximal Policy Optimization (PPO) trains a policy and value function network to navigate domain-unique constraints unsuitable for traditional RMAB index policies
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### Combining Diverse Information for Coordinated Action: Stochastic Bandit Algorithms for Heterogeneous Agents
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Stochastic multi-agent multi-armed bandits / UCB algorithm design --- Min-Width algorithm, a UCB-style coordination algorithm prioritizing information aggregation across agents to exploit known structure in reward functions
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### Escape Sensing Games: Detection-vs-Evasion in Security Applications
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Game-theoretic security optimization / Escape Sensing Games --- Novel class of security games centered around strategically arranging targets to protect them against constrained adversaries; NP-hardness proofs and effective heuristic algorithms
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### Improving Health Information Access in the World's Largest Maternal Mobile Health Program via Bandit Algorithms
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Non-Markovian time-series Restless Multi-Armed Bandits --- CHAHAK system optimizes multiple interventions using non-markovian RMABs to handle domain complexities unsuitable for traditional markovian solutions
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### Efficient Public Health Intervention Planning Using Decomposition-Based Decision-Focused Learning
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Decision-Focused Learning (DFL) coupled with Restless Multi-Armed Bandits --- Mathematically decoupling planning across different beneficiaries to speed up the nested RMAB evaluation in DFL training by up to 100x while yielding superior performance
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.

### A Decision-Language Model (DLM) for Dynamic Restless Multi-Armed Bandit Tasks in Public Health
- **Status**: completed
- **Predicted**: logistic_regression
- **Alternatives**: manual_triage, gradient_boosted_trees
- **Ground Truth**: Automated planner for Multi-agent RMAB reward function specification --- The Decision Language Model (DLM) framework uses LLMs to interpret human policy preference prompts, generate reward functions as code, and iterate via feedback from grounded RMAB simulations
- **Recommendation Summary**: Recommended family: logistic_regression. This fits because the problem is structured as prediction with explicit constraints and governance safeguards.
