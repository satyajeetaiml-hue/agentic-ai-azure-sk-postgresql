# Semantic Kernel + Azure PostgreSQL — Orders Assistant

[![CI](https://github.com/satyajeetaiml-hue/agentic-ai-azure-sk-postgresql/actions/workflows/ci.yml/badge.svg)](https://github.com/satyajeetaiml-hue/agentic-ai-azure-sk-postgresql/actions/workflows/ci.yml)

> Companion project to the *Agentic AI on Azure — Enterprise Master Class*.
> Course hub: [azure-agentic-ai-masterclass](https://github.com/satyajeetaiml-hue/azure-agentic-ai-masterclass).

> ▶️ **Run in VS Code — no Azure needed.** `pip install -r requirements.txt`, then `uvicorn app.main:app --reload` and open http://127.0.0.1:8000/docs. The SK kernel + plugin run **for real** offline; Azure PostgreSQL is optional.

---

## 🎯 What it shows
A **Semantic Kernel** agent skill backed by a **relational database**. A native plugin
(`OrdersPlugin.get_order_status`) reads from an orders table — an in-memory table offline, or
**Azure Database for PostgreSQL** (`psycopg`) when configured.

## 🧩 How it works
- `OrdersPlugin.get_order_status(order_id)` — a `@kernel_function` invoked via the kernel.
- **Mock mode (default):** reads from an in-memory `orders` dict.
- **Postgres mode:** `_fetch_order` runs `SELECT status, customer, total FROM orders WHERE order_id=%s`.

## 🚀 Quick start
```bash
python -m venv .venv && .\.venv\Scripts\Activate.ps1   # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
```bash
curl -X POST http://127.0.0.1:8000/api/v1/orders/ask \
  -H "Content-Type: application/json" -d '{"question": "where is order ORD-1001?"}'
```
Run tests: `pytest -q`. Sample orders: `ORD-1001` (shipped), `ORD-1002` (processing), `ORD-2001` (delivered).

## ☁️ Wire Azure Database for PostgreSQL
```bash
az postgres flexible-server create -g <rg> -n my-pg --tier Burstable --sku-name Standard_B1ms
# create an `orders` table: order_id (text pk), status (text), customer (text), total (numeric)
```
Set `POSTGRES_CONNECTION_STRING` in `.env` (use `sslmode=require`; prefer Entra/Managed Identity auth in
production). `GET /health` reports `"store": "postgres"`.

## 🧰 Tech stack
Semantic Kernel, Azure Database for PostgreSQL (`psycopg`), FastAPI, Pydantic v2.

## 📁 Structure
```
app/kernel_app.py  # Kernel, OrdersPlugin, data access (mock | postgres)
app/main.py        # POST /api/v1/orders/ask
tests/test_app.py
```

## 📄 License
MIT — see [`LICENSE`](LICENSE).
