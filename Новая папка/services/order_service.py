"""Сервис для работы с заказами."""

import logging
from typing import List, Optional
from decimal import Decimal

from domain.models import Cart, Order, OrderStatus, OrderItem, Product
from domain.exceptions import (
    CartEmptyError, CartNotFoundError, OrderNotFoundError,
    InsufficientStockError, BusinessRuleViolation, ValidationError
)
from repositories.interfaces import CartRepository, OrderRepository, ProductRepository

logger = logging.getLogger(__name__)


class OrderService:
    """Сервис для управления заказами."""

    def __init__(
        self,
        order_repository: OrderRepository,
        cart_repository: CartRepository,
        product_repository: ProductRepository
    ):
        self._order_repo = order_repository
        self._cart_repo = cart_repository
        self._product_repo = product_repository

    def create_order_from_cart(
        self,
        user_id: int,
        discount_percentage: Optional[Decimal] = None
    ) -> Order:
        """
        Создать заказ из корзины.

        Args:
            user_id: ID пользователя
            discount_percentage: Процент скидки (0-100)

        Returns:
            Созданный заказ
        """
        logger.info(f"Creating order from cart for user: {user_id}")

        # Получаем корзину
        cart = self._cart_repo.get_by_user_id(user_id)
        if not cart:
            raise CartNotFoundError(f"Корзина для пользователя {user_id} не найдена")

        if not cart.items:
            raise CartEmptyError("Невозможно создать заказ из пустой корзины")

        # Проверяем наличие всех товаров
        for item in cart.items:
            product = self._product_repo.get_by_id(item.product_id)
            if not product:
                raise BusinessRuleViolation(f"Товар с ID {item.product_id} больше не доступен")
            if not product.has_stock(item.quantity):
                raise InsufficientStockError(
                    f"Недостаточно товара '{product.name}'. "
                    f"Доступно: {product.stock}, запрошено: {item.quantity}"
                )

        # Создаем позиции заказа
        order_items = []
        for item in cart.items:
            order_items.append(OrderItem(
                product_id=item.product_id,
                product_name=item.product_name,
                quantity=item.quantity,
                unit_price=item.unit_price
            ))

        # Создаем заказ
        order = Order(
            id=None,
            user_id=user_id,
            items=order_items,
            status=OrderStatus.PENDING,
            total_price=cart.total_price,
            discount_amount=Decimal('0')
        )

        # Применяем скидку, если указана
        if discount_percentage:
            order.apply_discount(discount_percentage)

        # Сохраняем заказ
        saved_order = self._order_repo.save(order)

        # Уменьшаем количество товаров на складе
        for item in cart.items:
            product = self._product_repo.get_by_id(item.product_id)
            if product:
                product.reduce_stock(item.quantity)
                self._product_repo.save(product)

        # Очищаем корзину
        cart.clear()
        self._cart_repo.save(cart)

        logger.info(f"Order created with id: {saved_order.id}, total: {saved_order.final_price}")
        return saved_order

    def get_order(self, order_id: int) -> Order:
        """Получить заказ по ID."""
        order = self._order_repo.get_by_id(order_id)
        if not order:
            raise OrderNotFoundError(f"Заказ с ID {order_id} не найден")
        return order

    def get_user_orders(self, user_id: int) -> List[Order]:
        """Получить все заказы пользователя."""
        return self._order_repo.get_by_user_id(user_id)

    def get_orders_by_status(self, status: OrderStatus) -> List[Order]:
        """Получить заказы по статусу."""
        return self._order_repo.get_by_status(status)

    def update_order_status(self, order_id: int, new_status: OrderStatus) -> Order:
        """Обновить статус заказа."""
        logger.info(f"Updating order {order_id} status to: {new_status.value}")

        order = self.get_order(order_id)

        # Проверка возможности смены статуса
        if order.status == OrderStatus.CANCELLED:
            raise BusinessRuleViolation("Нельзя изменить статус отменённого заказа")
        if order.status == OrderStatus.DELIVERED:
            raise BusinessRuleViolation("Нельзя изменить статус доставленного заказа")

        # Если заказ отменяется - возвращаем товары на склад
        if new_status == OrderStatus.CANCELLED:
            if not order.can_be_cancelled():
                raise BusinessRuleViolation(f"Заказ в статусе {order.status.value} нельзя отменить")
            self._restore_order_items(order)

        return self._order_repo.update_status(order_id, new_status)

    def apply_discount_to_order(self, order_id: int, discount_percentage: Decimal) -> Order:
        """Применить скидку к заказу."""
        logger.info(f"Applying {discount_percentage}% discount to order {order_id}")

        order = self.get_order(order_id)

        if order.status != OrderStatus.PENDING:
            raise BusinessRuleViolation(f"Нельзя применить скидку к заказу в статусе {order.status.value}")

        order.apply_discount(discount_percentage)
        return self._order_repo.save(order)

    def _restore_order_items(self, order: Order) -> None:
        """Вернуть товары на склад при отмене заказа."""
        for item in order.items:
            product = self._product_repo.get_by_id(item.product_id)
            if product:
                product.increase_stock(item.quantity)
                self._product_repo.save(product)
        logger.info(f"Restored stock for cancelled order {order.id}")

    def calculate_order_total(self, order_id: int) -> Decimal:
        """Рассчитать общую сумму заказа."""
        order = self.get_order(order_id)
        return order.final_price