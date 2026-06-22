"""Сервис для работы с товарами."""

import logging
from typing import List, Optional
from decimal import Decimal

from domain.models import Product
from domain.exceptions import ProductNotFoundError, ValidationError
from repositories.interfaces import ProductRepository
from schemas.dto import ProductCreateDTO, ProductUpdateDTO

logger = logging.getLogger(__name__)


class ProductService:
    """Сервис для управления товарами."""

    def __init__(self, product_repository: ProductRepository):
        self._product_repo = product_repository

    def create_product(self, data: ProductCreateDTO) -> Product:
        """Создать новый товар."""
        logger.info(f"Creating product: {data.name}")

        # Валидация
        if data.price <= 0:
            raise ValidationError("Цена товара должна быть положительной")
        if data.stock < 0:
            raise ValidationError("Количество товара не может быть отрицательным")
        if not data.name.strip():
            raise ValidationError("Название товара не может быть пустым")

        product = Product(
            id=None,
            name=data.name.strip(),
            description=data.description or "",
            price=data.price,
            stock=data.stock,
            category=data.category
        )

        saved = self._product_repo.save(product)
        logger.info(f"Product created with id: {saved.id}")
        return saved

    def get_product(self, product_id: int) -> Product:
        """Получить товар по ID."""
        product = self._product_repo.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError(f"Товар с ID {product_id} не найден")
        return product

    def search_products(self, query: str) -> List[Product]:
        """Поиск товаров."""
        logger.debug(f"Searching products with query: {query}")
        return self._product_repo.search(query)

    def get_products_by_category(self, category: str) -> List[Product]:
        """Получить товары по категории."""
        return self._product_repo.get_by_category(category)

    def get_available_products(self) -> List[Product]:
        """Получить все доступные товары."""
        return self._product_repo.get_available()

    def update_product(self, product_id: int, data: ProductUpdateDTO) -> Product:
        """Обновить товар."""
        logger.info(f"Updating product: {product_id}")

        product = self.get_product(product_id)

        if data.name is not None:
            if not data.name.strip():
                raise ValidationError("Название товара не может быть пустым")
            product.name = data.name.strip()

        if data.description is not None:
            product.description = data.description

        if data.price is not None:
            if data.price <= 0:
                raise ValidationError("Цена товара должна быть положительной")
            product.price = data.price

        if data.stock is not None:
            if data.stock < 0:
                raise ValidationError("Количество товара не может быть отрицательным")
            product.stock = data.stock

        if data.category is not None:
            product.category = data.category

        return self._product_repo.save(product)

    def update_stock(self, product_id: int, new_stock: int) -> Product:
        """Обновить количество товара."""
        logger.info(f"Updating stock for product: {product_id} to {new_stock}")

        if new_stock < 0:
            raise ValidationError("Количество товара не может быть отрицательным")

        try:
            return self._product_repo.update_stock(product_id, new_stock)
        except ValueError as e:
            raise ProductNotFoundError(str(e))