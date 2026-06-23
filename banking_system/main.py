"""Точка входа в приложение. Демонстрация работы банковской системы."""

import logging
from decimal import Decimal
from datetime import datetime

from repositories.in_memory import (
    InMemoryCustomerRepository,
    InMemoryAccountRepository,
    InMemoryTransactionRepository
)
from services.banking_service import BankingService, FraudDetectionService
from domain.exceptions import (
    AccountNotFoundError, CustomerNotFoundError, 
    InsufficientFundsError, ValidationError,
    FraudDetectedError, AccountBlockedError
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_banking_system():
    """Демонстрация работы банковской системы"""
    
    logger.info("=" * 60)
    logger.info("ЗАПУСК ДЕМОНСТРАЦИИ БАНКОВСКОЙ СИСТЕМЫ")
    logger.info("=" * 60)
    
    # Инициализация репозиториев и сервиса
    customer_repo = InMemoryCustomerRepository()
    account_repo = InMemoryAccountRepository()
    transaction_repo = InMemoryTransactionRepository()
    fraud_service = FraudDetectionService()
    
    banking = BankingService(
        customer_repo=customer_repo,
        account_repo=account_repo,
        transaction_repo=transaction_repo,
        fraud_service=fraud_service
    )
    
    # 1. Регистрация клиента
    logger.info("\n1. РЕГИСТРАЦИЯ КЛИЕНТА")
    try:
        customer = banking.register_customer(
            full_name="Алексей Смирнов",
            email="alexey@mail.ru",
            phone="+79161112233",
            passport_number="4444 555555"
        )
        logger.info(f"✅ Клиент зарегистрирован: {customer.id}, {customer.full_name}")
    except ValidationError as e:
        logger.error(f"❌ Ошибка: {e}")
        return
    
    # 2. Открытие счёта
    logger.info("\n2. ОТКРЫТИЕ СЧЁТА")
    try:
        account1 = banking.create_account(
            customer_id=customer.id,
            account_type="checking",
            currency="RUB"
        )
        logger.info(f"✅ Счёт открыт: {account1.id}, номер: {account1.account_number}")
    except ValidationError as e:
        logger.error(f"❌ Ошибка: {e}")
        return
    
    # 3. Открытие второго счёта
    logger.info("\n3. ОТКРЫТИЕ ВТОРОГО СЧЁТА")
    try:
        account2 = banking.create_account(
            customer_id=customer.id,
            account_type="savings",
            currency="RUB"
        )
        logger.info(f"✅ Второй счёт открыт: {account2.id}")
    except ValidationError as e:
        logger.error(f"❌ Ошибка: {e}")
        return
    
    # 4. Пополнение счёта
    logger.info("\n4. ПОПОЛНЕНИЕ СЧЁТА")
    try:
        deposit = banking.deposit(
            account_id=account1.id,
            amount=Decimal('15000.00'),
            description="Пополнение с карты"
        )
        logger.info(f"✅ Пополнено на 15000.00 RUB. ID транзакции: {deposit.id}")
        balance = banking.get_account_balance(account1.id)
        logger.info(f"   Баланс счёта {account1.account_number}: {balance} RUB")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return
    
    # 5. Перевод между счетами
    logger.info("\n5. ПЕРЕВОД МЕЖДУ СЧЕТАМИ")
    try:
        transfer = banking.transfer(
            from_account_id=account1.id,
            to_account_id=account2.id,
            amount=Decimal('3000.00'),
            description="Перевод на накопительный счёт"
        )
        logger.info(f"✅ Перевод выполнен. ID транзакции: {transfer.id}")
        logger.info(f"   Сумма: {transfer.amount} RUB, Комиссия: {transfer.fee} RUB")
        
        balance1 = banking.get_account_balance(account1.id)
        balance2 = banking.get_account_balance(account2.id)
        logger.info(f"   Баланс счёта 1: {balance1} RUB")
        logger.info(f"   Баланс счёта 2: {balance2} RUB")
    except InsufficientFundsError as e:
        logger.error(f"❌ Ошибка: {e}")
    except FraudDetectedError as e:
        logger.error(f"❌ Операция отклонена антифрод-системой: {e}")
    
    # 6. Снятие средств
    logger.info("\n6. СНЯТИЕ СРЕДСТВ")
    try:
        withdraw = banking.withdraw(
            account_id=account1.id,
            amount=Decimal('500.00'),
            description="Снятие в банкомате"
        )
        logger.info(f"✅ Снято 500.00 RUB. ID транзакции: {withdraw.id}")
        balance = banking.get_account_balance(account1.id)
        logger.info(f"   Баланс счёта {account1.account_number}: {balance} RUB")
    except InsufficientFundsError as e:
        logger.error(f"❌ Ошибка: {e}")
    except LimitExceededError as e:
        logger.error(f"❌ Ошибка: {e}")
    
    # 7. Получение выписки по счёту
    logger.info("\n7. ВЫПИСКА ПО СЧЁТУ")
    try:
        transactions = banking.transaction_repo.find_by_account(account1.id, limit=10)
        logger.info(f"   Последние транзакции по счёту {account1.account_number}:")
        for i, tx in enumerate(transactions, 1):
            tx_type = tx.type.value
            amount = tx.amount
            status = tx.status.value
            logger.info(f"   {i}. {tx_type}: {amount} RUB ({status}) - {tx.description}")
    except Exception as e:
        logger.error(f"❌ Ошибка при получении выписки: {e}")
    
    # 8. Информация о клиенте
    logger.info("\n8. ИНФОРМАЦИЯ О КЛИЕНТЕ")
    try:
        customer_info = banking.get_customer(customer.id)
        accounts = banking.get_customer_accounts(customer.id)
        
        logger.info(f"   Клиент: {customer_info.full_name}")
        logger.info(f"   Email: {customer_info.email}")
        logger.info(f"   Телефон: {customer_info.phone}")
        logger.info(f"   Количество счетов: {len(accounts)}")
        total_balance = sum(acc.balance for acc in accounts)
        logger.info(f"   Общий баланс: {total_balance} RUB")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    logger.info("=" * 60)


if __name__ == "__main__":
    demo_banking_system()