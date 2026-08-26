from pydantic import BaseModel, Field


class RegisterUserPayload(BaseModel):
    telegram_user_id: int = Field(gt=0)
    username: str | None = Field(default=None, max_length=64)
    full_name: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: int
    telegram_user_id: int
    username: str | None
    full_name: str
    account_status: str
    registered_at: str


class CreateOrderPayload(BaseModel):
    telegram_user_id: int = Field(gt=0)
    phone_number: str = Field(min_length=6, max_length=32)
    amount: int = Field(gt=0)


class OrderResponse(BaseModel):
    id: int
    order_id: str
    user_id: int
    phone_number: str
    amount: int
    status: str
    flexy_reference: str | None
    flexy_message: str | None
    created_at: str
    updated_at: str


class PaymentResponse(BaseModel):
    id: int
    payment_id: str
    order_id: str
    amount: int
    status: str
    created_at: str
    updated_at: str


class OrderStatusResponse(BaseModel):
    order_id: str
    status: str


class TopUpPayload(BaseModel):
    telegram_user_id: int = Field(gt=0)
    phone_number: str = Field(min_length=6, max_length=32)
    amount: int = Field(gt=0)


class TopUpResponse(BaseModel):
    request_id: int
    status: str
    provider_reference: str
    message: str
