"""Интерфейсы репозиториев"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

from domain.models import Customer, BankAccount, Transaction, TransactionStatus


class CustomerRepository(ABC):
    """Репозиторий для работы с клиентами"""
    
    @abstractmethod
    def save(self, customer: Customer) -> Customer:
        """Сохранить клиента"""
        pass
    
    @abstractmethod
    def find_by_id(self, customer_id: str) -> Optional[Customer]:
        """Найти клиента по ID"""
        pass
    
    @abstractmethod
    def find_by_email(self, email: str) -> Optional[Customer]:
        """Найти клиента по email"""
        pass
    
    @abstractmethod
    def find_by_passport(self, passport_number: str) -> Optional[Customer]:
        """Найти клиента по паспорту"""
        pass
    
    @abstractmethod
    def find_all(self, limit: int = 100, offset: int = 0) -> List[Customer]:
        """Получить всех клиентов с пагинацией"""
        pass
    
    @abstractmethod
    def delete(self, customer_id: str) -> bool:
        """Удалить клиента"""
        pass


class AccountRepository(ABC):
    """Репозиторий для работы со счетами"""
    
    @abstractmethod
    def save(self, account: BankAccount) -> BankAccount:
        """Сохранить счёт"""
        pass
    
    @abstractmethod
    def find_by_id(self, account_id: str) -> Optional[BankAccount]:
        """Найти счёт по ID"""
        pass
    
    @abstractmethod
    def find_by_customer(self, customer_id: str) -> List[BankAccount]:
        """Найти все счета клиента"""
        pass
    
    @abstractmethod
    def find_by_number(self, account_number: str) -> Optional[BankAccount]:
        """Найти счёт по номеру"""
        pass
    
    @abstractmethod
    def update_balance(self, account_id: str, new_balance: Decimal) -> BankAccount:
        """Обновить баланс счёта"""
        pass
    
    @abstractmethod
    def find_all(self, limit: int = 100, offset: int = 0) -> List[BankAccount]:
        """Получить все счета с пагинацией"""
        pass


class TransactionRepository(ABC):
    """Репозиторий для работы с транзакциями"""
    
    @abstractmethod
    def save(self, transaction: Transaction) -> Transaction:
        """Сохранить транзакцию"""
        pass
    
    @abstractmethod
    def find_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """Найти транзакцию по ID"""
        pass
    
    @abstractmethod
    def find_by_account(self, account_id: str, 
                        limit: int = 50, 
                        offset: int = 0) -> List[Transaction]:
        """Найти транзакции по счёту"""
        pass
    
    @abstractmethod
    def find_by_customer(self, customer_id: str,
                         limit: int = 50,
                         offset: int = 0) -> List[Transaction]:
        """Найти транзакции по клиенту"""
        pass
    
    @abstractmethod
    def find_by_date_range(self, start_date: datetime,
                           end_date: datetime,
                           account_id: Optional[str] = None) -> List[Transaction]:
        """Найти транзакции за период"""
        pass
    
    @abstractmethod
    def update_status(self, transaction_id: str,
                      status: TransactionStatus) -> Transaction:
        """Обновить статус транзакции"""
        pass