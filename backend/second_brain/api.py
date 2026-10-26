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
from starlette.exceptions import HTTPException

from .config import Settings
from .db import make_engine
from .muse import Muse
from .schemas import RANGES, Approval, ContextEdit, PlanRequest, TaskCreate, TaskEdit
from .service import Service


def create_app(settings=None, engine=None, muse=None):
    settings = settings or Settings()
    settings.validate_hosted()
    engine = engine or make_engine(settings.database_url)
    service = Service(
        engine, muse or Muse(settings), settings.mock_user_id, settings.meta_model
    )
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
        # Resolve repository UI assets independently of the command's cwd.
        page = FilePath(__file__).resolve().parents[2] / "frontend" / "dashboard.py"
        if not page.is_file():
            # Vercel may install the package into site-packages; it preserves
            # included frontend assets relative to the project working directory.
            page = FilePath.cwd() / "frontend" / "dashboard.py"
        return HTMLResponse(
            run_path(str(page))["PAGE"], headers={"Cache-Control": "no-store"}
        )

    def identity(authorization: Annotated[str | None, Header()] = None):
        token = settings.mock_auth_token
        if token and not secrets.compare_digest(
            authorization or "", "Bearer " + token.get_secret_value()
        ):
            raise HTTPException(401, "Valid demo bearer token required")
        return service

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
        return {"status": "ok", "authentication": "mock", "model": settings.meta_model}

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

    @app.post("/api/runs/{run_id}/approve")
    def approve(run_id: UUID, body: Approval, s: Annotated[Service, Depends(identity)]):
        return s.review(str(run_id), body)

    @app.post("/api/runs/{run_id}/reject")
    def reject(run_id: UUID, s: Annotated[Service, Depends(identity)]):
        return s.review(str(run_id), reject=True)

    return app
