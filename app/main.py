"""Semantic Kernel + Azure PostgreSQL — Orders Assistant (FastAPI service).

Real SK kernel + native plugin. Works offline (mock table); set
POSTGRES_CONNECTION_STRING for Azure Database for PostgreSQL.
Run:  uvicorn app.main:app --reload
"""

from fastapi import FastAPI

from app.kernel_app import OrderQuery, OrderResult, ask_orders, get_settings

settings = get_settings()
app = FastAPI(title="Semantic Kernel + Azure PostgreSQL — Orders Assistant", version="0.1.0")


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "framework": "semantic-kernel",
        "store": "postgres" if settings.use_postgres else "mock",
    }


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {
        "service": "agentic-ai-azure-sk-postgresql",
        "endpoint": "/api/v1/orders/ask",
        "store": "postgres" if settings.use_postgres else "mock",
        "docs": "/docs",
    }


@app.post("/api/v1/orders/ask", response_model=OrderResult, tags=["sk-postgresql"])
async def orders_ask(payload: OrderQuery) -> OrderResult:
    return await ask_orders(payload)
