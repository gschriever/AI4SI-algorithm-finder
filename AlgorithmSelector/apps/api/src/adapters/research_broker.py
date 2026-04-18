from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from urllib.parse import parse_qs, quote_plus, urljoin, urlparse

import httpx

from adapters.prompt_executor import PromptExecutor
from config import settings
from models.method_card import Citation, MethodEvidenceCard, ResearchEvidenceResult
from models.problem_spec import ProblemSpec, ProblemType


@dataclass
class RetrievedSource:
    source_id: str
    url: str
    title: str
    source_type: str
    snippet: str = ""
    authors: list[str] | None = None
    published_at: str | None = None

    def to_prompt_item(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "url": self.url,
            "title": self.title,
            "source_type": self.source_type,
            "snippet": self.snippet,
            "authors": self.authors or [],
            "published_at": self.published_at,
        }


class BaseResearchProvider:
    def run_research(self, problem_spec: ProblemSpec) -> ResearchEvidenceResult:
        raise NotImplementedError


class FixtureResearchProvider(BaseResearchProvider):
    def run_research(self, problem_spec: ProblemSpec) -> ResearchEvidenceResult:
        # First check for AI4SI domain hints
        if problem_spec.domain_hint:
            return self._run_ai4si_research(problem_spec)
        
        # Fall back to standard archetype-based research
        if problem_spec.problem_type == ProblemType.MATCHING:
            cards = [
                MethodEvidenceCard(method_family="integer_programming", archetypes_supported=["matching"], assumptions=["Utility scores are meaningful"], data_requirements=["beneficiary and mentor features"], constraint_support="native", fairness_implications=["Can encode allocation floors explicitly"], implementation_burden="medium", interpretability="high", failure_modes=["Bad utility weights produce bad matches"], baseline=False, confidence="high", citations=[Citation(source_id="fixture-matching-1", url="fixture://matching/integer_programming", title="Matching fixture", source_type="fixture")]),
                MethodEvidenceCard(method_family="rules_based_scoring", archetypes_supported=["matching"], assumptions=["Simple compatibility heuristics are adequate"], data_requirements=["basic profile fields"], constraint_support="approximate", fairness_implications=["Can hide subjective scoring choices"], implementation_burden="low", interpretability="high", failure_modes=["Misses globally optimal feasible assignments"], baseline=True, non_ml_alternative=True, confidence="high", citations=[Citation(source_id="fixture-matching-2", url="fixture://matching/rules", title="Rules fixture", source_type="fixture")]),
                MethodEvidenceCard(method_family="embedding_recommender", archetypes_supported=["matching"], assumptions=["Large historical match outcomes exist"], data_requirements=["large labeled history"], constraint_support="weak", fairness_implications=["Opaque recommendation logic"], implementation_burden="high", interpretability="low", failure_modes=["Poor fit for small nonprofit datasets"], confidence="low", citations=[Citation(source_id="fixture-matching-3", url="fixture://matching/recommender", title="Recommender fixture", source_type="fixture")]),
            ]
            return ResearchEvidenceResult(search_queries=["beneficiary matching integer programming capacity fairness", "mentor matching min-cost flow baseline rules"], candidate_method_families=[c.method_family for c in cards], evidence_cards=cards)
        
        if problem_spec.problem_type == ProblemType.FORECASTING:
            cards = [
                MethodEvidenceCard(method_family="time_series_forecasting", archetypes_supported=["forecasting"], assumptions=["Useful historical demand exists"], data_requirements=["historical demand time series"], constraint_support="external solver", fairness_implications=["Needs explicit service-floor constraints downstream"], implementation_burden="medium", interpretability="medium", failure_modes=["Past stockouts can censor demand"], confidence="high", citations=[Citation(source_id="fixture-forecasting-1", url="fixture://forecasting/time_series", title="Forecasting fixture", source_type="fixture")]),
                MethodEvidenceCard(method_family="linear_programming", archetypes_supported=["allocation"], assumptions=["Costs and capacities can be formalised"], data_requirements=["forecast outputs and constraints"], constraint_support="native", fairness_implications=["Can encode service floors"], implementation_burden="medium", interpretability="high", failure_modes=["Objective mis-specification can distort allocation"], baseline=True, non_ml_alternative=True, confidence="high", citations=[Citation(source_id="fixture-forecasting-2", url="fixture://forecasting/lp", title="Allocation fixture", source_type="fixture")]),
                MethodEvidenceCard(method_family="deep_learning_forecast", archetypes_supported=["forecasting"], assumptions=["Large stable time series corpus exists"], data_requirements=["large training history"], constraint_support="external solver", fairness_implications=["Harder to inspect errors by subgroup"], implementation_burden="high", interpretability="low", failure_modes=["Overkill for small operational datasets"], confidence="low", citations=[Citation(source_id="fixture-forecasting-3", url="fixture://forecasting/deep", title="Deep fixture", source_type="fixture")]),
            ]
            return ResearchEvidenceResult(search_queries=["forecasting downstream planning probabilistic forecasting service constraints", "inventory allocation linear programming baseline"], candidate_method_families=[c.method_family for c in cards], evidence_cards=cards)
        
        # Default to PREDICTION archetype
        cards = [
            MethodEvidenceCard(method_family="logistic_regression", archetypes_supported=["prediction"], assumptions=["Tabular risk signals are informative"], data_requirements=["case-level historical data"], constraint_support="external thresholding", fairness_implications=["Needs calibration and subgroup review"], implementation_burden="low", interpretability="high", failure_modes=["Can optimize a biased proxy label"], baseline=True, confidence="high", citations=[Citation(source_id="fixture-risk-1", url="fixture://risk/logistic", title="Risk fixture", source_type="fixture")]),
            MethodEvidenceCard(method_family="gradient_boosted_trees", archetypes_supported=["prediction"], assumptions=["Nonlinear tabular interactions matter"], data_requirements=["clean labeled case history"], constraint_support="external thresholding", fairness_implications=["Needs fairness monitoring"], implementation_burden="medium", interpretability="medium", failure_modes=["Harder to explain than linear baselines"], confidence="high", citations=[Citation(source_id="fixture-risk-2", url="fixture://risk/gbt", title="GBT fixture", source_type="fixture")]),
            MethodEvidenceCard(method_family="manual_triage", archetypes_supported=["prediction"], assumptions=["Case workers can apply stable manual rules"], data_requirements=["basic administrative fields"], constraint_support="manual", fairness_implications=["Human inconsistency can also be biased"], implementation_burden="low", interpretability="high", failure_modes=["Does not scale consistently"], baseline=True, non_ml_alternative=True, confidence="medium", citations=[Citation(source_id="fixture-risk-3", url="fixture://risk/manual", title="Manual triage fixture", source_type="fixture")]),
        ]
        return ResearchEvidenceResult(search_queries=["risk prediction intervention prioritization calibration fairness baseline", "simple baseline manual triage logistic regression"], candidate_method_families=[c.method_family for c in cards], evidence_cards=cards)
    
    def _run_ai4si_research(self, problem_spec: ProblemSpec) -> ResearchEvidenceResult:
        """Return domain-specific methods for AI4SI optimization problems."""
        domain = problem_spec.domain_hint.lower() if problem_spec.domain_hint else None
        
        if domain == "rmab":
            cards = [
                MethodEvidenceCard(method_family="restless_bandits", archetypes_supported=["sequential_decision"], assumptions=["Stationary or slowly-evolving arm dynamics", "Benefit of knowing state evolution"], data_requirements=["historical engagement/outcome paths", "arm state features"], constraint_support="native", fairness_implications=["Can encode service floors and equitable coverage constraints"], implementation_burden="high", interpretability="medium", failure_modes=["Model misspecification of arm dynamics can compound over time"], baseline=False, confidence="high", citations=[Citation(source_id="ai4si-rmab-1", url="ai4si://rmab/whittle_index", title="Whittle Index RMAB", source_type="ai4si")]),
                MethodEvidenceCard(method_family="decision_focused_learning", archetypes_supported=["sequential_decision"], assumptions=["End-to-end differentiability possible", "Downstream optimizer is differentiable"], data_requirements=["labeled trajectories", "ability to backpropagate through optimizer"], constraint_support="native", fairness_implications=["Can jointly optimize for fairness and efficiency"], implementation_burden="very_high", interpretability="low", failure_modes=["Gradient signal can be weak or misleading"], baseline=False, confidence="high", citations=[Citation(source_id="ai4si-rmab-2", url="ai4si://rmab/dfl", title="Decision-Focused Learning", source_type="ai4si")]),
                MethodEvidenceCard(method_family="contextual_bandits", archetypes_supported=["sequential_decision"], assumptions=["Context or arm features are informative"], data_requirements=["feature vectors, historical feedback"], constraint_support="external control", fairness_implications=["Features can embed or amplify existing biases"], implementation_burden="medium", interpretability="medium", failure_modes=["Exploration-exploitation tradeoff can be unstable"], baseline=True, non_ml_alternative=False, confidence="high", citations=[Citation(source_id="ai4si-rmab-3", url="ai4si://rmab/contextual", title="Contextual Bandits", source_type="ai4si")]),
            ]
            return ResearchEvidenceResult(search_queries=["restless multi-armed bandits maternal health", "whittle index RMAB fairness constraints", "decision-focused learning optimization"], candidate_method_families=[c.method_family for c in cards], evidence_cards=cards)
        
        elif domain == "game_theory":
            cards = [
                MethodEvidenceCard(method_family="stackelberg_games", archetypes_supported=["game_theoretic"], assumptions=["Leader commits first and has information advantage", "Adversary or other player plays optimally"], data_requirements=["utility functions or estimated payoffs"], constraint_support="native", fairness_implications=["Can encode fairness in leader objective or constraints"], implementation_burden="medium", interpretability="high", failure_modes=["Utility misspecification leads to poor equilibrium"], baseline=False, confidence="high", citations=[Citation(source_id="ai4si-game-1", url="ai4si://game/stackelberg", title="Stackelberg Games", source_type="ai4si")]),
                MethodEvidenceCard(method_family="nash_equilibrium", archetypes_supported=["game_theoretic"], assumptions=["No single actor has commitment power", "Mutual best response characterization exists"], data_requirements=["payoff matrices or continuous utility models"], constraint_support="approximate via constraints", fairness_implications=["Equilibrium may not be fair; fairness requires separate design"], implementation_burden="high", interpretability="low", failure_modes=["Multiple equilibria may exist; selection is non-obvious"], baseline=False, confidence="high", citations=[Citation(source_id="ai4si-game-2", url="ai4si://game/nash", title="Nash Equilibrium", source_type="ai4si")]),
                MethodEvidenceCard(method_family="mixed_integer_programming", archetypes_supported=["game_theoretic", "allocation"], assumptions=["Game structure can be encoded as integer constraints"], data_requirements=["strategic payoffs and feasible action sets"], constraint_support="native", fairness_implications=["Can encode equity constraints directly"], implementation_burden="medium", interpretability="high", failure_modes=["Computational intractability for large instances"], baseline=True, non_ml_alternative=True, confidence="high", citations=[Citation(source_id="ai4si-game-3", url="ai4si://game/mip", title="MIP Formulation", source_type="ai4si")]),
            ]
            return ResearchEvidenceResult(search_queries=["stackelberg game security wildlife protection", "game-theoretic optimization fairness", "nash equilibrium computation"], candidate_method_families=[c.method_family for c in cards], evidence_cards=cards)
        
        elif domain == "multi_objective_rl":
            cards = [
                MethodEvidenceCard(method_family="multi_objective_reinforcement_learning", archetypes_supported=["multi_objective"], assumptions=["Multiple objectives can be jointly optimized", "Pareto frontier is computable"], data_requirements=["reward signals for each objective", "environment or simulator"], constraint_support="native via reward design", fairness_implications=["Can directly optimize welfare functions (egalitarian, utilitarian, etc.)"], implementation_burden="very_high", interpretability="low", failure_modes=["Value function approximation error multiples across objectives"], baseline=False, confidence="high", citations=[Citation(source_id="ai4si-morl-1", url="ai4si://morl/pareto", title="Multi-Objective RL", source_type="ai4si")]),
                MethodEvidenceCard(method_family="social_welfare_optimization", archetypes_supported=["multi_objective"], assumptions=["Social welfare function can be defined", "Preferences over welfare criteria are stable"], data_requirements=["outcome data, stakeholder preference elicitation"], constraint_support="native", fairness_implications=["Welfare function choice directly affects fairness"], implementation_burden="high", interpretability="very_high", failure_modes=["Welfare aggregation can obscure individual harms"], baseline=False, confidence="high", citations=[Citation(source_id="ai4si-morl-2", url="ai4si://morl/welfare", title="Social Welfare", source_type="ai4si")]),
                MethodEvidenceCard(method_family="policy_portfolio", archetypes_supported=["multi_objective"], assumptions=["Portfolio of simple policies can approximate Pareto frontier"], data_requirements=["access to policy evaluation or simulation"], constraint_support="native", fairness_implications=["Each policy can be separately audited for fairness"], implementation_burden="medium", interpretability="high", failure_modes=["Portfolio may not cover entire trade-off space"], baseline=True, confidence="medium", citations=[Citation(source_id="ai4si-morl-3", url="ai4si://morl/portfolio", title="Policy Portfolio", source_type="ai4si")]),
            ]
            return ResearchEvidenceResult(search_queries=["multi-objective RL welfare functions", "Pareto optimization social impact", "policy portfolio fairness"], candidate_method_families=[c.method_family for c in cards], evidence_cards=cards)
        
        elif domain == "decision_focused_learning":
            cards = [
                MethodEvidenceCard(method_family="decision_focused_learning", archetypes_supported=["decision_focused"], assumptions=["Downstream optimizer is differentiable or has known gradient", "End-to-end training is feasible"], data_requirements=["labeled outcomes", "access to optimization layer"], constraint_support="native", fairness_implications=["Can optimize predictions directly for fairness metrics"], implementation_burden="very_high", interpretability="medium", failure_modes=["Gradient pathology or weak signal can destabilize training"], baseline=False, confidence="high", citations=[Citation(source_id="ai4si-dfl-1", url="ai4si://dfl/end2end", title="Decision-Focused Learning", source_type="ai4si")]),
                MethodEvidenceCard(method_family="predict_then_optimize", archetypes_supported=["decision_focused"], assumptions=["Prediction and optimization can be decoupled"], data_requirements=["historical outcomes, optimization target data"], constraint_support="native in optimize step", fairness_implications=["Fairness must be enforced separately in optimizer"], implementation_burden="medium", interpretability="high", failure_modes=["Prediction error compounds into suboptimal decisions"], baseline=True, non_ml_alternative=False, confidence="high", citations=[Citation(source_id="ai4si-dfl-2", url="ai4si://dfl/predict_then_opt", title="Predict-Then-Optimize", source_type="ai4si")]),
                MethodEvidenceCard(method_family="inverse_optimization", archetypes_supported=["decision_focused"], assumptions=["Expert decisions reveal their underlying objective"], data_requirements=["observed expert actions and context"], constraint_support="infers constraints from data", fairness_implications=["Can recover implicit fairness criteria"], implementation_burden="high", interpretability="medium", failure_modes=["Expert behavior may not be optimal or consistent"], baseline=False, confidence="medium", citations=[Citation(source_id="ai4si-dfl-3", url="ai4si://dfl/inverse", title="Inverse Optimization", source_type="ai4si")]),
            ]
            return ResearchEvidenceResult(search_queries=["decision-focused learning end-to-end", "predict-then-optimize fairness", "inverse optimization"], candidate_method_families=[c.method_family for c in cards], evidence_cards=cards)
        
        # Default to generic prediction methods for unknown domains
        cards = [
            MethodEvidenceCard(method_family="logistic_regression", archetypes_supported=["prediction"], assumptions=["Tabular risk signals are informative"], data_requirements=["case-level historical data"], constraint_support="external thresholding", fairness_implications=["Needs calibration and subgroup review"], implementation_burden="low", interpretability="high", failure_modes=["Can optimize a biased proxy label"], baseline=True, confidence="high", citations=[Citation(source_id="fixture-risk-1", url="fixture://risk/logistic", title="Risk fixture", source_type="fixture")]),
            MethodEvidenceCard(method_family="gradient_boosted_trees", archetypes_supported=["prediction"], assumptions=["Nonlinear tabular interactions matter"], data_requirements=["clean labeled case history"], constraint_support="external thresholding", fairness_implications=["Needs fairness monitoring"], implementation_burden="medium", interpretability="medium", failure_modes=["Harder to explain than linear baselines"], confidence="high", citations=[Citation(source_id="fixture-risk-2", url="fixture://risk/gbt", title="GBT fixture", source_type="fixture")]),
        ]
        return ResearchEvidenceResult(search_queries=["optimization prediction intervention prioritization"], candidate_method_families=[c.method_family for c in cards], evidence_cards=cards)


