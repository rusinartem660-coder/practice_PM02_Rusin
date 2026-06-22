"""Доменные модели интернет-магазина."""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional


class OrderStatus(Enum):
    """Статусы заказа."""
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@dataclass
class Product:
    """Модель товара."""
    id: Optional[int]
    name: str
    description: str
    price: Decimal
    stock: int
    category: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def has_stock(self, quantity: int) -> bool:
        """Проверка наличия товара в нужном количестве."""
        return self.stock >= quantity

    def reduce_stock(self, quantity: int) -> None:
        """Уменьшить количество товара."""
        if not self.has_stock(quantity):
            raise InsufficientStockError(
                f"Недостаточно товара '{self.name}'. "
                f"Доступно: {self.stock}, запрошено: {quantity}"
            )
        self.stock -= quantity
        self.updated_at = datetime.now()

    def increase_stock(self, quantity: int) -> None:
        """Увеличить количество товара."""
        if quantity < 0:
            raise InvalidQuantityError("Количество для увеличения не может быть отрицательным")
        self.stock += quantity
        self.updated_at = datetime.now()


@dataclass
class CartItem:
    """Позиция в корзине."""
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal

    @property
    def total_price(self) -> Decimal:
        """Общая стоимость позиции."""
        return self.unit_price * self.quantity


@dataclass
class Cart:
    """Корзина покупателя."""
    id: Optional[int]
    user_id: int
    items: List[CartItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def total_price(self) -> Decimal:
        """Общая стоимость корзины."""
        return sum(item.total_price for item in self.items)

    @property
    def item_count(self) -> int:
        """Количество позиций в корзине."""
        return len(self.items)

    @property
    def total_quantity(self) -> int:
        """Общее количество товаров в корзине."""
        return sum(item.quantity for item in self.items)

    def add_item(self, product: Product, quantity: int) -> None:
        """Добавить товар в корзину."""
        if quantity <= 0:
            raise InvalidQuantityError("Количество должно быть положительным")

        if not product.has_stock(quantity):
            raise InsufficientStockError(
                f"Недостаточно товара '{product.name}'. "
                f"Доступно: {product.stock}, запрошено: {quantity}"
            )

        # Обновляем существующую позицию или добавляем новую
        for item in self.items:
            if item.product_id == product.id:
                new_quantity = item.quantity + quantity
                if not product.has_stock(new_quantity):
                    raise InsufficientStockError(
                        f"Недостаточно товара '{product.name}'. "
                        f"Доступно: {product.stock}, всего в корзине: {new_quantity}"
                    )
                item.quantity = new_quantity
                self.updated_at = datetime.now()
                return

        self.items.append(CartItem(
            product_id=product.id,
            product_name=product.name,
            quantity=quantity,
            unit_price=product.price
        ))
        self.updated_at = datetime.now()

    def remove_item(self, product_id: int) -> None:
        """Удалить товар из корзины."""
        for i, item in enumerate(self.items):
            if item.product_id == product_id:
                del self.items[i]
                self.updated_at = datetime.now()
                return
        raise NotFoundError(f"Товар с ID {product_id} не найден в корзине")

    def update_quantity(self, product_id: int, quantity: int) -> None:
        """Обновить количество товара в корзине."""
        if quantity < 0:
            raise InvalidQuantityError("Количество не может быть отрицательным")

        for item in self.items:
            if item.product_id == product_id:
                if quantity == 0:
                    self.remove_item(product_id)
                    return
                item.quantity = quantity
                self.updated_at = datetime.now()
                return
        raise NotFoundError(f"Товар с ID {product_id} не найден в корзине")

    def clear(self) -> None:
        """Очистить корзину."""
        self.items.clear()
        self.updated_at = datetime.now()


@dataclass
class OrderItem:
    """Позиция заказа."""
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal

    @property
    def total_price(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass
class Order:
    """Заказ."""
    id: Optional[int]
    user_id: int
    items: List[OrderItem]
    status: OrderStatus
    total_price: Decimal
    discount_amount: Decimal = Decimal('0')
    final_price: Decimal = field(init=False)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        self.final_price = self.total_price - self.discount_amount
        if self.final_price < 0:
            self.final_price = Decimal('0')

    def apply_discount(self, percentage: Decimal) -> Decimal:
        """Применить скидку в процентах."""
        if not 0 <= percentage <= 100:
            raise DiscountNotApplicableError("Процент скидки должен быть от 0 до 100")
        self.discount_amount = (self.total_price * percentage) / 100
        self.final_price = self.total_price - self.discount_amount
        self.updated_at = datetime.now()
        return self.discount_amount

    def apply_fixed_discount(self, amount: Decimal) -> Decimal:
        """Применить фиксированную скидку."""
        if amount < 0:
            raise DiscountNotApplicableError("Сумма скидки не может быть отрицательной")
        if amount > self.total_price:
            raise DiscountNotApplicableError("Сумма скидки не может превышать сумму заказа")
        self.discount_amount = amount
        self.final_price = self.total_price - self.discount_amount
        self.updated_at = datetime.now()
        return self.discount_amount

    def can_be_cancelled(self) -> bool:
        """Можно ли отменить заказ."""
        return self.status in (OrderStatus.PENDING, OrderStatus.PAID)