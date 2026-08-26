# xflexy

Safe phase-two scaffold for a Telegram bot and FastAPI backend for a Flexy-style service.

This project still uses mock-only Flexy and mock-only payment behavior. It does not connect to any real provider, payment gateway, SIM card, or external Flexy API.

## Requirements

- Python 3.11 or newer
- SQLite for the first version
- No real API keys, payment credentials, or Telegram tokens are required for tests

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
pytest
uvicorn xflexy.backend.main:app --reload
```

Open:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

## Configuration

The `.env` file is used for local settings and secrets. Keep real secrets out of Git.

```env
FLEXY_PROVIDER=mock
MOCK_FLEXY_MODE=success
ADMIN_API_KEY=change-me-local-admin-key
MIN_FLEXY_AMOUNT=50
MAX_FLEXY_AMOUNT=50000
PHONE_REGEX=^\+?[0-9]{8,15}$
```

`MOCK_FLEXY_MODE` supports:

- `success`
- `failure`
- `timeout`

## Project Structure

```text
xflexy/
  admin/          Protected admin API routes
  backend/        FastAPI app, schemas, dependencies
  bot/            Telegram bot handlers and conversation setup
  core/           Settings, security, logging, statuses
  database/       SQLite schema and repositories
  flexy/          Flexy provider protocol and mock adapter
  services/       User and order business logic
tests/            Backend, service, and mock provider tests
```

## Main API Endpoints

- `GET /health`
- `POST /users/register`
- `POST /orders`
- `GET /orders/{order_id}`
- `GET /orders/{order_id}/status`
- `GET /users/{telegram_user_id}/orders`
- `POST /internal/mock-payments/{order_id}/confirm`
- `GET /admin/users`
- `GET /admin/orders`
- `GET /admin/payments`
- `GET /admin/operations`

Admin and internal mock endpoints require:

```text
x-admin-api-key: change-me-local-admin-key
```

Use a local test value only. Do not put real keys in source code.

## Order Lifecycle

- `pending`
- `awaiting_payment`
- `paid`
- `processing`
- `completed`
- `cancelled`
- `failed`

The current order creation flow starts new orders in `awaiting_payment` and creates a linked mock payment record in `pending`.

When the protected mock payment confirmation endpoint is called:

1. Payment becomes `confirmed`.
2. Order moves to `paid`.
3. Order moves to `processing`.
4. Mock Flexy is called.
5. Order becomes `completed` or `failed`.

Repeated confirmation for an already completed order is skipped safely.

## Telegram Bot

The bot registers users on `/start` and includes a `/flexy` conversation that collects:

- beneficiary phone number
- amount
- confirm/cancel decision

Tests only verify that the bot application and handlers can be created safely with a fake token. Do not run polling or webhook permanently in this phase.

## Demo

This demo shows the full safe workflow without any real Telegram, payment, SIM, or Flexy provider connection.

### Run The Automated Demo Scenario

From the project root:

```bash
.venv\Scripts\activate
python scripts\demo_scenario.py
```

The script uses FastAPI's local test client and the same application code. It does not start a public server and does not call any external API.

### What The Scenario Does

1. Registers a demo Telegram user:
   - `telegram_user_id`: `424242001`
   - `username`: `demo_customer`
   - `full_name`: `Demo Customer`
2. Creates a Flexy order with demo-only data:
   - phone number: `0555123456`
   - amount: `500`
3. Shows the order in `awaiting_payment`.
4. Calls the protected internal mock payment confirmation endpoint.
5. Moves the order through payment confirmation and mock Flexy execution.
6. Shows the final order in `completed`.
7. Shows the Admin demo dashboard with users, orders, payments, and operations.

### Manual API Demo

Start the API:

```bash
uvicorn xflexy.backend.main:app --reload
```

Then open:

- `http://127.0.0.1:8000/docs`
- `GET /health`

Use these requests in order:

```http
POST /users/register
Content-Type: application/json

{
  "telegram_user_id": 424242001,
  "username": "demo_customer",
  "full_name": "Demo Customer"
}
```

```http
POST /orders
Content-Type: application/json

{
  "telegram_user_id": 424242001,
  "phone_number": "0555123456",
  "amount": 500
}
```

```http
GET /orders/{order_id}/status
```

```http
POST /internal/mock-payments/{order_id}/confirm
x-admin-api-key: change-me-local-admin-key
```

```http
GET /admin/demo-dashboard
x-admin-api-key: change-me-local-admin-key
```

### What The Project Owner Should See

- A user record created once, without duplicate Telegram users.
- A new order with phone number, amount, and `awaiting_payment` status.
- A mock payment moving from `pending` to `confirmed`.
- The order moving to `processing`, then `completed`.
- A fake Flexy reference like `mock-xxxxxxxxxx`.
- The successful operation listed in Admin views.

### Demo Boundaries

Still mock-only:

- Telegram token and live Telegram updates.
- Payment confirmation.
- Flexy execution.
- SIM card or mobile operator integration.
- Any external API integration.

## Safety Notes

- No real payment provider is connected.
- No real Flexy provider is connected.
- No real Telegram token is included.
- No real personal data is needed for tests.
- Mock endpoints are protected with `ADMIN_API_KEY`.

## Public Demo Deployment

The project is ready for a simple Render Web Service deployment.

Recommended settings:

- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn xflexy.backend.main:app --host 0.0.0.0 --port $PORT`
- Health path: `/health`

Set these environment variables in the hosting dashboard:

```env
ENVIRONMENT=demo
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./xflexy.db
FLEXY_PROVIDER=mock
MOCK_FLEXY_MODE=success
MIN_FLEXY_AMOUNT=50
MAX_FLEXY_AMOUNT=50000
PHONE_REGEX=^\+?[0-9]{8,15}$
ADMIN_API_KEY=<demo-admin-key>
TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_SECRET=
```

Do not use real keys. The public page is available at `/`, Swagger at `/docs`, and health check at `/health`.
