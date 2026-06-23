"""Модульные тесты для BankingService"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta

from domain.exceptions import (
    AccountNotFoundError, CustomerNotFoundError, InsufficientFundsError,
    ValidationError, LimitExceededError, FraudDetectedError,
    AccountBlockedError, TransferLimitError
)
from domain.models import AccountStatus, AccountType, TransactionStatus
from services.banking_service import BankingService


class TestBankingService:
    """Тесты банковского сервиса"""

    def test_register_customer_success(self, banking_service):
        """Успешная регистрация клиента"""
        customer = banking_service.register_customer(
            full_name="Петр Петров",
            email="petr@test.ru",
            phone="+79211234567",
            passport_number="5678 123456"
        )
        
        assert customer.id is not None
        assert customer.full_name == "Петр Петров"
        assert customer.email == "petr@test.ru"
        assert customer.is_active is True

    def test_register_customer_invalid_email(self, banking_service):
        """Регистрация с некорректным email"""
        with pytest.raises(ValidationError, match="Некорректный формат email"):
            banking_service.register_customer(
                full_name="Тест Тестов",
                email="invalid-email",
                phone="+79211234567",
                passport_number="5678 123456"
            )

    def test_register_customer_duplicate_email(self, banking_service):
        """Регистрация с уже существующим email"""
        banking_service.register_customer(
            full_name="Иван Иванов",
            email="duplicate@test.ru",
            phone="+79111234567",
            passport_number="1111 111111"
        )
        
        with pytest.raises(ValidationError, match="уже зарегистрирован"):
            banking_service.register_customer(
                full_name="Петр Петров",
                email="duplicate@test.ru",
                phone="+79211234567",
                passport_number="2222 222222"
            )

    def test_create_account_success(self, banking_service, sample_customer):
        """Успешное открытие счёта"""
        # Сохраняем клиента
        banking_service.customer_repo.save(sample_customer)
        
        account = banking_service.create_account(
            customer_id=sample_customer.id,
            account_type="checking",
            currency="RUB"
        )
        
        assert account.id is not None
        assert account.customer_id == sample_customer.id
        assert account.account_type == AccountType.CHECKING
        assert account.balance == Decimal('0.00')
        assert account.status == AccountStatus.ACTIVE

    def test_create_account_customer_not_found(self, banking_service):
        """Открытие счёта для несуществующего клиента"""
        with pytest.raises(CustomerNotFoundError, match="не найден"):
            banking_service.create_account(
                customer_id="non_existent",
                account_type="checking"
            )

    def test_get_account_success(self, banking_service, sample_customer, sample_account):
        """Получение счёта по ID"""
        banking_service.customer_repo.save(sample_customer)
        banking_service.account_repo.save(sample_account)
        
        account = banking_service.get_account(sample_account.id)
        assert account.id == sample_account.id
        assert account.balance == Decimal('10000.00')

    def test_get_account_not_found(self, banking_service):
        """Получение несуществующего счёта"""
        with pytest.raises(AccountNotFoundError, match="не найден"):
            banking_service.get_account("non_existent")

    def test_deposit_success(self, banking_service, sample_customer, sample_account):
        """Успешное пополнение счёта"""
        banking_service.customer_repo.save(sample_customer)
        banking_service.account_repo.save(sample_account)
        
        transaction = banking_service.deposit(
            account_id=sample_account.id,
            amount=Decimal('500.00'),
            description="Пополнение наличными"
        )
        
        assert transaction.status == TransactionStatus.COMPLETED
        assert transaction.amount == Decimal('500.00')
        
        # Проверка обновлённого баланса
        account = banking_service.get_account(sample_account.id)
        assert account.balance == Decimal('10500.00')

    def test_deposit_negative_amount(self, banking_service, sample_customer, sample_account):
        """Пополнение на отрицательную сумму"""
        banking_service.customer_repo.save(sample_customer)
        banking_service.account_repo.save(sample_account)
        
        with pytest.raises(ValidationError, match="положительной"):
            banking_service.deposit(
                account_id=sample_account.id,
                amount=Decimal('-100.00')
            )

    def test_deposit_blocked_account(self, banking_service, sample_customer, sample_account):
        """Пополнение заблокированного счёта"""
        banking_service.customer_repo.save(sample_customer)
        sample_account.status = AccountStatus.BLOCKED
        banking_service.account_repo.save(sample_account)
        
        with pytest.raises(AccountBlockedError, match="неактивен"):
            banking_service.deposit(
                account_id=sample_account.id,
                amount=Decimal('100.00')
            )

    def test_withdraw_success(self, banking_service, sample_customer, sample_account):
        """Успешное снятие средств"""
        banking_service.customer_repo.save(sample_customer)
        banking_service.account_repo.save(sample_account)
        
        transaction = banking_service.withdraw(
            account_id=sample_account.id,
            amount=Decimal('1000.00'),
            description="Снятие в банкомате"
        )
        
        assert transaction.status == TransactionStatus.COMPLETED
        assert transaction.amount == Decimal('1000.00')
        
        # Проверка обновлённого баланса
        account = banking_service.get_account(sample_account.id)
        assert account.balance == Decimal('9000.00')

    def test_withdraw_insufficient_funds(self, banking_service, sample_customer, sample_account):
        """Снятие при недостатке средств"""
        banking_service.customer_repo.save(sample_customer)
        banking_service.account_repo.save(sample_account)
        
        with pytest.raises(InsufficientFundsError, match="Недостаточно средств"):
            banking_service.withdraw(
                account_id=sample_account.id,
                amount=Decimal('20000.00')
            )

    def test_withdraw_exceeds_daily_limit(self, banking_service, sample_customer, sample_account):
        """Снятие с превышением дневного лимита"""
        banking_service.customer_repo.save(sample_customer)
        sample_account.daily_limit = Decimal('5000.00')
        banking_service.account_repo.save(sample_account)
        
        with pytest.raises(LimitExceededError, match="превышает дневной лимит"):
            banking_service.withdraw(
                account_id=sample_account.id,
                amount=Decimal('10000.00')
            )

    def test_transfer_success(self, banking_service, sample_customer, sample_account, sample_account2):
        """Успешный перевод между счетами"""
        banking_service.customer_repo.save(sample_customer)
        banking_service.account_repo.save(sample_account)
        banking_service.account_repo.save(sample_account2)
        
        transaction = banking_service.transfer(
            from_account_id=sample_account.id,
            to_account_id=sample_account2.id,
            amount=Decimal('1000.00'),
            description="Перевод другу"
        )
        
        assert transaction.status == TransactionStatus.COMPLETED
        assert transaction.amount == Decimal('1000.00')
        
        # Проверка балансов
        from_account = banking_service.get_account(sample_account.id)
        to_account = banking_service.get_account(sample_account2.id)
        
        # Учитываем комиссию 1%
        assert from_account.balance == Decimal('8990.00')  # 10000 - 1000 - 10
        assert to_account.balance == Decimal('51000.00')   # 50000 + 1000

    def test_transfer_same_account(self, banking_service, sample_customer, sample_account):
        """Перевод на тот же счёт"""
        banking_service.customer_repo.save(sample_customer)
        banking_service.account_repo.save(sample_account)
        
        with pytest.raises(ValidationError, match="Нельзя переводить на тот же счёт"):
            banking_service.transfer(
                from_account_id=sample_account.id,
                to_account_id=sample_account.id,
                amount=Decimal('100.00')
            )

    def test_transfer_insufficient_funds(self, banking_service, sample_customer, sample_account, sample_account2):
        """Перевод при недостатке средств с учётом комиссии"""
        banking_service.customer_repo.save(sample_customer)
        banking_service.account_repo.save(sample_account)
        banking_service.account_repo.save(sample_account2)
        
        with pytest.raises(InsufficientFundsError, match="Недостаточно средств"):
            banking_service.transfer(
                from_account_id=sample_account.id,
                to_account_id=sample_account2.id,
                amount=Decimal('9500.00')  # 9500 + комиссия 95 = 9595 > 10000
            )

    def test_transfer_fraud_detected(self, banking_service, sample_customer, sample_account, sample_account2):
        """Перевод, заблокированный антифрод-системой"""
        banking_service.customer_repo.save(sample_customer)
        banking_service.account_repo.save(sample_account)
        banking_service.account_repo.save(sample_account2)
        
        # Подменяем сервис антифрод для генерации ошибки
        fraud_mock = Mock()
        fraud_mock.check_transfer.return_value = (False, "Подозрительная операция")
        banking_service.fraud_service = fraud_mock
        
        with pytest.raises(FraudDetectedError, match="Операция отклонена"):
            banking_service.transfer(
                from_account_id=sample_account.id,
                to_account_id=sample_account2.id,
                amount=Decimal('100.00')
            )

    def test_transfer_blocked_from_account(self, banking_service, sample_customer, sample_account, sample_account2):
        """Перевод с заблокированного счёта"""
        banking_service.customer_repo.save(sample_customer)
        sample_account.status = AccountStatus.BLOCKED
        banking_service.account_repo.save(sample_account)
        banking_service.account_repo.save(sample_account2)
        
        with pytest.raises(AccountBlockedError, match="неактивен"):
            banking_service.transfer(
                from_account_id=sample_account.id,
                to_account_id=sample_account2.id,
                amount=Decimal('100.00')
            )

    def test_get_customer_accounts(self, banking_service, sample_customer, sample_account, sample_account2):
        """Получение всех счетов клиента"""
        banking_service.customer_repo.save(sample_customer)
        banking_service.account_repo.save(sample_account)
        banking_service.account_repo.save(sample_account2)
        
        accounts = banking_service.get_customer_accounts(sample_customer.id)
        assert len(accounts) == 2
        
        account_ids = [acc.id for acc in accounts]
        assert sample_account.id in account_ids
        assert sample_account2.id in account_ids

    def test_get_account_balance(self, banking_service, sample_customer, sample_account):
        """Получение баланса счёта"""
        banking_service.customer_repo.save(sample_customer)
        banking_service.account_repo.save(sample_account)
        
        balance = banking_service.get_account_balance(sample_account.id)
        assert balance == Decimal('10000.00')

    def test_block_account(self, banking_service, sample_customer, sample_account):
        """Блокировка счёта"""
        banking_service.customer_repo.save(sample_customer)
        banking_service.account_repo.save(sample_account)
        
        blocked = banking_service.block_account(
            account_id=sample_account.id,
            reason="Подозрительная активность"
        )
        
        assert blocked.status == AccountStatus.BLOCKED

    def test_freeze_account(self, banking_service, sample_customer, sample_account):
        """Заморозка счёта"""
        banking_service.customer_repo.save(sample_customer)
        banking_service.account_repo.save(sample_account)
        
        frozen = banking_service.freeze_account(sample_account.id)
        assert frozen.status == AccountStatus.FROZEN

    def test_register_customer_invalid_phone(self, banking_service):
        """Регистрация с некорректным телефоном"""
        with pytest.raises(ValidationError, match="Некорректный формат телефона"):
            banking_service.register_customer(
                full_name="Тест Тестов",
                email="test@test.ru",
                phone="123",  # Слишком короткий
                passport_number="5678 123456"
            )

    def test_transfer_with_mocks(self, mocker, banking_service, sample_customer, sample_account, sample_account2):
        """Перевод с использованием моков"""
        # Сохраняем тестовые данные
        banking_service.customer_repo.save(sample_customer)
        banking_service.account_repo.save(sample_account)
        banking_service.account_repo.save(sample_account2)
        
        # Мокаем сервис антифрод
        mock_fraud = mocker.Mock()
        mock_fraud.check_transfer.return_value = (True, "OK")
        banking_service.fraud_service = mock_fraud
        
        transaction = banking_service.transfer(
            from_account_id=sample_account.id,
            to_account_id=sample_account2.id,
            amount=Decimal('500.00')
        )
        
        assert transaction.status == TransactionStatus.COMPLETED
        mock_fraud.check_transfer.assert_called_once()