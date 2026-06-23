"""In-memory реализация репозиториев"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
import copy

from repositories.interfaces import (
    CustomerRepository, 
    AccountRepository, 
    TransactionRepository
)
from domain.models import Customer, BankAccount, Transaction, TransactionStatus
from domain.exceptions import ValidationError


class InMemoryCustomerRepository(CustomerRepository):
    """In-memory репозиторий клиентов"""
    
    def __init__(self):
        self._storage: Dict[str, Customer] = {}
        self._email_index: Dict[str, str] = {}
        self._passport_index: Dict[str, str] = {}
    
    def save(self, customer: Customer) -> Customer:
        if not customer.id:
            raise ValidationError("ID клиента не может быть пустым")
        
        # Проверка уникальности email
        if customer.email:
            existing = self.find_by_email(customer.email)
            if existing and existing.id != customer.id:
                raise ValidationError(f"Клиент с email {customer.email} уже существует")
        
        # Проверка уникальности паспорта
        if customer.passport_number:
            existing = self.find_by_passport(customer.passport_number)
            if existing and existing.id != customer.id:
                raise ValidationError(f"Клиент с паспортом {customer.passport_number} уже существует")
        
        self._storage[customer.id] = copy.deepcopy(customer)
        if customer.email:
            self._email_index[customer.email] = customer.id
        if customer.passport_number:
            self._passport_index[customer.passport_number] = customer.id
        return customer
    
    def find_by_id(self, customer_id: str) -> Optional[Customer]:
        if customer_id in self._storage:
            return copy.deepcopy(self._storage[customer_id])
        return None
    
    def find_by_email(self, email: str) -> Optional[Customer]:
        if email in self._email_index:
            return self.find_by_id(self._email_index[email])
        return None
    
    def find_by_passport(self, passport_number: str) -> Optional[Customer]:
        if passport_number in self._passport_index:
            return self.find_by_id(self._passport_index[passport_number])
        return None
    
    def find_all(self, limit: int = 100, offset: int = 0) -> List[Customer]:
        customers = list(self._storage.values())
        return copy.deepcopy(customers[offset:offset + limit])
    
    def delete(self, customer_id: str) -> bool:
        if customer_id in self._storage:
            customer = self._storage[customer_id]
            if customer.email and customer.email in self._email_index:
                del self._email_index[customer.email]
            if customer.passport_number and customer.passport_number in self._passport_index:
                del self._passport_index[customer.passport_number]
            del self._storage[customer_id]
            return True
        return False


class InMemoryAccountRepository(AccountRepository):
    """In-memory репозиторий счетов"""
    
    def __init__(self):
        self._storage: Dict[str, BankAccount] = {}
        self._customer_index: Dict[str, List[str]] = {}
        self._number_index: Dict[str, str] = {}
    
    def save(self, account: BankAccount) -> BankAccount:
        if not account.id:
            raise ValidationError("ID счёта не может быть пустым")
        
        # Проверка уникальности номера счёта
        if account.account_number:
            existing = self.find_by_number(account.account_number)
            if existing and existing.id != account.id:
                raise ValidationError(f"Счёт с номером {account.account_number} уже существует")
        
        self._storage[account.id] = copy.deepcopy(account)
        if account.account_number:
            self._number_index[account.account_number] = account.id
        
        # Обновление индекса по клиентам
        if account.customer_id not in self._customer_index:
            self._customer_index[account.customer_id] = []
        if account.id not in self._customer_index[account.customer_id]:
            self._customer_index[account.customer_id].append(account.id)
        
        return account
    
    def find_by_id(self, account_id: str) -> Optional[BankAccount]:
        if account_id in self._storage:
            return copy.deepcopy(self._storage[account_id])
        return None
    
    def find_by_customer(self, customer_id: str) -> List[BankAccount]:
        if customer_id in self._customer_index:
            return [self.find_by_id(acc_id) for acc_id in self._customer_index[customer_id] 
                    if acc_id in self._storage]
        return []
    
    def find_by_number(self, account_number: str) -> Optional[BankAccount]:
        if account_number in self._number_index:
            return self.find_by_id(self._number_index[account_number])
        return None
    
    def update_balance(self, account_id: str, new_balance: Decimal) -> BankAccount:
        if account_id not in self._storage:
            raise ValidationError(f"Счёт {account_id} не найден")
        if new_balance < 0:
            raise ValidationError("Баланс не может быть отрицательным")
        
        account = self._storage[account_id]
        account.balance = new_balance
        account.updated_at = datetime.now()
        return copy.deepcopy(account)
    
    def find_all(self, limit: int = 100, offset: int = 0) -> List[BankAccount]:
        accounts = list(self._storage.values())
        return copy.deepcopy(accounts[offset:offset + limit])


class InMemoryTransactionRepository(TransactionRepository):
    """In-memory репозиторий транзакций"""
    
    def __init__(self):
        self._storage: Dict[str, Transaction] = {}
        self._account_index: Dict[str, List[str]] = {}
        self._customer_index: Dict[str, List[str]] = {}
    
    def save(self, transaction: Transaction) -> Transaction:
        if not transaction.id:
            raise ValidationError("ID транзакции не может быть пустым")
        
        self._storage[transaction.id] = copy.deepcopy(transaction)
        
        # Индексы для быстрого поиска
        if transaction.from_account_id:
            if transaction.from_account_id not in self._account_index:
                self._account_index[transaction.from_account_id] = []
            if transaction.id not in self._account_index[transaction.from_account_id]:
                self._account_index[transaction.from_account_id].append(transaction.id)
        
        if transaction.to_account_id:
            if transaction.to_account_id not in self._account_index:
                self._account_index[transaction.to_account_id] = []
            if transaction.id not in self._account_index[transaction.to_account_id]:
                self._account_index[transaction.to_account_id].append(transaction.id)
        
        if transaction.customer_id:
            if transaction.customer_id not in self._customer_index:
                self._customer_index[transaction.customer_id] = []
            if transaction.id not in self._customer_index[transaction.customer_id]:
                self._customer_index[transaction.customer_id].append(transaction.id)
        
        return transaction
    
    def find_by_id(self, transaction_id: str) -> Optional[Transaction]:
        if transaction_id in self._storage:
            return copy.deepcopy(self._storage[transaction_id])
        return None
    
    def find_by_account(self, account_id: str, 
                        limit: int = 50, 
                        offset: int = 0) -> List[Transaction]:
        if account_id in self._account_index:
            transactions = [self.find_by_id(t_id) for t_id in self._account_index[account_id]
                           if t_id in self._storage]
            return transactions[offset:offset + limit]
        return []
    
    def find_by_customer(self, customer_id: str,
                         limit: int = 50,
                         offset: int = 0) -> List[Transaction]:
        if customer_id in self._customer_index:
            transactions = [self.find_by_id(t_id) for t_id in self._customer_index[customer_id]
                           if t_id in self._storage]
            return transactions[offset:offset + limit]
        return []
    
    def find_by_date_range(self, start_date: datetime,
                           end_date: datetime,
                           account_id: Optional[str] = None) -> List[Transaction]:
        transactions = []
        
        for trans in self._storage.values():
            if start_date <= trans.created_at <= end_date:
                if account_id:
                    if trans.from_account_id == account_id or trans.to_account_id == account_id:
                        transactions.append(copy.deepcopy(trans))
                else:
                    transactions.append(copy.deepcopy(trans))
        
        return transactions
    
    def update_status(self, transaction_id: str,
                      status: TransactionStatus) -> Transaction:
        if transaction_id not in self._storage:
            raise ValidationError(f"Транзакция {transaction_id} не найдена")
        
        transaction = self._storage[transaction_id]
        transaction.status = status
        if status == TransactionStatus.COMPLETED:
            transaction.completed_at = datetime.now()
        return copy.deepcopy(transaction)