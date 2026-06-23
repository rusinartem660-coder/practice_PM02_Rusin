"""Конфигурация тестов и глобальные фикстуры"""

import pytest
from decimal import Decimal
from datetime import datetime

from domain.models import Customer, BankAccount, AccountType, AccountStatus
from repositories.in_memory import (
    InMemoryCustomerRepository,
    InMemoryAccountRepository,
    InMemoryTransactionRepository
)
from services.banking_service import BankingService, FraudDetectionService


@pytest.fixture
def customer_repo():
    """Фикстура репозитория клиентов"""
    return InMemoryCustomerRepository()


@pytest.fixture
def account_repo():
    """Фикстура репозитория счетов"""
    return InMemoryAccountRepository()


@pytest.fixture
def transaction_repo():
    """Фикстура репозитория транзакций"""
    return InMemoryTransactionRepository()


@pytest.fixture
def fraud_service():
    """Фикстура сервиса антифрод"""
    return FraudDetectionService()


@pytest.fixture
def banking_service(customer_repo, account_repo, transaction_repo, fraud_service):
    """Фикстура основного банковского сервиса"""
    return BankingService(customer_repo, account_repo, transaction_repo, fraud_service)


@pytest.fixture
def sample_customer():
    """Фикстура тестового клиента"""
    return Customer(
        id="cust_test_1",
        full_name="Иван Иванов",
        email="ivan@test.ru",
        phone="+79111234567",
        passport_number="1234 567890"
    )


@pytest.fixture
def sample_account(sample_customer):
    """Фикстура тестового счёта"""
    return BankAccount(
        id="acc_test_1",
        customer_id=sample_customer.id,
        account_number="40817810000000000001",
        account_type=AccountType.CHECKING,
        balance=Decimal('10000.00'),
        currency="RUB",
        status=AccountStatus.ACTIVE
    )


@pytest.fixture
def sample_account2(sample_customer):
    """Фикстура второго тестового счёта"""
    return BankAccount(
        id="acc_test_2",
        customer_id=sample_customer.id,
        account_number="40817810000000000002",
        account_type=AccountType.SAVINGS,
        balance=Decimal('50000.00'),
        currency="RUB",
        status=AccountStatus.ACTIVE
    )