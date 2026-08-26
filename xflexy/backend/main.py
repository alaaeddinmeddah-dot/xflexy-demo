import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse

from xflexy.admin.routes import router as admin_router
from xflexy.backend.dependencies import get_order_service, get_request_repository, get_user_service
from xflexy.backend.schemas import (
    CreateOrderPayload,
    OrderResponse,
    OrderStatusResponse,
    RegisterUserPayload,
    TopUpPayload,
    TopUpResponse,
    UserResponse,
)
from xflexy.core.config import get_settings
from xflexy.core.logging import configure_logging
from xflexy.core.security import require_admin_api_key
from xflexy.database.connection import get_connection
from xflexy.database.repositories import FlexyRequestRepository
from xflexy.database.schema import initialize_schema
from xflexy.flexy.factory import get_flexy_provider
from xflexy.flexy.provider import FlexyTopUpRequest
from xflexy.services.order_service import OrderService
from xflexy.services.user_service import UserService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings)
    app.state.settings = settings
    app.state.flexy_provider = get_flexy_provider(settings)

    with get_connection(settings.database_url) as connection:
        initialize_schema(connection)

    logger.info("xflexy backend started in %s mode", settings.environment)
    yield
    logger.info("xflexy backend stopped")


app = FastAPI(title="xflexy API", version="0.2.0", lifespan=lifespan)
app.include_router(admin_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "xflexy"}


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def demo_home() -> str:
    return """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>xflexy Demo</title>
        <style>
          body { margin: 0; font-family: Arial, sans-serif; background: #f6f7f9; color: #16202a; }
          main { max-width: 920px; margin: 0 auto; padding: 40px 20px; }
          h1 { margin: 0 0 8px; font-size: 36px; }
          p { line-height: 1.6; }
          .panel { background: white; border: 1px solid #d9dee5; border-radius: 8px; padding: 20px; margin: 18px 0; }
          .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
          .step { border-left: 4px solid #2563eb; padding: 10px 12px; background: #f9fbff; }
          code { background: #eef1f5; padding: 2px 5px; border-radius: 4px; }
          a { color: #1d4ed8; font-weight: 700; }
        </style>
      </head>
      <body>
        <main>
          <h1>xflexy Demo</h1>
          <p>Safe public demo for the mock Flexy order workflow. No real payments, no real Flexy provider, no SIM integration, and no real Telegram token are connected.</p>
          <section class="panel">
            <h2>Demo Flow</h2>
            <div class="grid">
              <div class="step">1. Register a Telegram demo user</div>
              <div class="step">2. Create a mock Flexy order</div>
              <div class="step">3. Show <code>awaiting_payment</code></div>
              <div class="step">4. Confirm mock payment with protected admin key</div>
              <div class="step">5. Execute Mock Flexy</div>
              <div class="step">6. Reach <code>completed</code> with a fake reference</div>
            </div>
          </section>
          <section class="panel">
            <h2>Open The API Demo</h2>
            <p><a href="/docs">Swagger UI</a> lets you run the public demo endpoints. Admin/internal endpoints require the demo admin key and do not expose it in the page.</p>
            <p>Health check: <a href="/health"><code>/health</code></a></p>
          </section>
          <section class="panel">
            <h2>Safety Boundary</h2>
            <p>This is a presentation build only. Everything involving money, Flexy execution, Telegram live updates, and operator integration remains mocked.</p>
          </section>
        </main>
      </body>
    </html>
    """


@app.post("/users/register", response_model=UserResponse)
def register_user(
    payload: RegisterUserPayload,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = service.register_telegram_user(
        telegram_user_id=payload.telegram_user_id,
        username=payload.username,
        full_name=payload.full_name,
    )
    return UserResponse(**user.__dict__)


@app.post("/orders", response_model=OrderResponse)
def create_order(
    payload: CreateOrderPayload,
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    try:
        order = service.create_order(
            telegram_user_id=payload.telegram_user_id,
            phone_number=payload.phone_number,
            amount=payload.amount,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return OrderResponse(**order.__dict__)


@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: str,
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    try:
        order = service.get_order(order_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return OrderResponse(**order.__dict__)


@app.get("/orders/{order_id}/status", response_model=OrderStatusResponse)
def get_order_status(
    order_id: str,
    service: OrderService = Depends(get_order_service),
) -> OrderStatusResponse:
    try:
        order = service.get_order(order_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return OrderStatusResponse(order_id=order.order_id, status=order.status)


@app.get("/users/{telegram_user_id}/orders", response_model=list[OrderResponse])
def list_user_orders(
    telegram_user_id: int,
    service: OrderService = Depends(get_order_service),
) -> list[OrderResponse]:
    return [OrderResponse(**order.__dict__) for order in service.list_user_orders(telegram_user_id)]


@app.post(
    "/internal/mock-payments/{order_id}/confirm",
    response_model=OrderResponse,
    dependencies=[Depends(require_admin_api_key)],
)
def confirm_mock_payment(
    order_id: str,
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    try:
        order = service.confirm_mock_payment(order_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return OrderResponse(**order.__dict__)


@app.post("/flexy/top-up", response_model=TopUpResponse)
def create_top_up(
    payload: TopUpPayload,
    repository: FlexyRequestRepository = Depends(get_request_repository),
) -> TopUpResponse:
    result = app.state.flexy_provider.top_up(
        FlexyTopUpRequest(
            phone_number=payload.phone_number,
            amount=payload.amount,
        )
    )
    request = repository.create(
        telegram_user_id=payload.telegram_user_id,
        phone_number=payload.phone_number,
        amount=payload.amount,
        status=result.status,
        provider_reference=result.reference,
    )
    return TopUpResponse(
        request_id=request.id,
        status=result.status,
        provider_reference=result.reference,
        message=result.message,
    )
