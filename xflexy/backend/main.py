import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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
STATIC_DIR = Path(__file__).resolve().parents[1] / "frontend" / "static"


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
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "xflexy"}


@app.get("/", include_in_schema=False)
def demo_home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/admin-ui", include_in_schema=False)
def admin_ui() -> FileResponse:
    return FileResponse(STATIC_DIR / "admin.html")


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
