"""Тесты для ProductService."""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch

from domain.models import Product
from domain.exceptions import ProductNotFoundError, ValidationError
from services.product_service import ProductService
from repositories.in_memory import InMemoryProductRepository
from schemas.dto import ProductCreateDTO, ProductUpdateDTO


class TestProductService:
    """Тесты для ProductService."""

    @pytest.fixture
    def product_repo(self):
        return InMemoryProductRepository()

    @pytest.fixture
    def product_service(self, product_repo):
        return ProductService(product_repo)

    @pytest.fixture
    def sample_product(self, product_service):
        data = ProductCreateDTO(
            name="Test Product",
            description="Test Description",
            price=Decimal('99.99'),
            stock=10,
            category="Test"
        )
        return product_service.create_product(data)

    def test_create_product_success(self, product_service):
        """Тест успешного создания товара."""
        data = ProductCreateDTO(
            name="New Product",
            description="Description",
            price=Decimal('49.99'),
            stock=5,
            category="Electronics"
        )

        product = product_service.create_product(data)

        assert product.id is not None
        assert product.name == "New Product"
        assert product.price == Decimal('49.99')
        assert product.stock == 5

    def test_create_product_invalid_price(self, product_service):
        """Тест создания товара с некорректной ценой."""
        data = ProductCreateDTO(
            name="Invalid Product",
            price=Decimal('-10.00'),
            stock=5,
            category="Test"
        )

        with pytest.raises(ValidationError, match="Цена товара должна быть положительной"):
            product_service.create_product(data)

    def test_create_product_invalid_stock(self, product_service):
        """Тест создания товара с отрицательным количеством."""
        data = ProductCreateDTO(
            name="Invalid Product",
            price=Decimal('10.00'),
            stock=-5,
            category="Test"
        )

        with pytest.raises(ValidationError, match="Количество товара не может быть отрицательным"):
            product_service.create_product(data)

    def test_get_product_success(self, product_service, sample_product):
        """Тест успешного получения товара."""
        product = product_service.get_product(sample_product.id)
        assert product.id == sample_product.id
        assert product.name == sample_product.name

    def test_get_product_not_found(self, product_service):
        """Тест получения несуществующего товара."""
        with pytest.raises(ProductNotFoundError, match="Товар с ID 999 не найден"):
            product_service.get_product(999)

    def test_search_products(self, product_service, sample_product):
        """Тест поиска товаров."""
        results = product_service.search_products("Test")
        assert len(results) > 0
        assert any(p.name == "Test Product" for p in results)

    def test_update_product_success(self, product_service, sample_product):
        """Тест успешного обновления товара."""
        data = ProductUpdateDTO(
            name="Updated Product",
            price=Decimal('149.99'),
            stock=20
        )

        updated = product_service.update_product(sample_product.id, data)

        assert updated.name == "Updated Product"
        assert updated.price == Decimal('149.99')
        assert updated.stock == 20

    def test_update_product_not_found(self, product_service):
        """Тест обновления несуществующего товара."""
        data = ProductUpdateDTO(name="New Name")

        with pytest.raises(ProductNotFoundError):
            product_service.update_product(999, data)

    def test_update_stock_success(self, product_service, sample_product):
        """Тест успешного обновления количества товара."""
        updated = product_service.update_stock(sample_product.id, 50)
        assert updated.stock == 50

    def test_update_stock_negative(self, product_service, sample_product):
        """Тест обновления количества с отрицательным значением."""
        with pytest.