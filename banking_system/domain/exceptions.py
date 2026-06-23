"""Доменные исключения для банковской системы"""


class BankingError(Exception):
    """Базовое исключение для банковской системы"""
    pass


class AccountNotFoundError(BankingError):
    """Счёт не найден"""
    pass


class CustomerNotFoundError(BankingError):
    """Клиент не найден"""
    pass


class InsufficientFundsError(BankingError):
    """Недостаточно средств на счёте"""
    pass


class ValidationError(BankingError):
    """Ошибка валидации данных"""
    pass


class LimitExceededError(BankingError):
    """Превышен лимит операции"""
    pass


class FraudDetectedError(BankingError):
    """Обнаружена подозрительная транзакция"""
    pass


class AccountBlockedError(BankingError):
    """Счёт заблокирован"""
    pass


class TransferLimitError(BankingError):
    """Превышен лимит перевода"""
    pass