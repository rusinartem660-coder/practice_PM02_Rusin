"""Интерфейсы репозиториев."""

from abc import ABC, abstractmethod
from typing import List, Optional
from decimal import Decimal

from domain.models import Product, Cart, Order, OrderStatus


class ProductRepository(ABC):
    """Репозиторий для работы с товарами."""

    @abstractmethod
    def get_by_id(self, product_id: int) -> Optional[Product]:
        """Получить товар по ID."""
        pass

    @abstractmethod
    def get_by_category(self, category: str) -> List[Product]:
        """Получить товары по категории."""
        pass

    @abstractmethod
    def search(self, query: str) -> List[Product]:
        """Поиск товаров по названию или описанию."""
        pass

    @abstractmethod
    def get_available(self) -> List[Product]:
        """Получить все доступные товары (stock > 0)."""
        pass

    @abstractmethod
    def save(self, product: Product) -> Product:
        """Сохранить товар."""
        pass

    @abstractmethod
    def update_stock(self, product_id: int, new_stock: int) -> Product:
        """Обновить количество товара."""
        pass


class CartRepository(ABC):
    """Репозиторий для работы с корзинами."""

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> Optional[Cart]:
        """Получить корзину по ID пользователя."""
        pass

    @abstractmethod
    def save(self, cart: Cart) -> Cart:
        """Сохранить корзину."""
        pass

    @abstractmethod
    def delete(self, cart_id: int) -> bool:
        """Удалить корзину."""
        pass


class OrderRepository(ABC):
    """Репозиторий для работы с заказами."""

    @abstractmethod
    def get_by_id(self, order_id: int) -> Optional[Order]:
        """Получить заказ по ID."""
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> List[Order]:
        """Получить все заказы пользователя."""
        pass

    @abstractmethod
    def get_by_status(self, status: OrderStatus) -> List[Order]:
        """Получить заказы по статусу."""
        pass

    @abstractmethod
    def save(self, order: Order) -> Order:
        """Сохранить заказ."""
        pass

    @abstractmethod
    def update_status(self, order_id: int, new_status: OrderStatus) -> Order:
        """Обновить статус заказа."""
        pass