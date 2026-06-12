"""Semantic Kernel + Azure Database for PostgreSQL — Orders Assistant.

A real **Semantic Kernel** ``Kernel`` with a native plugin (`OrdersPlugin`) whose
`@kernel_function` looks up an order. The data accessor runs **offline** against an
in-memory table by default, and against **Azure Database for PostgreSQL** (via
`psycopg`, lazy-imported) when `POSTGRES_CONNECTION_STRING` is set.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from semantic_kernel import Kernel
from semantic_kernel.functions import KernelArguments, kernel_function


# ── settings ────────────────────────────────────────────────────────────
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    postgres_connection_string: str = ""

    @property
    def use_postgres(self) -> bool:
        return bool(self.postgres_connection_string)


@lru_cache
def get_settings() -> Settings:
    return Settings()


# ── schemas ─────────────────────────────────────────────────────────────
class OrderQuery(BaseModel):
    question: str = Field(..., min_length=1, description="Natural-language order question.")


class OrderResult(BaseModel):
    order_id: str | None
    found: bool
    status: str
    customer: str | None = None
    total: float | None = None
    answer: str
    mode: str
    invoked_via: str


# ── data access (in-memory mock | Azure PostgreSQL) ─────────────────────
_ORDERS = {
    "ORD-1001": {"status": "shipped", "customer": "Jordan Avery", "total": 129.50},
    "ORD-1002": {"status": "processing", "customer": "Sam Rivera", "total": 42.00},
    "ORD-2001": {"status": "delivered", "customer": "Lee Chen", "total": 318.75},
}


def _fetch_order(order_id: str) -> dict | None:
    s = get_settings()
    key = (order_id or "").strip().upper()
    if not s.use_postgres:
        return _ORDERS.get(key)
    # Real Azure Database for PostgreSQL lookup (lazy import).
    import psycopg

    with psycopg.connect(s.postgres_connection_string) as conn:
        row = conn.execute(
            "SELECT status, customer, total FROM orders WHERE order_id = %s", (key,)
        ).fetchone()
    if not row:
        return None
    return {"status": row[0], "customer": row[1], "total": float(row[2])}


# ── the Semantic Kernel native plugin ───────────────────────────────────
class OrdersPlugin:
    @kernel_function(name="get_order_status", description="Look up an order by id; returns JSON.")
    def get_order_status(self, order_id: str) -> str:
        rec = _fetch_order(order_id)
        if rec is None:
            return json.dumps({"order_id": order_id, "found": False, "status": "not_found"})
        return json.dumps({"order_id": order_id, "found": True, **rec})


@lru_cache
def build_kernel() -> Kernel:
    kernel = Kernel()
    kernel.add_plugin(OrdersPlugin(), plugin_name="orders")
    return kernel


_ORDER_RE = re.compile(r"\bORD-\d{3,6}\b", re.IGNORECASE)


def _extract_order(text: str) -> str | None:
    m = _ORDER_RE.search(text)
    return m.group(0).upper() if m else None


async def ask_orders(req: OrderQuery) -> OrderResult:
    kernel = build_kernel()
    order_id = _extract_order(req.question)
    result = await kernel.invoke(
        plugin_name="orders", function_name="get_order_status",
        arguments=KernelArguments(order_id=order_id or ""),
    )
    data = json.loads(str(result))
    if not order_id:
        answer = "Please include an order id like ORD-1001."
    elif not data.get("found"):
        answer = f"No order found for {order_id}."
    else:
        answer = f"Order {order_id} for {data['customer']} is {data['status']} (total ${data['total']:.2f})."
    return OrderResult(
        order_id=order_id,
        found=bool(data.get("found")),
        status=data.get("status", "unknown"),
        customer=data.get("customer"),
        total=data.get("total"),
        answer=answer,
        mode="postgres" if get_settings().use_postgres else "mock",
        invoked_via="semantic-kernel native plugin",
    )
