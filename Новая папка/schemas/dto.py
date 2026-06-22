"""DTO схемы для валидации данных."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class ProductCreateDTO:
    """DTO для создания товара."""
    name: str
    description: Optional[str] = None
    price: Decimal = Decimal('0')
    stock: int = 0
    category: str = ""


@dataclass
class ProductUpdateDTO:
    """DTO для обновления товара."""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    stock: Optional[int] = None
    category: Optional[str] = None


@dataclass
class CartItemDTO:
    """DTO позиции корзины."""
    product_id: int
    quantity: int


@dataclass
class OrderCreateDTO:
    """DTO для создания заказа."""
    user_id: int
    discount_percentage: Optional[Decimal] = None


@dataclass
class OrderUpdateDTO:
    """DTO для обновления заказа."""
    status: str