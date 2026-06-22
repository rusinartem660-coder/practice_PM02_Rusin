"""In-Memory реализации репозиториев."""

from typing import List, Optional, Dict
from decimal import Decimal
from datetime import datetime

from domain.models import Product, Cart, CartItem, Order, OrderStatus, OrderItem
from repositories.interfaces import ProductRepository, CartRepository, OrderRepository


class InMemoryProductRepository(ProductRepository):
    """In-Memory репозиторий товаров."""

    def __init__(self):
        self._products: Dict[int, Product] = {}
        self._next_id = 1

    def get_by_id(self, product_id: int) -> Optional[Product]:
        return self._products.get(product_id)

    def get_by_category(self, category: str) -> List[Product]:
        return [p for p in self._products.values() if p.category.lower() == category.lower()]

    def search(self, query: str) -> List[Product]:
        query_lower = query.lower()
        return [
            p for p in self._products.values()
            if query_lower in p.name.lower() or query_lower in p.description.lower()
        ]

    def get_available(self) -> List[Product]:
        return [p for p in self._products.values() if p.stock > 0]

    def save(self, product: Product) -> Product:
        if product.id is None:
            product.id = self._next_id
            self._next_id += 1
        self._products[product.id] = product
        return product

    def update_stock(self, product_id: int, new_stock: int) -> Product:
        product = self.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product with id {product_id} not found")
        if new_stock < 0:
            raise ValueError("Stock cannot be negative")
        product.stock = new_stock
        product.updated_at = datetime.now()
        return product


class InMemoryCartRepository(CartRepository):
    """In-Memory репозиторий корзин."""

    def __init__(self):
        self._carts: Dict[int, Cart] = {}
        self._next_id = 1

    def get_by_user_id(self, user_id: int) -> Optional[Cart]:
        for cart in self._carts.values():
            if cart.user_id == user_id:
                return cart
        return None

    def save(self, cart: Cart) -> Cart:
        if cart.id is None:
            cart.id = self._next_id
            self._next_id += 1
        cart.updated_at = datetime.now()
        self._carts[cart.id] = cart
        return cart

    def delete(self, cart_id: int) -> bool:
        if cart_id in self._carts:
            del self._carts[cart_id]
            return True
        return False


class InMemoryOrderRepository(OrderRepository):
    """In-Memory репозиторий заказов."""

    def __init__(self):
        self._orders: Dict[int, Order] = {}
        self._next_id = 1

    def get_by_id(self, order_id: int) -> Optional[Order]:
        return self._orders.get(order_id)

    def get_by_user_id(self, user_id: int) -> List[Order]:
        return [o for o in self._orders.values() if o.user_id == user_id]

    def get_by_status(self, status: OrderStatus) -> List[Order]:
        return [o for o in self._orders.values() if o.status == status]

    def save(self, order: Order) -> Order:
        if order.id is None:
            order.id = self._next_id
            self._next_id += 1
        order.updated_at = datetime.now()
        self._orders[order.id] = order
        return order

    def update_status(self, order_id: int, new_status: OrderStatus) -> Order:
        order = self.get_by_id(order_id)
        if not order:
            raise ValueError(f"Order with id {order_id} not found")
        order.status = new_status
        order.updated_at = datetime.now()
        return order