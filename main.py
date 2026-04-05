from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from src.api.routes import router
from src.services import app_state

app = FastAPI(
    title="Supplier Requirements Multimodal RAG",
    description=(
        "FastAPI service for ingesting supplier requirements manuals and answering "
        "grounded questions across text, tables, and page-level visual context."
    ),
    version="1.2.0",
)

app.include_router(router)


@app.on_event("startup")
def startup_event() -> None:
    app_state.initialize()


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    frontend_path = Path(__file__).resolve().parent / "frontend" / "index.html"
    return FileResponse(frontend_path)
