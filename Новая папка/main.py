"""Пример использования сервисов интернет-магазина."""

import sys
import os
from pathlib import Path

# Добавляем текущую папку в путь поиска модулей
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

import logging
from decimal import Decimal

# Теперь импорты должны работать
from domain.models import OrderStatus
from repositories.in_memory import (
    InMemoryProductRepository,
    InMemoryCartRepository,
    InMemoryOrderRepository
)
from services.product_service import ProductService
from services.cart_service import CartService
from services.order_service import OrderService
from schemas.dto import ProductCreateDTO

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    """Основная функция демонстрации работы."""
    
    # Создаем репозитории
    product_repo = InMemoryProductRepository()
    cart_repo = InMemoryCartRepository()
    order_repo = InMemoryOrderRepository()
    
    # Создаем сервисы с внедрением зависимостей
    product_service = ProductService(product_repo)
    cart_service = CartService(cart_repo, product_repo)
    order_service = OrderService(order_repo, cart_repo, product_repo)
    
    print("=" * 50)
    print("ИНТЕРНЕТ-МАГАЗИН")
    print("=" * 50)
    
    # 1. Создаем товары
    print("\n1. Добавление товаров:")
    print("-" * 30)
    
    product1 = product_service.create_product(ProductCreateDTO(
        name="Ноутбук HP",
        description="Мощный ноутбук для работы и игр",
        price=Decimal('79999.99'),
        stock=5,
        category="Электроника"
    ))
    print(f"✓ Добавлен товар: {product1.name} (ID: {product1.id})")
    
    product2 = product_service.create_product(ProductCreateDTO(
        name="Мышь Logitech",
        description="Беспроводная мышь",
        price=Decimal('2999.99'),
        stock=10,
        category="Электроника"
    ))
    print(f"✓ Добавлен товар: {product2.name} (ID: {product2.id})")
    
    product3 = product_service.create_product(ProductCreateDTO(
        name="Книга Python для начинающих",
        description="Учебник по Python",
        price=Decimal('1500.00'),
        stock=20,
        category="Книги"
    ))
    print(f"✓ Добавлен товар: {product3.name} (ID: {product3.id})")
    
    # 2. Просмотр товаров по категории
    print("\n2. Просмотр товаров в категории 'Электроника':")
    print("-" * 30)
    electronics = product_service.get_products_by_category("Электроника")
    for p in electronics:
        print(f"  - {p.name}: {p.price} руб. (в наличии: {p.stock})")
    
    # 3. Добавляем товары в корзину
    print("\n3. Добавление товаров в корзину:")
    print("-" * 30)
    
    cart_service.add_to_cart(user_id=1, product_id=product1.id, quantity=1)
    print(f"✓ Добавлен {product1.name} (1 шт.)")
    
    cart_service.add_to_cart(user_id=1, product_id=product2.id, quantity=2)
    print(f"✓ Добавлен {product2.name} (2 шт.)")
    
    cart_service.add_to_cart(user_id=1, product_id=product3.id, quantity=1)
    print(f"✓ Добавлен {product3.name} (1 шт.)")
    
    # 4. Просмотр корзины
    print("\n4. Содержимое корзины:")
    print("-" * 30)
    cart = cart_service.get_or_create_cart(user_id=1)
    for item in cart.items:
        print(f"  - {item.product_name}: {item.quantity} шт. x {item.unit_price} руб. = {item.total_price} руб.")
    print(f"  ИТОГО: {cart.total_price} руб.")
    
    # 5. Оформляем заказ
    print("\n5. Оформление заказа:")
    print("-" * 30)
    
    order = order_service.create_order_from_cart(
        user_id=1,
        discount_percentage=Decimal('10')
    )
    print(f"✓ Заказ создан (ID: {order.id})")
    print(f"  Сумма: {order.total_price} руб.")
    print(f"  Скидка: {order.discount_amount} руб.")
    print(f"  Итого: {order.final_price} руб.")
    print(f"  Статус: {order.status.value}")
    
    # 6. Просмотр всех заказов пользователя
    print("\n6. История заказов пользователя:")
    print("-" * 30)
    orders = order_service.get_user_orders(user_id=1)
    for o in orders:
        print(f"  Заказ #{o.id}: {o.final_price} руб., статус: {o.status.value}")
    
    # 7. Обновление статуса заказа
    print("\n7. Обновление статуса заказа:")
    print("-" * 30)
    
    order_service.update_order_status(order.id, OrderStatus.PAID)
    print(f"✓ Заказ #{order.id} оплачен")
    
    order_service.update_order_status(order.id, OrderStatus.SHIPPED)
    print(f"✓ Заказ #{order.id} отправлен")
    
    order_service.update_order_status(order.id, OrderStatus.DELIVERED)
    print(f"✓ Заказ #{order.id} доставлен")
    
    # 8. Поиск товаров
    print("\n8. Поиск товаров по запросу 'Python':")
    print("-" * 30)
    results = product_service.search_products("Python")
    for p in results:
        print(f"  - {p.name}: {p.price} руб.")
    
    print("\n" + "=" * 50)
    print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 50)


if __name__ == "__main__":
    main()