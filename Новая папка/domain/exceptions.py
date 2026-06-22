"""Доменные исключения для интернет-магазина."""


class DomainError(Exception):
    """Базовое исключение для доменных ошибок."""
    pass


class NotFoundError(DomainError):
    """Объект не найден."""
    pass


class ValidationError(DomainError):
    """Ошибка валидации данных."""
    pass


class BusinessRuleViolation(DomainError):
    """Нарушение бизнес-правила."""
    pass


class ProductNotFoundError(NotFoundError):
    """Товар не найден."""
    pass


class CartNotFoundError(NotFoundError):
    """Корзина не найдена."""
    pass


class OrderNotFoundError(NotFoundError):
    """Заказ не найден."""
    pass


class InsufficientStockError(BusinessRuleViolation):
    """Недостаточно товара на складе."""
    pass


class InvalidQuantityError(ValidationError):
    """Некорректное количество товара."""
    pass


class CartEmptyError(BusinessRuleViolation):
    """Корзина пуста."""
    pass


class DiscountNotApplicableError(BusinessRuleViolation):
    """Скидка не применима."""
    pass