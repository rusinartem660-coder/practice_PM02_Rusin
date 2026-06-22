"""Сервис для работы с корзиной."""

import logging
from typing import Optional

from domain.models import Cart, Product
from domain.exceptions import (
    CartNotFoundError, ProductNotFoundError,
    InvalidQuantityError, InsufficientStockError
)
from repositories.interfaces import CartRepository, ProductRepository

logger = logging.getLogger(__name__)


class CartService:
    """Сервис для управления корзиной."""

    def __init__(
        self,
        cart_repository: CartRepository,
        product_repository: ProductRepository
    ):
        self._cart_repo = cart_repository
        self._product_repo = product_repository

    def get_or_create_cart(self, user_id: int) -> Cart:
        """Получить или создать корзину для пользователя."""
        cart = self._cart_repo.get_by_user_id(user_id)
        if not cart:
            logger.info(f"Creating new cart for user: {user_id}")
            cart = Cart(id=None, user_id=user_id)
            cart = self._cart_repo.save(cart)
        return cart

    def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1) -> Cart:
        """Добавить товар в корзину."""
        logger.info(f"Adding product {product_id} to cart for user {user_id}, quantity: {quantity}")

        if quantity <= 0:
            raise InvalidQuantityError("Количество должно быть положительным")

        # Получаем товар
        product = self._product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError(f"Товар с ID {product_id} не найден")

        # Получаем корзину
        cart = self.get_or_create_cart(user_id)

        # Добавляем товар в корзину
        try:
            cart.add_item(product, quantity)
        except InsufficientStockError:
            logger.warning(f"Insufficient stock for product {product_id}, stock: {product.stock}")
            raise

        # Сохраняем корзину
        return self._cart_repo.save(cart)

    def remove_from_cart(self, user_id: int, product_id: int) -> Cart:
        """Удалить товар из корзины."""
        logger.info(f"Removing product {product_id} from cart for user {user_id}")

        cart = self._cart_repo.get_by_user_id(user_id)
        if not cart:
            raise CartNotFoundError(f"Корзина для пользователя {user_id} не найдена")

        cart.remove_item(product_id)
        return self._cart_repo.save(cart)

    def update_cart_quantity(self, user_id: int, product_id: int, quantity: int) -> Cart:
        """Обновить количество товара в корзине."""
        logger.info(f"Updating quantity for product {product_id} in cart for user {user_id} to {quantity}")

        cart = self._cart_repo.get_by_user_id(user_id)
        if not cart:
            raise CartNotFoundError(f"Корзина для пользователя {user_id} не найдена")

        if quantity < 0:
            raise InvalidQuantityError("Количество не может быть отрицательным")

        # Если количество 0, удаляем товар из корзины
        if quantity == 0:
            return self.remove_from_cart(user_id, product_id)

        # Проверяем наличие товара
        product = self._product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError(f"Товар с ID {product_id} не найден")

        if not product.has_stock(quantity):
            raise InsufficientStockError(
                f"Недостаточно товара '{product.name}'. "
                f"Доступно: {product.stock}, запрошено: {quantity}"
            )

        cart.update_quantity(product_id, quantity)
        return self._cart_repo.save(cart)

    def clear_cart(self, user_id: int) -> Cart:
        """Очистить корзину."""
        logger.info(f"Clearing cart for user {user_id}")

        cart = self._cart_repo.get_by_user_id(user_id)
        if not cart:
            raise CartNotFoundError(f"Корзина для пользователя {user_id} не найдена")

        cart.clear()
        return self._cart_repo.save(cart)

    def get_cart_total(self, user_id: int) -> float:
        """Получить общую стоимость корзины."""
        cart = self._cart_repo.get_by_user_id(user_id)
        if not cart:
            return 0.0
        return float(cart.total_price)