class LiveResearchProvider(BaseResearchProvider):
    def __init__(self, prompt_executor: PromptExecutor | None = None, fixture_provider: FixtureResearchProvider | None = None) -> None:
        self.prompts = prompt_executor or PromptExecutor()
        self.fixture = fixture_provider or FixtureResearchProvider()
        self._timeout = settings.research_timeout_seconds
        self._headers = {"User-Agent": settings.research_user_agent}

    def run_research(self, problem_spec: ProblemSpec) -> ResearchEvidenceResult:
        queries = self._build_queries(problem_spec)[: settings.research_max_queries]
        try:
            retrieved = self._retrieve_sources(queries)
            if not retrieved:
                return self._fallback(problem_spec, queries, "No live sources were retrieved.")
            result = self.prompts.run_research_evidence(problem_spec, queries, [item.to_prompt_item() for item in retrieved])
            normalized = self._normalize_result(result, queries)
            if not normalized.evidence_cards or not any(card.baseline for card in normalized.evidence_cards):
                reason = "Live research did not yield enough grounded baseline evidence to continue confidently."
                return self._fallback(problem_spec, queries, reason)
            return normalized
        except Exception as exc:
            return self._fallback(problem_spec, queries, f"Live research failed: {exc}")

    def _retrieve_sources(self, queries: list[str]) -> list[RetrievedSource]:
        academic: list[RetrievedSource] = []
        web: list[RetrievedSource] = []
        if settings.research_academic_first:
            for query in queries:
                academic.extend(self._search_openalex(query))
            academic = self._dedupe_sources(academic)
            if len(academic) < settings.research_min_sources_before_web_fallback:
                for query in queries:
                    web.extend(self._search_duckduckgo(query))
            return self._dedupe_sources(academic + web)[: settings.research_max_sources]
        for query in queries:
            academic.extend(self._search_openalex(query))
            web.extend(self._search_duckduckgo(query))
        return self._dedupe_sources(academic + web)[: settings.research_max_sources]

    def _build_queries(self, problem_spec: ProblemSpec) -> list[str]:
        base = problem_spec.optimisation_subproblem or problem_spec.problem_summary
        queries = [
            f"{base} {problem_spec.problem_type.value} methods social impact",
            f"{base} baseline non-ml operational decision support",
        ]
        if problem_spec.constraints:
            constraint_terms = " ".join(constraint.name for constraint in problem_spec.constraints[:2])
            queries.append(f"{base} {constraint_terms} fairness constraints")
        elif problem_spec.fairness_harm_constraints:
            queries.append(f"{base} fairness constraints auditability")
        
        # Option 3: Enrich queries with domain-specific terms when domain_hint is present
        if problem_spec.domain_hint:
            domain = problem_spec.domain_hint.lower()
            if domain == "rmab":
                queries.insert(0, "restless multi-armed bandits fairness optimal control")
                queries.insert(1, "Whittle index sequential decision social impact")
            elif domain == "game_theory":
                queries.insert(0, "game theory stackelberg nash equilibrium social welfare")
                queries.insert(1, "mechanism design fairness strategic interaction")
            elif domain == "multi_objective_rl":
                queries.insert(0, "multi-objective reinforcement learning Pareto welfare")
                queries.insert(1, "reward learning social impact fairness RL")
            elif domain == "decision_focused_learning":
                queries.insert(0, "decision-focused learning end-to-end fairness optimization")
                queries.insert(1, "predict-then-optimize prescriptive analytics")
            elif domain == "graph_optimization":
                queries.insert(0, "graph optimization network design social welfare")
            elif domain == "inverse_rl":
                queries.insert(0, "inverse reinforcement learning preference learning fairness")
            elif domain == "robust_optimization":
                queries.insert(0, "robust optimization uncertainty fairness constraints")
        
        return [query.strip() for query in queries if query.strip()]

    def _search_openalex(self, query: str) -> list[RetrievedSource]:
        if settings.research_academic_provider != "openalex":
            return []
        params = {
            "search": query,
            "per-page": str(settings.research_max_results_per_query),
        }
        if settings.research_openalex_email:
            params["mailto"] = settings.research_openalex_email
        url = settings.research_openalex_base_url.rstrip("/") + "/works"
        with httpx.Client(timeout=self._timeout, headers=self._headers, follow_redirects=True) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
        payload = response.json()
        results: list[RetrievedSource] = []
        for item in payload.get("results", []):
            title = str(item.get("display_name") or "").strip()
            url = self._first_non_empty(
                item.get("primary_location", {}).get("landing_page_url"),
                item.get("primary_location", {}).get("pdf_url"),
                item.get("id"),
            )
            if not title or not url:
                continue
            abstract = self._openalex_abstract(item.get("abstract_inverted_index") or {})
            authors = [author.get("author", {}).get("display_name", "") for author in item.get("authorships", [])[:3]]
            results.append(
                RetrievedSource(
                    source_id=str(item.get("id") or url),
                    url=url,
                    title=title,
                    source_type="academic",
                    snippet=abstract,
                    authors=[author for author in authors if author],
                    published_at=str(item.get("publication_year") or "") or None,
                )
            )
        return results

    def _search_duckduckgo(self, query: str) -> list[RetrievedSource]:
        if settings.research_web_provider != "duckduckgo":
            return []
        url = settings.research_duckduckgo_base_url
        with httpx.Client(timeout=self._timeout, headers=self._headers, follow_redirects=True) as client:
            response = client.get(url, params={"q": query})
            response.raise_for_status()
        html = response.text
        anchors = re.findall(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, flags=re.IGNORECASE | re.DOTALL)
        snippets = re.findall(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>|<div[^>]*class="result__snippet"[^>]*>(.*?)</div>', html, flags=re.IGNORECASE | re.DOTALL)
        results: list[RetrievedSource] = []
        for index, anchor in enumerate(anchors[: settings.research_max_results_per_query], start=1):
            href, raw_title = anchor
            snippet_pair = snippets[index - 1] if index - 1 < len(snippets) else ("", "")
            snippet = self._clean_html(snippet_pair[0] or snippet_pair[1])
            resolved = self._resolve_duckduckgo_url(href)
            title = self._clean_html(raw_title)
            if not resolved or not title:
                continue
            results.append(
                RetrievedSource(
                    source_id=f"duckduckgo-{quote_plus(query)}-{index}",
                    url=resolved,
                    title=title,
                    source_type="web",
                    snippet=snippet,
                )
            )
        return results

    def _normalize_result(self, result: ResearchEvidenceResult, queries: list[str]) -> ResearchEvidenceResult:
        normalized_cards: list[MethodEvidenceCard] = []
        dropped = 0
        for card in result.evidence_cards:
            citations = self._normalize_citations(card.citations)
            if not citations:
                dropped += 1
                continue
            normalized_cards.append(
                MethodEvidenceCard(
                    method_family=card.method_family,
                    archetypes_supported=card.archetypes_supported,
                    assumptions=card.assumptions,
                    data_requirements=card.data_requirements,
                    constraint_support=card.constraint_support,
                    fairness_implications=card.fairness_implications,
                    implementation_burden=card.implementation_burden,
                    interpretability=card.interpretability,
                    failure_modes=card.failure_modes,
                    non_ml_alternative=card.non_ml_alternative,
                    baseline=card.baseline,
                    confidence=card.confidence,
                    citations=citations,
                )
            )
        assumptions = list(result.assumptions)
        if dropped:
            assumptions.append(f"Dropped {dropped} evidence cards because they lacked usable citations.")
        return ResearchEvidenceResult(
            search_queries=queries,
            candidate_method_families=[card.method_family for card in normalized_cards],
            evidence_cards=normalized_cards,
            assumptions=assumptions,
            missing_fields=result.missing_fields,
        )

    def _normalize_citations(self, citations: list[Citation]) -> list[Citation]:
        normalized: list[Citation] = []
        seen: set[tuple[str, str]] = set()
        for citation in citations:
            url = citation.url.strip()
            title = citation.title.strip()
            if not url or not title:
                continue
            key = (url.lower(), title.lower())
            if key in seen:
                continue
            seen.add(key)
            normalized.append(
                Citation(
                    source_id=citation.source_id or title.lower().replace(" ", "-"),
                    url=url,
                    title=title,
                    source_type=citation.source_type or "web",
                )
            )
        return normalized

    def _fallback(self, problem_spec: ProblemSpec, queries: list[str], reason: str) -> ResearchEvidenceResult:
        fallback = self.fixture.run_research(problem_spec)
        assumptions = [reason, "Fell back to fixture research evidence to preserve pipeline continuity."]
        assumptions.extend(fallback.assumptions)
        return ResearchEvidenceResult(
            search_queries=queries or fallback.search_queries,
            candidate_method_families=fallback.candidate_method_families,
            evidence_cards=fallback.evidence_cards,
            assumptions=assumptions,
            missing_fields=fallback.missing_fields,
        )

    def _dedupe_sources(self, sources: list[RetrievedSource]) -> list[RetrievedSource]:
        deduped: list[RetrievedSource] = []
        seen: set[tuple[str, str]] = set()
        for source in sources:
            key = (source.url.strip().lower(), source.title.strip().lower())
            if key in seen or not source.url.strip() or not source.title.strip():
                continue
            seen.add(key)
            deduped.append(source)
        return deduped

    def _resolve_duckduckgo_url(self, href: str) -> str:
        href = unescape(href)
        parsed = urlparse(href)
        if parsed.netloc.endswith("duckduckgo.com"):
            query = parse_qs(parsed.query)
            target = query.get("uddg", [""])[0]
            if target:
                return target
        if href.startswith("//"):
            return "https:" + href
        if href.startswith("http://") or href.startswith("https://"):
            return href
        return urljoin("https://duckduckgo.com", href)

    def _openalex_abstract(self, inverted_index: dict[str, list[int]]) -> str:
        if not inverted_index:
            return ""
        words: list[tuple[int, str]] = []
        for word, positions in inverted_index.items():
            for position in positions:
                words.append((position, word))
        words.sort(key=lambda item: item[0])
        return " ".join(word for _, word in words[:120])

    def _clean_html(self, value: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescape(value))).strip()

    def _first_non_empty(self, *values: object) -> str:
        for value in values:
            text = str(value or "").strip()
            if text:
                return text
        return ""


class ResearchBroker:
    def __init__(self, provider: BaseResearchProvider | None = None) -> None:
        self.provider = provider or self._build_provider()

    def run_research(self, problem_spec: ProblemSpec) -> ResearchEvidenceResult:
        return self.provider.run_research(problem_spec)

    def _build_provider(self) -> BaseResearchProvider:
        if settings.research_mode == "live":
            return LiveResearchProvider()
        return FixtureResearchProvider()
