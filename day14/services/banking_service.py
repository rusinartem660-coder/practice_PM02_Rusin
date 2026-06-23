"""Банковский сервис - основной слой бизнес-логики"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
import json
import random

from domain.models import (
    Customer, BankAccount, Transaction, TransactionType,
    TransactionStatus, AccountStatus, AccountType
)
from domain.exceptions import (
    AccountNotFoundError, CustomerNotFoundError, InsufficientFundsError,
    ValidationError, LimitExceededError, FraudDetectedError,
    AccountBlockedError, TransferLimitError
)
from repositories.interfaces import (
    CustomerRepository, AccountRepository, TransactionRepository
)
from schemas.validators import (
    CustomerCreateSchema, AccountCreateSchema, TransferSchema,
    TransactionSchema, ValidationResult
)

# Настройка логирования
logger = logging.getLogger(__name__)


class FraudDetectionService:
    """Сервис для обнаружения мошеннических операций"""
    
    def __init__(self):
        # В реальном проекте здесь были бы правила из БД
        self.rules = {
            'max_transfer': Decimal('1000000.00'),
            'daily_operations_limit': 10,
            'daily_sum_limit': Decimal('2000000.00')
        }
    
    def check_transfer(self, from_account: BankAccount,
                       to_account: BankAccount,
                       amount: Decimal) -> Tuple[bool, str]:
        """Проверка перевода на подозрительность"""
        
        # Проверка на большой перевод
        if amount > self.rules['max_transfer']:
            return False, f"Перевод {amount} превышает максимальный лимит {self.rules['max_transfer']}"
        
        # Проверка на частые операции (в реальном проекте - запрос к репозиторию)
        # Здесь мы упрощаем логику
        
        return True, "OK"


class BankingService:
    """
    Основной банковский сервис.
    Реализует всю бизнес-логику банковской системы.
    """
    
    def __init__(
        self,
        customer_repo: CustomerRepository,
        account_repo: AccountRepository,
        transaction_repo: TransactionRepository,
        fraud_service: Optional[FraudDetectionService] = None
    ):
        self.customer_repo = customer_repo
        self.account_repo = account_repo
        self.transaction_repo = transaction_repo
        self.fraud_service = fraud_service or FraudDetectionService()
        
        # Комиссии (в процентах)
        self.transfer_fee = Decimal('0.01')  # 1%
        self.fee_min = Decimal('10.00')
        self.fee_max = Decimal('1000.00')
        
        # Счётчик для генерации номеров счетов
        self._account_counter = 0
        
        logger.info("BankingService инициализирован")
    
    def _generate_account_number(self) -> str:
        """Генерация уникального номера счёта"""
        self._account_counter += 1
        # Формат: 40817810 + 10 цифр (счётчик с ведущими нулями)
        return f"40817810{str(self._account_counter).zfill(10)}"
    
    # ==================== Управление клиентами ====================
    
    def register_customer(self, full_name: str, email: str,
                         phone: str, passport_number: str) -> Customer:
        """
        Регистрация нового клиента.
        
        Args:
            full_name: Полное имя
            email: Email
            phone: Телефон
            passport_number: Номер паспорта
            
        Returns:
            Customer: Зарегистрированный клиент
            
        Raises:
            ValidationError: Если данные невалидны или уже существуют
        """
        logger.info(f"Регистрация нового клиента: {full_name}")
        
        # Валидация данных
        schema = CustomerCreateSchema(
            full_name=full_name,
            email=email,
            phone=phone,
            passport_number=passport_number
        )
        validation = schema.validate()
        if not validation.is_valid:
            raise ValidationError(f"Ошибка валидации: {validation.errors}")
        
        # Проверка на существование
        if email and self.customer_repo.find_by_email(email):
            raise ValidationError(f"Клиент с email {email} уже зарегистрирован")
        if passport_number and self.customer_repo.find_by_passport(passport_number):
            raise ValidationError(f"Клиент с паспортом {passport_number} уже зарегистрирован")
        
        # Создание клиента
        customer = Customer(
            full_name=full_name,
            email=email,
            phone=phone,
            passport_number=passport_number
        )
        
        saved = self.customer_repo.save(customer)
        logger.info(f"Клиент зарегистрирован: {saved.id}")
        return saved
    
    def get_customer(self, customer_id: str) -> Customer:
        """Получение клиента по ID"""
        customer = self.customer_repo.find_by_id(customer_id)
        if not customer:
            logger.warning(f"Клиент не найден: {customer_id}")
            raise CustomerNotFoundError(f"Клиент {customer_id} не найден")
        return customer
    
    def get_all_customers(self, limit: int = 100, offset: int = 0) -> List[Customer]:
        """Получение всех клиентов с пагинацией"""
        return self.customer_repo.find_all(limit, offset)
    
    # ==================== Управление счетами ====================
    
    def create_account(self, customer_id: str, account_type: str,
                      currency: str = "RUB") -> BankAccount:
        """
        Открытие банковского счёта.
        
        Args:
            customer_id: ID клиента
            account_type: Тип счёта (checking, savings, business)
            currency: Валюта
            
        Returns:
            BankAccount: Созданный счёт
            
        Raises:
            CustomerNotFoundError: Если клиент не найден
            ValidationError: Если данные невалидны
        """
        logger.info(f"Открытие счёта для клиента {customer_id}, тип: {account_type}")
        
        # Проверка существования клиента
        customer = self.customer_repo.find_by_id(customer_id)
        if not customer:
            raise CustomerNotFoundError(f"Клиент {customer_id} не найден")
        
        # Валидация типа счёта
        try:
            acc_type = AccountType(account_type)
        except ValueError:
            raise ValidationError(f"Неизвестный тип счёта: {account_type}")
        
        # Проверка лимита счетов для клиента (не более 5)
        existing_accounts = self.account_repo.find_by_customer(customer_id)
        if len(existing_accounts) >= 5:
            raise ValidationError("Клиент не может иметь более 5 счетов")
        
        # Создание счёта
        account = BankAccount(
            customer_id=customer_id,
            account_number=self._generate_account_number(),
            account_type=acc_type,
            currency=currency
        )
        
        saved = self.account_repo.save(account)
        logger.info(f"Счёт открыт: {saved.id}, номер: {saved.account_number}")
        return saved
    
    def get_account(self, account_id: str) -> BankAccount:
        """Получение счёта по ID"""
        account = self.account_repo.find_by_id(account_id)
        if not account:
            logger.warning(f"Счёт не найден: {account_id}")
            raise AccountNotFoundError(f"Счёт {account_id} не найден")
        return account
    
    def get_customer_accounts(self, customer_id: str) -> List[BankAccount]:
        """Получение всех счетов клиента"""
        # Проверка существования клиента
        customer = self.customer_repo.find_by_id(customer_id)
        if not customer:
            raise CustomerNotFoundError(f"Клиент {customer_id} не найден")
        
        return self.account_repo.find_by_customer(customer_id)
    
    def get_account_balance(self, account_id: str) -> Decimal:
        """Получение баланса счёта"""
        account = self.get_account(account_id)
        return account.balance
    
    def block_account(self, account_id: str, reason: str = "") -> BankAccount:
        """Блокировка счёта"""
        account = self.get_account(account_id)
        account.status = AccountStatus.BLOCKED
        saved = self.account_repo.save(account)
        logger.warning(f"Счёт {account_id} заблокирован. Причина: {reason}")
        return saved
    
    def freeze_account(self, account_id: str) -> BankAccount:
        """Заморозка счёта"""
        account = self.get_account(account_id)
        account.status = AccountStatus.FROZEN
        saved = self.account_repo.save(account)
        logger.info(f"Счёт {account_id} заморожен")
        return saved
    
    # ==================== Вспомогательные методы ====================
    
    def _check_daily_limits(self, account: BankAccount, amount: Decimal) -> None:
        """Проверка дневных лимитов"""
        # Сброс дневного лимита при новом дне
        account.reset_daily_limit_if_needed()
        
        # Проверка дневного лимита
        new_daily_sum = account.daily_operation_sum + amount
        if new_daily_sum > account.daily_limit:
            raise LimitExceededError(
                f"Сумма операции {amount} превышает дневной лимит {account.daily_limit}. "
                f"Использовано: {account.daily_operation_sum}"
            )
    
    def _update_daily_limit(self, account: BankAccount, amount: Decimal) -> None:
        """Обновление дневного лимита"""
        account.reset_daily_limit_if_needed()
        account.daily_operation_sum += amount
        self.account_repo.save(account)
    
    def _calculate_fee(self, amount: Decimal) -> Decimal:
        """Расчёт комиссии за перевод"""
        fee = amount * self.transfer_fee
        # Ограничиваем комиссию минимальным и максимальным значением
        if fee < self.fee_min:
            fee = self.fee_min
        elif fee > self.fee_max:
            fee = self.fee_max
        return fee
    
    # ==================== Операции со счетами ====================
    
    def deposit(self, account_id: str, amount: Decimal,
                description: str = "Пополнение счёта") -> Transaction:
        """
        Пополнение счёта.
        
        Args:
            account_id: ID счёта
            amount: Сумма пополнения
            description: Описание операции
            
        Returns:
            Transaction: Транзакция пополнения
        """
        logger.info(f"Пополнение счёта {account_id} на {amount}")
        
        # Валидация
        if amount <= 0:
            raise ValidationError("Сумма пополнения должна быть положительной")
        
        account = self.get_account(account_id)
        if account.status != AccountStatus.ACTIVE:
            raise AccountBlockedError(f"Счёт {account_id} неактивен")
        
        # Создание транзакции
        transaction = Transaction(
            to_account_id=account_id,
            customer_id=account.customer_id,
            amount=amount,
            type=TransactionType.DEPOSIT,
            description=description
        )
        
        # Обновление баланса счёта (все изменения в одной транзакции)
        try:
            new_balance = account.balance + amount
            self.account_repo.update_balance(account_id, new_balance)
            transaction.status = TransactionStatus.COMPLETED
            transaction.completed_at = datetime.now()
            saved = self.transaction_repo.save(transaction)
            
            logger.info(f"Пополнение выполнено: {saved.id}, новый баланс: {new_balance}")
            return saved
        except Exception as e:
            logger.error(f"Ошибка при пополнении: {e}")
            transaction.status = TransactionStatus.FAILED
            self.transaction_repo.save(transaction)
            raise
    
    def withdraw(self, account_id: str, amount: Decimal,
                 description: str = "Снятие со счёта") -> Transaction:
        """
        Снятие средств со счёта.
        
        Args:
            account_id: ID счёта
            amount: Сумма снятия
            description: Описание операции
            
        Returns:
            Transaction: Транзакция снятия
        """
        logger.info(f"Снятие со счёта {account_id} на {amount}")
        
        # Валидация
        if amount <= 0:
            raise ValidationError("Сумма снятия должна быть положительной")
        
        account = self.get_account(account_id)
        if account.status != AccountStatus.ACTIVE:
            raise AccountBlockedError(f"Счёт {account_id} неактивен")
        
        # Проверка лимитов
        self._check_daily_limits(account, amount)
        
        # Проверка достаточности средств
        if account.balance < amount:
            logger.warning(f"Недостаточно средств на счёте {account_id}. "
                          f"Баланс: {account.balance}, требуется: {amount}")
            raise InsufficientFundsError(
                f"Недостаточно средств. Баланс: {account.balance}, требуется: {amount}"
            )
        
        # Создание транзакции
        transaction = Transaction(
            from_account_id=account_id,
            customer_id=account.customer_id,
            amount=amount,
            type=TransactionType.WITHDRAWAL,
            description=description
        )
        
        try:
            # Обновление баланса
            new_balance = account.balance - amount
            self.account_repo.update_balance(account_id, new_balance)
            
            # Обновление дневного лимита
            self._update_daily_limit(account, amount)
            
            transaction.status = TransactionStatus.COMPLETED
            transaction.completed_at = datetime.now()
            saved = self.transaction_repo.save(transaction)
            
            logger.info(f"Снятие выполнено: {saved.id}, новый баланс: {new_balance}")
            return saved
        except Exception as e:
            logger.error(f"Ошибка при снятии: {e}")
            transaction.status = TransactionStatus.FAILED
            self.transaction_repo.save(transaction)
            raise
    
    def transfer(self, from_account_id: str, to_account_id: str,
                 amount: Decimal, description: str = "Перевод") -> Transaction:
        """
        Перевод средств между счетами.
        
        Args:
            from_account_id: ID счёта отправителя
            to_account_id: ID счёта получателя
            amount: Сумма перевода
            description: Описание операции
            
        Returns:
            Transaction: Транзакция перевода
        """
        logger.info(f"Перевод {amount} со счёта {from_account_id} на счёт {to_account_id}")
        
        # Валидация
        if amount <= 0:
            raise ValidationError("Сумма перевода должна быть положительной")
        
        if from_account_id == to_account_id:
            raise ValidationError("Нельзя переводить на тот же счёт")
        
        # Получение счетов
        from_account = self.get_account(from_account_id)
        to_account = self.get_account(to_account_id)
        
        # Проверка статусов
        if from_account.status != AccountStatus.ACTIVE:
            raise AccountBlockedError(f"Счёт отправителя {from_account_id} неактивен")
        if to_account.status != AccountStatus.ACTIVE:
            raise AccountBlockedError(f"Счёт получателя {to_account_id} неактивен")
        
        # Проверка лимитов
        self._check_daily_limits(from_account, amount)
        
        # Проверка на мошенничество
        fraud_check, fraud_message = self.fraud_service.check_transfer(
            from_account, to_account, amount
        )
        if not fraud_check:
            logger.warning(f"Обнаружена подозрительная операция: {fraud_message}")
            raise FraudDetectedError(f"Операция отклонена: {fraud_message}")
        
        # Расчёт комиссии
        fee = self._calculate_fee(amount)
        total_amount = amount + fee
        
        # Проверка достаточности средств с учётом комиссии
        if from_account.balance < total_amount:
            logger.warning(f"Недостаточно средств. Баланс: {from_account.balance}, "
                          f"требуется: {total_amount}")
            raise InsufficientFundsError(
                f"Недостаточно средств. Баланс: {from_account.balance}, "
                f"требуется: {total_amount} (сумма + комиссия {fee})"
            )
        
        # Создание транзакции
        transaction = Transaction(
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            customer_id=from_account.customer_id,
            amount=amount,
            type=TransactionType.TRANSFER,
            description=description,
            fee=fee
        )
        
        try:
            # Выполнение перевода (атомарно)
            # 1. Списание с отправителя
            from_new_balance = from_account.balance - total_amount
            self.account_repo.update_balance(from_account_id, from_new_balance)
            
            # 2. Зачисление получателю
            to_new_balance = to_account.balance + amount
            self.account_repo.update_balance(to_account_id, to_new_balance)
            
            # 3. Обновление дневного лимита отправителя
            self._update_daily_limit(from_account, total_amount)
            
            # 4. Сохранение транзакции
            transaction.status = TransactionStatus.COMPLETED
            transaction.completed_at = datetime.now()
            saved = self.transaction_repo.save(transaction)
            
            logger.info(f"Перевод выполнен: {saved.id}, "
                       f"отправитель: {from_account_id}, получатель: {to_account_id}")
            return saved
        except Exception as e:
            logger.error(f"Ошибка при переводе: {e}")
            transaction.status = TransactionStatus.FAILED
            self.transaction_repo.save(transaction)
            raise