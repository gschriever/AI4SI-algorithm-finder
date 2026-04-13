# Algorithm Selector

Algorithm Selector is a FastAPI backend for turning a rough problem narrative into a grounded recommendation about what kind of algorithmic or non-algorithmic approach fits the problem.

The current version is built around an iterative clarification loop. It does not assume the first narrative is complete. It first diagnoses whether the problem is operationally well specified, asks targeted follow-up questions when key information is missing, and only proceeds to research, ranking, governance review, and explanation once the problem is sufficiently clarified.

## Objective

The app is designed to answer a practical question:

Given a social-sector or operations problem, is there a defensible optimization or decision-support problem here, and if so, what method family is most appropriate?

It is intentionally conservative.
- It separates broad social goals from narrower operational decisions.
- It prefers clarification over premature recommendation.
- It includes governance checks before and after ranking.
- It keeps baseline and non-ML options in scope.
- It does not recommend full automation by default.

## How The App Operates

The backend runs as a stateful session workflow.

1. A client starts a session with an initial narrative.
2. The system performs intake diagnosis.
   Output: an `IntakeDiagnosisResult` describing the social goal, operational decision, constraints, likely problem archetype, and missing information.
3. The system formalizes the current state into a `ProblemSpec`.
   Output: a structured canonical problem specification suitable for governance review and later ranking.
4. The system checks whether the problem is sufficiently specified.
   Output: either a set of clarifying questions or permission to continue.
5. If key information is missing, the session pauses and returns targeted clarification questions.
   Output: `pending_questions` plus partial artifacts.
6. The client answers those questions and resumes the session.
   Output: the diagnosis and problem spec are regenerated using the new clarifications.
7. Once enough information exists, the system runs a governance pre-check.
   Output: either a veto or permission to continue.
8. If the problem passes pre-check, the system generates candidate evidence and method cards.
   Output: `ResearchEvidenceResult`.
9. The system ranks candidate method families using the ranking prompt and supplied evidence cards.
   Output: `RankedMethods` with model-assigned scores, rationales, and supporting methods.
10. The system performs final governance review.
    Output: a `GovernanceDecision` that may constrain usage to decision support only.
11. The system produces a plain-language recommendation package.
    Output: `RecommendationPackage` with summary, recommendation, alternatives, risks, safeguards, and next steps.
12. All artifacts are written to the session folder for later retrieval.

## Key Components

### API Layer
- [apps/api/src/main.py](./apps/api/src/main.py) creates the FastAPI application and mounts the routes.
- [apps/api/src/routes/pipeline.py](./apps/api/src/routes/pipeline.py) exposes the session workflow endpoints.

### Workflow Coordinator
- [apps/api/src/services/coordinator_service.py](./apps/api/src/services/coordinator_service.py) orchestrates the full session lifecycle.
- It is responsible for pause/resume behavior, stage ordering, and persistence.

### Prompted Modules
- [apps/api/src/adapters/prompt_executor.py](./apps/api/src/adapters/prompt_executor.py) runs the prompted diagnosis, formalization, and explanation steps.
- [apps/api/src/prompt_library.yaml](./apps/api/src/prompt_library.yaml) contains the prompt library used by the executor.
- [apps/api/src/adapters/prompt_library.py](./apps/api/src/adapters/prompt_library.py) loads those prompts.

### Clarification Logic
- [apps/api/src/services/clarification_service.py](./apps/api/src/services/clarification_service.py) converts missing information into targeted follow-up questions.
- It controls whether the workflow pauses for more information and caps clarification rounds.

### Governance And Ranking
- [apps/api/src/services/governance_service.py](./apps/api/src/services/governance_service.py) applies pre-check and final governance decisions.
- [apps/api/src/services/ranking_service.py](./apps/api/src/services/ranking_service.py) delegates candidate-method ranking to the prompt executor.
- [apps/api/src/adapters/research_broker.py](./apps/api/src/adapters/research_broker.py) dispatches to fixture or live research providers behind a stable broker interface.

