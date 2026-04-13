import sys
import unittest
from unittest.mock import patch

sys.path.append(r'apps/api/src')

from adapters.prompt_executor import PromptExecutor
from adapters.research_broker import FixtureResearchProvider, LiveResearchProvider, ResearchBroker, RetrievedSource
from config import settings
from models.method_card import Citation, MethodEvidenceCard, ResearchEvidenceResult
from models.session import AnswerClarificationsRequest, ClarificationAnswer, StartSessionRequest
from services.coordinator_service import CoordinatorService


class ResearchPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_research_mode = settings.research_mode
        self.original_academic_first = settings.research_academic_first
        self.original_min_sources = settings.research_min_sources_before_web_fallback
        self.original_llm_provider = settings.llm_provider
        self.original_llm_api_key = settings.llm_api_key
        settings.llm_provider = 'fixture'
        settings.llm_api_key = ''

    def tearDown(self) -> None:
        settings.research_mode = self.original_research_mode
        settings.research_academic_first = self.original_academic_first
        settings.research_min_sources_before_web_fallback = self.original_min_sources
        settings.llm_provider = self.original_llm_provider
        settings.llm_api_key = self.original_llm_api_key

    def _problem_spec(self, narrative: str):
        executor = PromptExecutor()
        diagnosis = executor._fixture_intake_diagnosis(narrative, None)
        return executor._fixture_formalization(diagnosis)

    def test_broker_selects_provider_by_research_mode(self) -> None:
        settings.research_mode = 'fixture'
        self.assertIsInstance(ResearchBroker().provider, FixtureResearchProvider)

        settings.research_mode = 'live'
        self.assertIsInstance(ResearchBroker().provider, LiveResearchProvider)

    def test_live_provider_builds_queries_from_problem_spec(self) -> None:
        provider = LiveResearchProvider()
        problem_spec = self._problem_spec('We need to match beneficiaries to mentors given mentor capacity and compatibility constraints.')

        queries = provider._build_queries(problem_spec)

        self.assertGreaterEqual(len(queries), 2)
        self.assertTrue(any('baseline' in query for query in queries))
        self.assertTrue(any('capacity' in query for query in queries))

    def test_normalize_citations_dedupes_and_drops_incomplete(self) -> None:
        provider = LiveResearchProvider()
        citations = [
            Citation(source_id='a', url='https://example.com/paper', title='Paper', source_type='academic'),
            Citation(source_id='b', url='https://example.com/paper', title='Paper', source_type='academic'),
            Citation(source_id='c', url='', title='Missing URL', source_type='web'),
        ]

        normalized = provider._normalize_citations(citations)

        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0].url, 'https://example.com/paper')

    def test_live_provider_falls_back_to_web_when_academic_results_sparse(self) -> None:
        provider = LiveResearchProvider()
        settings.research_academic_first = True
        settings.research_min_sources_before_web_fallback = 3

        with patch.object(provider, '_search_openalex', return_value=[RetrievedSource('a1', 'https://academic.example/1', 'Academic Source', 'academic')]) as academic_mock:
            with patch.object(provider, '_search_duckduckgo', return_value=[RetrievedSource('w1', 'https://web.example/1', 'Web Source', 'web')]) as web_mock:
                results = provider._retrieve_sources(['matching methods'])

        self.assertTrue(academic_mock.called)
        self.assertTrue(web_mock.called)
        self.assertEqual({item.source_type for item in results}, {'academic', 'web'})

    def test_live_provider_returns_fixture_fallback_when_retrieval_fails(self) -> None:
        provider = LiveResearchProvider()
        problem_spec = self._problem_spec('We need to match beneficiaries to mentors given mentor capacity and compatibility constraints.')

        with patch.object(provider, '_retrieve_sources', side_effect=RuntimeError('network failed')):
            result = provider.run_research(problem_spec)

        self.assertGreater(len(result.evidence_cards), 0)
        self.assertTrue(any('Fell back to fixture research evidence' in assumption for assumption in result.assumptions))
        self.assertTrue(any(card.baseline for card in result.evidence_cards))

    def test_live_provider_normalizes_prompt_backed_research_output(self) -> None:
        provider = LiveResearchProvider()
        problem_spec = self._problem_spec('We need to match beneficiaries to mentors given mentor capacity and compatibility constraints.')
        retrieved = [RetrievedSource('s1', 'https://example.com/paper', 'Matching Paper', 'academic', snippet='integer programming for matching')]
        llm_result = ResearchEvidenceResult(
            search_queries=['matching methods'],
            candidate_method_families=['integer_programming', 'rules_based_scoring'],
            evidence_cards=[
                MethodEvidenceCard(
                    method_family='integer_programming',
                    archetypes_supported=['matching'],
                    assumptions=['Utility score is available'],
                    data_requirements=['beneficiary features'],
                    constraint_support='native',
                    fairness_implications=['Supports fairness floors'],
                    implementation_burden='medium',
                    interpretability='high',
                    failure_modes=['Bad utility design'],
                    confidence='high',
                    citations=[Citation(source_id='s1', url='https://example.com/paper', title='Matching Paper', source_type='academic')],
                ),
                MethodEvidenceCard(
                    method_family='rules_based_scoring',
                    archetypes_supported=['matching'],
                    assumptions=['Heuristics are acceptable'],
                    data_requirements=['basic profiles'],
                    constraint_support='approximate',
                    fairness_implications=['Needs review'],
                    implementation_burden='low',
                    interpretability='high',
                    failure_modes=['Can miss global optimum'],
                    baseline=True,
                    non_ml_alternative=True,
                    confidence='medium',
                    citations=[Citation(source_id='s2', url='https://example.com/rules', title='Rules Overview', source_type='web')],
                ),
            ],
        )

        with patch.object(provider, '_retrieve_sources', return_value=retrieved):
            with patch.object(provider.prompts, 'run_research_evidence', return_value=llm_result):
                result = provider.run_research(problem_spec)

        self.assertGreater(len(result.evidence_cards), 0)
        self.assertEqual(result.evidence_cards[0].method_family, 'integer_programming')
        self.assertEqual(result.evidence_cards[0].citations[0].title, 'Matching Paper')
        self.assertTrue(any(card.baseline for card in result.evidence_cards))
        self.assertFalse(any('Dropped 1 evidence cards' in assumption for assumption in result.assumptions))

    def test_coordinator_completes_with_mocked_live_research(self) -> None:
        settings.research_mode = 'live'
        retrieved = [RetrievedSource('s1', 'https://example.com/matching', 'Matching Overview', 'academic', snippet='integer programming and rules based matching')]
        research_result = ResearchEvidenceResult(
            search_queries=['matching methods'],
            candidate_method_families=['integer_programming', 'rules_based_scoring'],
            evidence_cards=[
                MethodEvidenceCard(
                    method_family='integer_programming',
                    archetypes_supported=['matching'],
                    assumptions=['Utility scores are meaningful'],
                    data_requirements=['beneficiary and mentor features'],
                    constraint_support='native',
                    fairness_implications=['Can encode allocation floors explicitly'],
                    implementation_burden='medium',
                    interpretability='high',
                    failure_modes=['Bad utility weights produce bad matches'],
                    confidence='high',
                    citations=[Citation(source_id='s1', url='https://example.com/matching', title='Matching Overview', source_type='academic')],
                ),
                MethodEvidenceCard(
                    method_family='rules_based_scoring',
                    archetypes_supported=['matching'],
                    assumptions=['Simple compatibility heuristics are adequate'],
                    data_requirements=['basic profile fields'],
                    constraint_support='approximate',
                    fairness_implications=['Can hide subjective scoring choices'],
                    implementation_burden='low',
                    interpretability='high',
                    failure_modes=['Misses globally optimal feasible assignments'],
                    baseline=True,
                    non_ml_alternative=True,
                    confidence='medium',
                    citations=[Citation(source_id='s1', url='https://example.com/matching', title='Matching Overview', source_type='academic')],
                ),
            ],
        )

        with patch('adapters.research_broker.LiveResearchProvider._retrieve_sources', return_value=retrieved):
            with patch('adapters.prompt_executor.PromptExecutor.run_research_evidence', return_value=research_result):
                service = CoordinatorService()
                start = service.start_session(StartSessionRequest(
                    session_id='live-research-test',
                    narrative='We need to match beneficiaries to mentors given mentor capacity and compatibility constraints.',
                ))
                answer = service.answer_clarifications(AnswerClarificationsRequest(
                    session_id='live-research-test',
                    answers=[ClarificationAnswer(question_id=start.pending_questions[0].question_id, answer='Use 70% match quality, 20% fairness, and 10% mentor workload balance.')],
                ))

        self.assertEqual(answer.status, 'completed')
        self.assertEqual(answer.artifacts.research.evidence_cards[0].citations[0].url, 'https://example.com/matching')
        self.assertTrue(any(card.baseline for card in answer.artifacts.research.evidence_cards))


if __name__ == '__main__':
    unittest.main()
