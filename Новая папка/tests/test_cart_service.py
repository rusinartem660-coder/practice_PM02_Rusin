"""Тесты для CartService."""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

from domain.models import Product, Cart, CartItem
from domain.exceptions import (
    CartNotFoundError, ProductNotFoundError,
    InvalidQuantityError, InsufficientStockError
)
from services.cart_service import CartService
from repositories.in_memory import InMemoryCartRepository, InMemoryProductRepository


class TestCartService:
    """Тесты для CartService."""

    @pytest.fixture
    def cart_repo(self):
        return InMemoryCartRepository()

    @pytest.fixture
    def product_repo(self):
        return InMemoryProductRepository()

    @pytest.fixture
    def cart_service(self, cart_repo, product_repo):
        return CartService(cart_repo, product_repo)

    @pytest.fixture
    def sample_product(self, product_repo):
        product = Product(
            id=None,
            name="Test Product",
            description="Test Description",
            price=Decimal('99.99'),
            stock=10,
            category="Test"
        )
        return product_repo.save(product)

    def test_get_or_create_cart_new_user(self, cart_service):
        """Тест создания новой корзины для пользователя."""
        cart = cart_service.get_or_create_cart(user_id=1)
        assert cart.id is not None
        assert cart.user_id == 1
        assert len(cart.items) == 0

    def test_get_or_create_cart_existing(self, cart_service):
        """Тест получения существующей корзины."""
        cart1 = cart_service.get_or_create_cart(user_id=1)
        cart2 = cart_service.get_or_create_cart(user_id=1)
        assert cart1.id == cart2.id

    def test_add_to_cart_success(self, cart_service, sample_product):
        """Тест успешного добавления товара в корзину."""
        cart = cart_service.add_to_cart(
            user_id=1,
            product_id=sample_product.id,
            quantity=2
        )

        assert len(cart.items) == 1
        assert cart.items[0].product_id == sample_product.id
        assert cart.items[0].quantity == 2
        assert cart.items[0].unit_price == Decimal('99.99')
        assert cart.total_price == Decimal('199.98')

    def test_add_to_cart_product_not_found(self, cart_service):
        """Тест добавления несуществующего товара."""
        with pytest.raises(ProductNotFoundError, match="Товар с ID 999 не найден"):
            cart_service.add_to_cart(user_id=1, product_id=999, quantity=1)

    def test_add_to_cart_invalid_quantity(self, cart_service, sample_product):
        """Тест добавления с некорректным количеством."""
        with pytest.raises(InvalidQuantityError, match="Количество должно быть положительным"):
            cart_service.add_to_cart(user_id=1, product_id=sample_product.id, quantity=0)

        with pytest.raises(InvalidQuantityError, match="Количество должно быть положительным"):
            cart_service.add_to_cart(user_id=1, product_id=sample_product.id, quantity=-5)

    def test_add_to_cart_insufficient_stock(self, cart_service, sample_product):
        """Тест добавления товара при недостаточном количестве на складе."""
        with pytest.raises(InsufficientStockError, match="Недостаточно товара"):
            cart_service.add_to_cart(
                user_id=1,
                product_id=sample_product.id,
                quantity=20  # больше чем stock=10
            )

    def test_remove_from_cart_success(self, cart_service, sample_product):
        """Тест успешного удаления товара из корзины."""
        # Сначала добавляем товар
        cart_service.add_to_cart(user_id=1, product_id=sample_product.id, quantity=2)

        # Удаляем товар
        cart = cart_service.remove_from_cart(user_id=1, product_id=sample_product.id)

        assert len(cart.items) == 0

    def test_remove_from_cart_not_found(self, cart_service):
        """Тест удаления из несуществующей корзины."""
        with pytest.raises(CartNotFoundError, match="Корзина для пользователя 999 не найдена"):
            cart_service.remove_from_cart(user_id=999, product_id=1)

    def test_update_cart_quantity_success(self, cart_service, sample_product):
        """Тест успешного обновления количества товара в корзине."""
        # Добавляем товар
        cart_service.add_to_cart(user_id=1, product_id=sample_product.id, quantity=2)

        # Обновляем количество
        cart = cart_service.update_cart_quantity(
            user_id=1,
            product_id=sample_product.id,
            quantity=5
        )

        assert cart.items[0].quantity == 5
        assert cart.total_price == Decimal('499.95')

    def test_update_cart_quantity_to_zero(self, cart_service, sample_product):
        """Тест обновления количества до 0 (удаление)."""
        # Добавляем товар
        cart_service.add_to_cart(user_id=1, product_id=sample_product.id, quantity=2)

        # Обновляем количество до 0
        cart = cart_service.update_cart_quantity(
            user_id=1,
            product_id=sample_product.id,
            quantity=0
        )

        assert len(cart.items) == 0

    def test_clear_cart_success(self, cart_service, sample_product):
        """Тест очистки корзины."""
        # Добавляем несколько товаров
        cart_service.add_to_cart(user_id=1, product_id=sample_product.id, quantity=2)

        # Очищаем корзину
        cart = cart_service.clear_cart(user_id=1)

        assert len(cart.items) == 0

    def test_clear_cart_not_found(self, cart_service):
        """Тест очистки несуществующей корзины."""
        with pytest.raises(CartNotFoundError, match="Корзина для пользователя 999 не найдена"):
            cart_service.clear_cart(user_id=999)

    def test_get_cart_total(self, cart_service, sample_product):
        """Тест получения общей стоимости корзины."""
        # Добавляем товары
        cart_service.add_to_cart(user_id=1, product_id=sample_product.id, quantity=2)

        total = cart_service.get_cart_total(user_id=1)
        assert total == 199.98

    def test_get_cart_total_empty(self, cart_service):
        """Тест получения стоимости пустой корзины."""
        total = cart_service.get_cart_total(user_id=1)
        assert total == 0.0

    def test_add_to_cart_multiple_items(self, cart_service, product_repo):
        """Тест добавления нескольких разных товаров."""
        # Создаем несколько товаров
        product1 = product_repo.save(Product(
            id=None, name="Product 1", description="", 
            price=Decimal('10.00'), stock=10, category="Test"
        ))
        product2 = product_repo.save(Product(
            id=None, name="Product 2", description="", 
            price=Decimal('20.00'), stock=10, category="Test"
        ))

        # Добавляем оба товара
        cart_service.add_to_cart(user_id=1, product_id=product1.id, quantity=2)
        cart = cart_service.add_to_cart(user_id=1, product_id=product2.id, quantity=3)

        assert len(cart.items) == 2
        assert cart.total_price == Decimal('80.00')  # 2*10 + 3*20