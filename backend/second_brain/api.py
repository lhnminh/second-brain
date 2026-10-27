import secrets
from pathlib import Path as FilePath
from runpy import run_path
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, Header, Path, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException

from .config import Settings
from .db import make_engine
from .muse import Muse
from .schemas import (
    RANGES,
    Approval,
    ContextEdit,
    ConversationApproval,
    ConversationRequest,
    PlanRequest,
    SessionCreate,
    TaskCreate,
    TaskEdit,
)
from .service import Service
from .session import COOKIE_NAME, SESSION_SECONDS, create_session, valid_session
from .voice import MAX_AUDIO_BYTES, VoiceFailure, VoiceTranscriber


def create_app(settings=None, engine=None, muse=None, transcriber=None):
    settings = settings or Settings()
    settings.validate_hosted()
    engine = engine or make_engine(settings.database_url)
    service = Service(
        engine, muse or Muse(settings), settings.mock_user_id, settings.meta_model
    )
    transcriber = transcriber or VoiceTranscriber(settings)
    app = FastAPI(title="Visual Second Brain", version="0.1.0")
    app.state.engine = engine
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_methods=["GET", "POST", "PATCH", "PUT"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def dashboard_page():
        return frontend_page("dashboard.py")

    @app.get("/dev", response_class=HTMLResponse, include_in_schema=False)
    def dev_page():
        return frontend_page("dev.py")

    def frontend_page(filename):
        # Resolve repository UI assets independently of the command's cwd.
        page = FilePath(__file__).resolve().parents[2] / "frontend" / filename
        if not page.is_file():
            # Vercel may install the package into site-packages; it preserves
            # included frontend assets relative to the project working directory.
            page = FilePath.cwd() / "frontend" / filename
        return HTMLResponse(
            run_path(str(page))["PAGE"], headers={"Cache-Control": "no-store"}
        )

    def same_origin(request):
        origin = request.headers.get("origin")
        expected = str(request.base_url).rstrip("/")
        # Vercel terminates public HTTPS before forwarding to the Python app.
        if settings.vercel:
            expected = "https://" + request.headers["host"]
        if origin is not None and origin != expected:
            raise HTTPException(403, "Session requests must use the app's origin")

    def identity(
        request: Request, authorization: Annotated[str | None, Header()] = None
    ):
        token = settings.mock_auth_token
        if token:
            if authorization is not None:
                if not secrets.compare_digest(
                    authorization.encode(),
                    ("Bearer " + token.get_secret_value()).encode(),
                ):
                    raise HTTPException(401, "Valid demo access token required")
            elif valid_session(settings, request.cookies.get(COOKIE_NAME)):
                if request.method not in {"GET", "HEAD", "OPTIONS"}:
                    same_origin(request)
            else:
                raise HTTPException(401, "Connect with your demo access token")
        return service

    @app.middleware("http")
    async def private_api_responses(request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.post("/api/session")
    def connect(body: SessionCreate, request: Request):
        same_origin(request)
        token = settings.mock_auth_token
        if token and not secrets.compare_digest(
            body.token.get_secret_value().encode(), token.get_secret_value().encode()
        ):
            raise HTTPException(401, "Valid demo access token required")
        response = JSONResponse({"authenticated": True, "authentication": "mock"})
        if token:
            response.set_cookie(
                COOKIE_NAME,
                create_session(settings),
                max_age=SESSION_SECONDS,
                httponly=True,
                secure=bool(settings.vercel) or request.url.scheme == "https",
                samesite="strict",
                path="/api",
            )
        return response

    @app.delete("/api/session")
    def disconnect(request: Request):
        same_origin(request)
        response = JSONResponse({"authenticated": False})
        response.delete_cookie(
            COOKIE_NAME,
            path="/api",
            httponly=True,
            samesite="strict",
            secure=bool(settings.vercel) or request.url.scheme == "https",
        )
        return response

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code, content={"error": {"message": exc.detail}}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # Exclude submitted values from validation responses.
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "message": "Invalid request",
                    "fields": [
                        {"path": list(e["loc"]), "message": e["msg"]}
                        for e in exc.errors()
                    ],
                }
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError):
        return JSONResponse(
            status_code=503,
            content={
                "error": {"message": "Database unavailable; changes were not saved"}
            },
        )

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "authentication": "mock",
            "model": settings.meta_model,
            "demo_access_required": bool(settings.mock_auth_token),
        }

    @app.get("/api/dashboard")
    def dashboard(s: Annotated[Service, Depends(identity)]):
        return s.dashboard()

    @app.get("/api/importance-levels")
    def importance(s: Annotated[Service, Depends(identity)]):
        return {key: {"min": low, "max": high} for key, (low, high) in RANGES.items()}

    @app.post("/api/tasks", status_code=201)
    def create_task(body: TaskCreate, s: Annotated[Service, Depends(identity)]):
        return s.create_task(body)

    @app.patch("/api/tasks/{task_id}")
    def edit_task(
        task_id: UUID, body: TaskEdit, s: Annotated[Service, Depends(identity)]
    ):
        return s.edit_task(str(task_id), body)

    @app.put("/api/context/{context_id}")
    def context(
        context_id: Annotated[str, Path(pattern=r"^[a-zA-Z0-9_-]{1,100}$")],
        body: ContextEdit,
        s: Annotated[Service, Depends(identity)],
    ):
        return s.save_context(context_id, body)

    @app.post("/api/tasks/{task_id}/plans")
    def plan(
        task_id: UUID, body: PlanRequest, s: Annotated[Service, Depends(identity)]
    ):
        return s.plan(str(task_id), body)

    @app.post("/api/voice/transcribe")
    async def transcribe_voice(
        request: Request, s: Annotated[Service, Depends(identity)]
    ):
        if request.headers.get("content-type", "").split(";")[0].lower() != "audio/wav":
            raise HTTPException(415, "Voice input must be an audio/wav recording")
        audio = bytearray()
        async for chunk in request.stream():
            if len(audio) + len(chunk) > MAX_AUDIO_BYTES:
                raise HTTPException(413, "Recording exceeds the one-minute audio limit")
            audio.extend(chunk)
        try:
            text = await run_in_threadpool(transcriber.transcribe, bytes(audio))
        except VoiceFailure as exc:
            raise HTTPException(exc.status, str(exc)) from None
        return {"transcript": text, "model": settings.meta_voice_model}

    @app.post("/api/conversation")
    def converse(body: ConversationRequest, s: Annotated[Service, Depends(identity)]):
        return s.plan(None, body)

    @app.post("/api/conversation/{run_id}/approve")
    def approve_conversation(
        run_id: UUID,
        body: ConversationApproval,
        s: Annotated[Service, Depends(identity)],
    ):
        return s.review(str(run_id), body, conversation=True)

    @app.post("/api/runs/{run_id}/approve")
    def approve(run_id: UUID, body: Approval, s: Annotated[Service, Depends(identity)]):
        return s.review(str(run_id), body)

    @app.post("/api/runs/{run_id}/reject")
    def reject(run_id: UUID, s: Annotated[Service, Depends(identity)]):
        return s.review(str(run_id), reject=True)

    return app
