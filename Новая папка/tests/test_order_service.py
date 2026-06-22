"""Тесты для OrderService."""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

from domain.models import Product, OrderStatus
from domain.exceptions import (
    CartEmptyError, CartNotFoundError, OrderNotFoundError,
    InsufficientStockError, BusinessRuleViolation
)
from services.order_service import OrderService
from repositories.in_memory import (
    InMemoryOrderRepository,
    InMemoryCartRepository,
    InMemoryProductRepository
)


class TestOrderService:
    """Тесты для OrderService."""

    @pytest.fixture
    def order_repo(self):
        return InMemoryOrderRepository()

    @pytest.fixture
    def cart_repo(self):
        return InMemoryCartRepository()

    @pytest.fixture
    def product_repo(self):
        return InMemoryProductRepository()

    @pytest.fixture
    def order_service(self, order_repo, cart_repo, product_repo):
        return OrderService(order_repo, cart_repo, product_repo)

    @pytest.fixture
    def cart_service(self, cart_repo, product_repo):
        from services.cart_service import CartService
        return CartService(cart_repo, product_repo)

    @pytest.fixture
    def setup_cart_with_items(self, cart_service, product_repo):
        """Создает корзину с товарами."""
        product1 = product_repo.save(Product(
            id=None, name="Product 1", description="", 
            price=Decimal('100.00'), stock=10, category="Test"
        ))
        product2 = product_repo.save(Product(
            id=None, name="Product 2", description="", 
            price=Decimal('50.00'), stock=10, category="Test"
        ))

        cart_service.add_to_cart(user_id=1, product_id=product1.id, quantity=2)
        cart_service.add_to_cart(user_id=1, product_id=product2.id, quantity=3)

        return product1, product2

    def test_create_order_success(self, order_service, setup_cart_with_items):
        """Тест успешного создания заказа из корзины."""
        order = order_service.create_order_from_cart(user_id=1)

        assert order.id is not None
        assert order.user_id == 1
        assert order.status == OrderStatus.PENDING
        assert order.total_price == Decimal('350.00')  # 2*100 + 3*50
        assert order.final_price == Decimal('350.00')
        assert len(order.items) == 2

    def test_create_order_with_discount(self, order_service, setup_cart_with_items):
        """Тест создания заказа со скидкой."""
        order = order_service.create_order_from_cart(
            user_id=1,
            discount_percentage=Decimal('20')
        )

        assert order.total_price == Decimal('350.00')
        assert order.discount_amount == Decimal('70.00')  # 20% от 350
        assert order.final_price == Decimal('280.00')

    def test_create_order_empty_cart(self, order_service):
        """Тест создания заказа из пустой корзины."""
        with pytest.raises(CartEmptyError, match="Невозможно создать заказ из пустой корзины"):
            order_service.create_order_from_cart(user_id=1)

    def test_create_order_cart_not_found(self, order_service):
        """Тест создания заказа из несуществующей корзины."""
        with pytest.raises(CartNotFoundError, match="Корзина для пользователя 999 не найдена"):
            order_service.create_order_from_cart(user_id=999)

    def test_create_order_stock_decreased(self, order_service, order_service, setup_cart_with_items, product_repo):
        """Тест проверки уменьшения количества товаров на складе."""
        product1, product2 = setup_cart_with_items
        
        # Проверяем начальное количество
        assert product_repo.get_by_id(product1.id).stock == 10
        assert product_repo.get_by_id(product2.id).stock == 10

        # Создаем заказ
        order_service.create_order_from_cart(user_id=1)

        # Проверяем, что количество уменьшилось
        assert product_repo.get_by_id(product1.id).stock == 8  # 10 - 2
        assert product_repo.get_by_id(product2.id).stock == 7  # 10 - 3

    def test_get_order_success(self, order_service, setup_cart_with_items):
        """Тест успешного получения заказа."""
        created = order_service.create_order_from_cart(user_id=1)
        retrieved = order_service.get_order(created.id)

        assert retrieved.id == created.id
        assert retrieved.user_id == created.user_id
        assert retrieved.total_price == created.total_price

    def test_get_order_not_found(self, order_service):
        """Тест получения несуществующего заказа."""
        with pytest.raises(OrderNotFoundError, match="Заказ с ID 999 не найден"):
            order_service.get_order(999)

    def test_get_user_orders(self, order_service, setup_cart_with_items):
        """Тест получения заказов пользователя."""
        order_service.create_order_from_cart(user_id=1)
        
        # Добавляем еще товары и создаем второй заказ
        # (в реальном тесте нужно было бы добавить еще товаров)
        orders = order_service.get_user_orders(user_id=1)
        assert len(orders) == 1

    def test_update_order_status_success(self, order_service, setup_cart_with_items):
        """Тест успешного обновления статуса заказа."""
        order = order_service.create_order_from_cart(user_id=1)

        updated = order_service.update_order_status(
            order.id,
            OrderStatus.PAID
        )

        assert updated.status == OrderStatus.PAID

    def test_update_order_status_cancelled_restores_stock(self, order_service, setup_cart_with_items, product_repo):
        """Тест отмены заказа с возвратом товаров на склад."""
        product1, product2 = setup_cart_with_items

        # Создаем заказ
        order = order_service.create_order_from_cart(user_id=1)

        # Проверяем, что количество уменьшилось
        assert product_repo.get_by_id(product1.id).stock == 8
        assert product_repo.get_by_id(product2.id).stock == 7

        # Отменяем заказ
        updated = order_service.update_order_status(order.id, OrderStatus.CANCELLED)

        assert updated.status == OrderStatus.CANCELLED

        # Проверяем, что количество вернулось
        assert product_repo.get_by_id(product1.id).stock == 10
        assert product_repo.get_by_id(product2.id).stock == 10

    def test_apply_discount_to_order(self, order_service, setup_cart_with_items):
        """Тест применения скидки к заказу."""
        order = order_service.create_order_from_cart(user_id=1)

        updated = order_service.apply_discount_to_order(
            order.id,
            Decimal('15')
        )

        assert updated.discount_amount == Decimal('52.50')  # 15% от 350
        assert updated.final_price == Decimal('297.50')

    def test_apply_discount_to_paid_order_fails(self, order_service, setup_cart_with_items):
        """Тест применения скидки к оплаченному заказу."""
        order = order_service.create_order_from_cart(user_id=1)
        order_service.update_order_status(order.id, OrderStatus.PAID)

        with pytest.raises(BusinessRuleViolation, match="Нельзя применить скидку к заказу в статусе"):
            order_service.apply_discount_to_order(order.id, Decimal('10'))

    def test_calculate_order_total(self, order_service, setup_cart_with_items):
        """Тест расчета общей суммы заказа."""
        order = order_service.create_order_from_cart(user_id=1)
        total = order_service.calculate_order_total(order.id)

        assert total == Decimal('350.00')