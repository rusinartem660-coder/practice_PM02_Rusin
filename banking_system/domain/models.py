"""Доменные модели банковской системы"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
import uuid


class AccountType(Enum):
    """Типы счетов"""
    CHECKING = "checking"
    SAVINGS = "savings"
    BUSINESS = "business"


class AccountStatus(Enum):
    """Статусы счёта"""
    ACTIVE = "active"
    FROZEN = "frozen"
    BLOCKED = "blocked"
    CLOSED = "closed"


class TransactionType(Enum):
    """Типы транзакций"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    FEE = "fee"
    INTEREST = "interest"


class TransactionStatus(Enum):
    """Статусы транзакций"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Customer:
    """Клиент банка"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    full_name: str = ""
    email: str = ""
    phone: str = ""
    passport_number: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    
    def __post_init__(self):
        if not self.full_name or len(self.full_name.strip()) < 2:
            from domain.exceptions import ValidationError
            raise ValidationError("Имя клиента должно содержать минимум 2 символа")
        if self.email and '@' not in self.email:
            from domain.exceptions import ValidationError
            raise ValidationError("Некорректный email")


@dataclass
class BankAccount:
    """Банковский счёт"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    account_number: str = ""
    account_type: AccountType = AccountType.CHECKING
    balance: Decimal = Decimal('0.00')
    currency: str = "RUB"
    status: AccountStatus = AccountStatus.ACTIVE
    daily_limit: Decimal = Decimal('100000.00')
    monthly_limit: Decimal = Decimal('1000000.00')
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    daily_operation_sum: Decimal = Decimal('0.00')
    daily_operation_date: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if self.balance < 0:
            from domain.exceptions import ValidationError
            raise ValidationError("Баланс не может быть отрицательным")
        if self.daily_limit < 0 or self.monthly_limit < 0:
            from domain.exceptions import ValidationError
            raise ValidationError("Лимиты не могут быть отрицательными")
    
    def can_withdraw(self, amount: Decimal) -> bool:
        """Проверка возможности снятия"""
        if self.status != AccountStatus.ACTIVE:
            return False
        if self.balance < amount:
            return False
        if amount > self.daily_limit:
            return False
        return True
    
    def reset_daily_limit_if_needed(self):
        """Сброс дневного лимита при новом дне"""
        today = datetime.now().date()
        if self.daily_operation_date.date() != today:
            self.daily_operation_sum = Decimal('0.00')
            self.daily_operation_date = datetime.now()


@dataclass
class Transaction:
    """Транзакция"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_account_id: Optional[str] = None
    to_account_id: Optional[str] = None
    customer_id: str = ""
    amount: Decimal = Decimal('0.00')
    currency: str = "RUB"
    type: TransactionType = TransactionType.TRANSFER
    status: TransactionStatus = TransactionStatus.PENDING
    description: str = ""
    fee: Decimal = Decimal('0.00')
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.amount <= 0:
            from domain.exceptions import ValidationError
            raise ValidationError("Сумма должна быть положительной")
        if self.fee < 0:
            from domain.exceptions import ValidationError
            raise ValidationError("Комиссия не может быть отрицательной")


@dataclass
class FraudRule:
    """Правило для антифрод-системы"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    is_active: bool = True
    max_amount: Optional[Decimal] = None
    max_daily_operations: Optional[int] = None
    max_daily_sum: Optional[Decimal] = None
    suspicious_countries: List[str] = field(default_factory=list)