from fastapi import APIRouter

from models.session import AnswerClarificationsRequest, PipelineResponse, SessionState, StartSessionRequest
from services.coordinator_service import CoordinatorService

router = APIRouter(prefix="/pipeline", tags=["pipeline"])
service = CoordinatorService()


@router.post("/start", response_model=PipelineResponse)
def start_session(request: StartSessionRequest) -> PipelineResponse:
    return service.start_session(request)


@router.post("/answer", response_model=PipelineResponse)
def answer_clarifications(request: AnswerClarificationsRequest) -> PipelineResponse:
    return service.answer_clarifications(request)


@router.get("/session/{session_id}", response_model=SessionState)
def get_session(session_id: str) -> SessionState:
    return service.get_session(session_id)


@router.post("/run", response_model=PipelineResponse)
def run_pipeline(request: StartSessionRequest) -> PipelineResponse:
    return service.run(request)