### Models And Storage
- [apps/api/src/models](./apps/api/src/models) contains the Pydantic models that define the runtime data contracts.
- [apps/api/src/storage/session_repo.py](./apps/api/src/storage/session_repo.py) persists stage outputs and session state under `data/sessions/<session_id>/`.

## API Endpoints

### `POST /api/pipeline/start`
Starts a new session.

Input:
- `session_id`
- `narrative`
- optional `prior_state`

Output:
- `status = needs_clarification`, `completed`, or `vetoed`
- partial or full `artifacts`
- `pending_questions` when more information is required

### `POST /api/pipeline/answer`
Submits answers to the current session's pending questions and resumes the workflow.

Input:
- `session_id`
- `answers[]` with `question_id` and `answer`

Output:
- updated `PipelineResponse`
- either another clarification round or a completed/vetoed result

### `GET /api/pipeline/session/{session_id}`
Returns the persisted session state, including artifacts, pending questions, and prior answers.

### `POST /api/pipeline/run`
Alias for `POST /api/pipeline/start`.

## Outputs And Persistence

Each session writes JSON artifacts under `data/sessions/<session_id>/`.

Typical files include:
- `01_intake_diagnosis.json`
- `02_problem_spec.json`
- `03_governance_precheck.json`
- `04_research.json`
- `05_ranking.json`
- `06_governance_final.json`
- `07_recommendation.json`
- `session_state.json`

These files are generated outputs, not schema sources.
The runtime source of truth is the Pydantic model layer in `apps/api/src/models/`.

## Prompt And Model Behavior

The prompt library is designed for iterative elicitation.
- Diagnosis is expected to preserve unresolved gaps rather than hide them.
- Formalization is expected to produce a usable but clarification-aware `ProblemSpec`.
- Research should only occur once the problem is sufficiently specified.
- Explanation is generated only after the workflow has enough information to make a defensible recommendation.

In fixture mode, the app uses deterministic mock behavior for diagnosis, formalization, research, ranking, and explanation. In live mode, the prompt executor can call an OpenAI-compatible chat-completions endpoint, and the research broker can retrieve academic-first evidence from OpenAlex with DuckDuckGo fallback for broader practical sources.

## Research Modes

### `research_mode=fixture`
- Uses deterministic fixture evidence cards and fixture citations.
- Best for offline demos, local development, and tests.

### `research_mode=live`
- Uses a provider-backed live research pipeline behind `ResearchBroker`.
- Generates search queries from the `ProblemSpec`.
- Retrieves scholarly sources from OpenAlex first.
- Falls back to DuckDuckGo HTML results when scholarly retrieval is too sparse.
- Sends retrieved source metadata and snippets through the `research_evidence` prompt to normalize them into `ResearchEvidenceResult`.
- Drops evidence cards that do not have at least one usable citation.
- Falls back to fixture evidence when live retrieval or extraction is too weak to keep the pipeline moving safely.

Key live research settings live in [apps/api/src/config.py](./apps/api/src/config.py), including `research_mode`, `research_academic_first`, provider endpoints, timeouts, and source/result limits.

## Run

```bash
uvicorn main:app --app-dir apps/api/src --reload
```

## Current Constraints

- Live research depends on external HTTP access and source availability; when retrieval is sparse or fails, the broker intentionally falls back to fixture evidence.
- The DuckDuckGo fallback uses lightweight HTML parsing, so it is less stable than a formal search API.
- The local environment may require installing FastAPI and related dependencies before running the API server.
- Structured-output enforcement against Pydantic-derived JSON Schema has not been completed yet; the live prompt path still relies on JSON-mode plus model validation.
- Automated tests currently cover the broker/provider split, fallback logic, citation normalization, and a mocked coordinator integration path, but they do not exercise real external provider calls.
