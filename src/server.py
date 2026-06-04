from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .agents import create_financial_analyst_agent
from .config import get_settings
from .schemas import QueryRequest, QueryResponse


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Meridian Wealth Financial Analyst Agent",
        description="FastAPI backend for the LangChain v1 ReAct financial analyst agent.",
        version="0.1.0",
    )

    app.mount(
        "/static",
        StaticFiles(directory=settings.root_dir / "static"),
        name="static",
    )

    @app.on_event("startup")
    def startup_event() -> None:
        app.state.settings = settings
        app.state.agent = create_financial_analyst_agent()

    @app.get("/")
    def root() -> RedirectResponse:
        return RedirectResponse(url="/static/index.html")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/query", response_model=QueryResponse)
    def query_agent(payload: QueryRequest) -> QueryResponse:
        try:
            result = app.state.agent.invoke(
                {"messages": [{"role": "user", "content": payload.query}]}
            )
            final_message = result["messages"][-1]
            answer = getattr(final_message, "content", final_message)
            return QueryResponse(answer=str(answer))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    return app
