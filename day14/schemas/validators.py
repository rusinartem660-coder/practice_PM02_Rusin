"""Схемы и валидаторы для банковской системы"""

import re
from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional, Any
from datetime import datetime


@dataclass
class ValidationResult:
    """Результат валидации"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    
    def add_error(self, error: str):
        self.errors.append(error)
        self.is_valid = False


@dataclass
class CustomerCreateSchema:
    """Схема создания клиента"""
    full_name: str
    email: str
    phone: str
    passport_number: str
    
    def validate(self) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        
        # Проверка имени
        if not self.full_name or len(self.full_name.strip()) < 2:
            result.add_error("Имя должно содержать минимум 2 символа")
        if len(self.full_name.strip()) > 100:
            result.add_error("Имя не должно превышать 100 символов")
        
        # Проверка email
        if self.email:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, self.email):
                result.add_error("Некорректный формат email")
        
        # Проверка телефона
        if self.phone:
            phone_pattern = r'^\+?[0-9]{10,15}$'
            if not re.match(phone_pattern, self.phone.replace('-', '').replace(' ', '')):
                result.add_error("Некорректный формат телефона")
        
        # Проверка паспорта
        if self.passport_number:
            passport_pattern = r'^[0-9]{4}\s?[0-9]{6}$'
            if not re.match(passport_pattern, self.passport_number.replace(' ', '')):
                result.add_error("Некорректный формат паспорта (ожидается: XXXX XXXXXX)")
        
        return result


@dataclass
class AccountCreateSchema:
    """Схема создания счёта"""
    customer_id: str
    account_type: str
    currency: str = "RUB"
    
    def validate(self) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        
        if not self.customer_id:
            result.add_error("ID клиента обязателен")
        
        valid_types = ["checking", "savings", "business"]
        if self.account_type.lower() not in valid_types:
            result.add_error(f"Тип счёта должен быть одним из: {', '.join(valid_types)}")
        
        valid_currencies = ["RUB", "USD", "EUR"]
        if self.currency.upper() not in valid_currencies:
            result.add_error(f"Валюта должна быть одной из: {', '.join(valid_currencies)}")
        
        return result


@dataclass
class TransferSchema:
    """Схема перевода"""
    from_account_id: str
    to_account_id: str
    amount: Decimal
    description: str = ""
    
    def validate(self) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        
        if not self.from_account_id:
            result.add_error("ID счёта отправителя обязателен")
        
        if not self.to_account_id:
            result.add_error("ID счёта получателя обязателен")
        
        if self.from_account_id == self.to_account_id:
            result.add_error("Нельзя переводить на тот же счёт")
        
        if self.amount <= 0:
            result.add_error("Сумма должна быть положительной")
        
        if self.amount > Decimal('1000000000'):
            result.add_error("Сумма не должна превышать 1 000 000 000")
        
        if len(self.description) > 255:
            result.add_error("Описание не должно превышать 255 символов")
        
        return result


@dataclass
class TransactionSchema:
    """Схема транзакции"""
    account_id: str
    amount: Decimal
    description: str = ""
    
    def validate(self) -> ValidationResult:
        result = ValidationResult(is_valid=True)
        
        if not self.account_id:
            result.add_error("ID счёта обязателен")
        
        if self.amount <= 0:
            result.add_error("Сумма должна быть положительной")
        
        if self.amount > Decimal('1000000000'):
            result.add_error("Сумма не должна превышать 1 000 000 000")
        
        return result