#!/usr/bin/env python3
"""
backup_coinguard_standalone.py - Автономная система резервного копирования
Вариант 6: Криптобиржа
НЕ ТРЕБУЕТ PostgreSQL или AWS
"""

import json
import os
import shutil
import hashlib
import gzip
import time
from datetime import datetime, timedelta
import random

# ============================================================
# Класс для эмуляции базы данных
# ============================================================
class DatabaseEmulator:
    """Эмуляция базы данных для демонстрации"""
    
    def __init__(self):
        self.data = {
            'users': [
                {'id': 1, 'username': 'trader1', 'balance_btc': 1.5, 'balance_usdt': 100000},
                {'id': 2, 'username': 'trader2', 'balance_btc': 0.3, 'balance_usdt': 50000},
                {'id': 3, 'username': 'whale1', 'balance_btc': 500, 'balance_usdt': 5000000},
                {'id': 4, 'username': 'institutional1', 'balance_btc': 1000, 'balance_usdt': 10000000},
                {'id': 5, 'username': 'retail1', 'balance_btc': 0.01, 'balance_usdt': 1000}
            ],
            'orders': [
                {'id': 1, 'pair': 'BTC/USDT', 'side': 'BUY', 'price': 65000, 'quantity': 0.5, 'status': 'filled'},
                {'id': 2, 'pair': 'BTC/USDT', 'side': 'SELL', 'price': 68000, 'quantity': 0.3, 'status': 'open'},
                {'id': 3, 'pair': 'ETH/USDT', 'side': 'BUY', 'price': 3500, 'quantity': 10, 'status': 'partial'}
            ],
            'trades': [
                {'id': 1, 'pair': 'BTC/USDT', 'price': 66000, 'quantity': 0.5, 'buyer': 1, 'seller': 2},
                {'id': 2, 'pair': 'BTC/USDT', 'price': 67000, 'quantity': 2, 'buyer': 4, 'seller': 2}
            ],
            'blockchain': {
                'bitcoin': {'height': 800001, 'hash': '0000000000000000000123456789abcdef'},
                'ethereum': {'height': 18000001, 'hash': '0x123456789abcdef123456789abcdef123456789b'},
                'solana': {'height': 150000000, 'hash': 'solana_hash_123456'}
            },
            'hsm_keys': {
                'encryption': 'enc_key_12345',
                'signing': 'sign_key_67890',
                'recovery': 'recovery_key_abcde'
            },
            'audit_log': [
                {'user': 1, 'action': 'login', 'time': '2026-06-25 14:00:00'},
                {'user': 3, 'action': 'trade', 'time': '2026-06-25 14:05:00'},
                {'user': 4, 'action': 'withdraw', 'time': '2026-06-25 14:10:00'}
            ]
        }
        self.last_update = datetime.now()
    
    def get_data(self):
        """Получение всех данных"""
        return self.data
    
    def get_users(self):
        return self.data['users']
    
    def get_balances(self):
        return [(u['username'], u['balance_btc'], u['balance_usdt']) for u in self.data['users']]
    
    def get_orders(self):
        return self.data['orders']
    
    def get_blockchain_info(self):
        return self.data['blockchain']

# ============================================================
# Основной класс системы бэкапов
# ============================================================
class CoinGuardBackupSystem:
    
    def __init__(self):
        self.db = DatabaseEmulator()
        self.backup_dir = "./backups/"
        self.wal_dir = "./backups/wal/"
        self.full_dir = "./backups/full/"
        self.archive_dir = "./backups/archive/"
        self.log_file = "./backups/backup_history.json"
        self.retention_days = 7
        
        # Создание директорий
        for dir_path in [self.backup_dir, self.wal_dir, self.full_dir, self.archive_dir]:
            os.makedirs(dir_path, exist_ok=True)
        
        print("=" * 70)
        print("  🏦 CoinGuard - Система резервного копирования")
        print("  Вариант 6: Криптобиржа")
        print("=" * 70)
        print(f"  📁 Директория бэкапов: {self.backup_dir}")
        print(f"  📅 Retention: {self.retention_days} дней")
        print("=" * 70)
    
    # ============================================================
    # 1. Вычисление контрольной суммы
    # ============================================================
    def calculate_checksum(self, file_path):
        """Вычисление SHA-256 контрольной суммы"""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            print(f"❌ Ошибка вычисления контрольной суммы: {e}")
            return None
    
    # ============================================================
    # 2. Полный бэкап (Full Backup)
    # ============================================================
    def create_full_backup(self):
        """Создание полного бэкапа базы данных"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.full_dir}/full_backup_{timestamp}.json"
        
        print(f"\n📦 Создание полного бэкапа...")
        
        try:
            # Получение данных
            data = self.db.get_data()
            
            # Добавление метаданных
            backup_data = {
                'backup_type': 'full',
                'timestamp': timestamp,
                'created_at': datetime.now().isoformat(),
                'data_version': '1.0',
                'database_name': 'coinguard',
                'total_users': len(data['users']),
                'total_orders': len(data['orders']),
                'total_trades': len(data['trades']),
                'data': data
            }
            
            # Сохранение в JSON
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            # Создание сжатой версии
            compressed_file = f"{filename}.gz"
            with open(filename, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            # Вычисление контрольной суммы
            checksum = self.calculate_checksum(compressed_file)
            
            # Информация о бэкапе
            size_mb = os.path.getsize(compressed_file) / (1024 * 1024)
            
            print(f"  ✅ Полный бэкап создан:")
            print(f"     📄 Файл: {compressed_file}")
            print(f"     📊 Размер: {size_mb:.2f} МБ")
            print(f"     🔑 Контрольная сумма: {checksum[:16]}...")
            
            # Сохранение в журнал
            self._log_backup('full', compressed_file, size_mb, checksum)
            
            # Очистка временного файла
            os.remove(filename)
            
            return {'status': 'success', 'file': compressed_file, 'checksum': checksum}
            
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    # ============================================================
    # 3. WAL-бэкап (Incremental / Transaction Logs)
    # ============================================================
    def create_wal_backup(self):
        """Создание WAL-бэкапа (инкрементальный)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.wal_dir}/wal_{timestamp}.json"
        
        print(f"\n📝 Создание WAL-бэкапа...")
        
        try:
            # Эмуляция WAL-записей
            wal_data = {
                'backup_type': 'wal',
                'timestamp': timestamp,
                'created_at': datetime.now().isoformat(),
                'wal_position': f'0/{random.randint(1000000, 9999999):X}',
                'last_commit_lsn': f'0/{random.randint(1000000, 9999999):X}',
                'transactions': [
                    {
                        'tx_id': random.randint(1000, 9999),
                        'user_id': random.randint(1, 5),
                        'operation': random.choice(['insert', 'update', 'delete']),
                        'table': random.choice(['users', 'orders', 'balances']),
                        'timestamp': datetime.now().isoformat()
                    }
                    for _ in range(random.randint(5, 20))
                ],
                'changes': {
                    'users_modified': random.randint(0, 3),
                    'orders_created': random.randint(0, 5),
                    'trades_executed': random.randint(0, 2)
                }
            }
            
            # Сохранение
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(wal_data, f, indent=2, ensure_ascii=False)
            
            # Сжатие
            compressed_file = f"{filename}.gz"
            with open(filename, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            checksum = self.calculate_checksum(compressed_file)
            size_mb = os.path.getsize(compressed_file) / (1024 * 1024)
            
            print(f"  ✅ WAL-бэкап создан:")
            print(f"     📄 Файл: {compressed_file}")
            print(f"     📊 Размер: {size_mb:.2f} МБ")
            print(f"     📍 WAL позиция: {wal_data['wal_position']}")
            print(f"     🔑 Контрольная сумма: {checksum[:16]}...")
            
            self._log_backup('wal', compressed_file, size_mb, checksum)
            os.remove(filename)
            
            return {'status': 'success', 'file': compressed_file, 'checksum': checksum}
            
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            return {'status': 'failed', 'error': str(e)}
    
    # ============================================================
    # 4. Бэкап блокчейн-узлов
    # ============================================================
    def backup_blockchain_nodes(self):
        """Бэкап блокчейн-узлов (Bitcoin, Ethereum, Solana)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"\n⛓️ Бэкап блокчейн-узлов...")
        
        blockchain_data = self.db.get_blockchain_info()
        
        for node_name, node_data in blockchain_data.items():
            filename = f"{self.backup_dir}/blockchain_{node_name}_{timestamp}.json"
            
            backup_data = {
                'backup_type': 'blockchain_snapshot',
                'node': node_name,
                'timestamp': timestamp,
                'block_height': node_data['height'],
                'block_hash': node_data['hash'],
                'created_at': datetime.now().isoformat()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2)
            
            print(f"  ✅ {node_name.capitalize()}: блок {node_data['height']} сохранен")
    
    # ============================================================
    # 5. Бэкап HSM ключей (Shamir Secret Sharing)
    # ============================================================
    def backup_hsm_keys(self):
        """Бэкап HSM ключей с разделением секрета (Shamir Secret Sharing)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"\n🔐 Бэкап HSM ключей (Shamir Secret Sharing)...")
        
        hsm_data = self.db.get_data()['hsm_keys']
        
        # Симуляция разделения секрета на 5 частей
        for key_name, key_value in hsm_data.items():
            # Разделение на 5 частей (для демонстрации)
            parts = []
            key_b64 = key_value.encode().hex()
            part_size = len(key_b64) // 5
            
            for i in range(5):
                start = i * part_size
                end = start + part_size if i < 4 else len(key_b64)
                part_data = {
                    'share_id': i + 1,
                    'key_name': key_name,
                    'total_shares': 5,
                    'threshold': 3,
                    'data': key_b64[start:end]
                }
                parts.append(part_data)
                
                # Сохранение каждой части
                filename = f"{self.backup_dir}/hsm_{key_name}_share_{i+1}_{timestamp}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(part_data, f, indent=2)
            
            print(f"  ✅ Ключ '{key_name}' разделен на 5 частей (порог: 3)")
    
    # ============================================================
    # 6. Журнал бэкапов
    # ============================================================
    def _log_backup(self, backup_type, file_path, size_mb, checksum):
        """Запись в журнал бэкапов"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': backup_type,
            'file': file_path,
            'size_mb': round(size_mb, 2),
            'checksum': checksum
        }
        
        try:
            history = []
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            history.append(entry)
            
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"  ⚠️ Не удалось сохранить журнал: {e}")
    
    # ============================================================
    # 7. Показать историю
    # ============================================================
    def show_history(self):
        """Отображение истории бэкапов"""
        if not os.path.exists(self.log_file):
            print("\n📋 Журнал бэкапов пуст.")
            return
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            if not history:
                print("\n📋 Журнал бэкапов пуст.")
                return
            
            print("\n" + "=" * 80)
            print("📋 ИСТОРИЯ БЭКАПОВ")
            print("=" * 80)
            print(f"{'№':<4} {'Время':<25} {'Тип':<12} {'Размер':<12} {'Контрольная сумма':<30}")
            print("-" * 80)
            
            for i, entry in enumerate(history[-20:], 1):
                time_str = entry.get('timestamp', '')[:19]
                checksum = entry.get('checksum', '')[:16] + '...' if entry.get('checksum') else 'N/A'
                print(f"{i:<4} {time_str:<25} {entry.get('type', 'N/A'):<12} "
                      f"{entry.get('size_mb', 0):<12.2f} {checksum:<30}")
            print("=" * 80)
            
        except Exception as e:
            print(f"❌ Ошибка чтения журнала: {e}")
    
    # ============================================================
    # 8. Проверка целостности
    # ============================================================
    def verify_backups(self):
        """Проверка целостности бэкапов"""
        if not os.path.exists(self.log_file):
            print("\n📋 Нет бэкапов для проверки.")
            return
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            if not history:
                print("\n📋 Нет бэкапов для проверки.")
                return
            
            print("\n" + "=" * 70)
            print("🔍 ПРОВЕРКА ЦЕЛОСТНОСТИ БЭКАПОВ")
            print("=" * 70)
            
            ok_count = 0
            fail_count = 0
            
            for entry in history[-10:]:
                file_path = entry.get('file')
                stored_checksum = entry.get('checksum')
                
                if not os.path.exists(file_path):
                    print(f"  ❌ Файл отсутствует: {os.path.basename(file_path)}")
                    fail_count += 1
                    continue
                
                if not stored_checksum:
                    print(f"  ⚠️ Нет контрольной суммы: {os.path.basename(file_path)}")
                    continue
                
                current_checksum = self.calculate_checksum(file_path)
                if current_checksum == stored_checksum:
                    print(f"  ✅ {os.path.basename(file_path)} - ЦЕЛОСТЕН")
                    ok_count += 1
                else:
                    print(f"  ❌ {os.path.basename(file_path)} - ПОВРЕЖДЕН!")
                    fail_count += 1
            
            print("-" * 70)
            print(f"  ✅ Целостных: {ok_count} | ❌ Поврежденных: {fail_count}")
            print("=" * 70)
            
        except Exception as e:
            print(f"❌ Ошибка проверки: {e}")
    
    # ============================================================
    # 9. Очистка старых бэкапов
    # ============================================================
    def cleanup_old_backups(self):
        """Очистка бэкапов старше retention_days"""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        count = 0
        
        print(f"\n🧹 Очистка бэкапов старше {self.retention_days} дней...")
        
        for root, dirs, files in os.walk(self.backup_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if mtime < cutoff:
                        os.remove(file_path)
                        count += 1
                        print(f"  🗑️ Удален: {file}")
                except Exception as e:
                    print(f"  ⚠️ Не удалось удалить {file}: {e}")
        
        print(f"  ✅ Удалено {count} файлов")
    
    # ============================================================
    # 10. Восстановление (симуляция)
    # ============================================================
    def simulate_restore(self, backup_file=None):
        """Симуляция восстановления из бэкапа"""
        if backup_file is None:
            # Найти последний полный бэкап
            full_backups = [f for f in os.listdir(self.full_dir) if f.startswith('full_backup_') and f.endswith('.json.gz')]
            if not full_backups:
                print("\n❌ Нет полных бэкапов для восстановления.")
                return
            
            backup_file = os.path.join(self.full_dir, sorted(full_backups)[-1])
        
        print(f"\n🔄 Восстановление из бэкапа: {os.path.basename(backup_file)}")
        print("  ⏳ Распаковка...")
        
        try:
            # Распаковка
            with gzip.open(backup_file, 'rb') as f_in:
                data = json.loads(f_in.read().decode('utf-8'))
            
            print(f"  ✅ Данные восстановлены:")
            print(f"     👤 Пользователей: {len(data.get('data', {}).get('users', []))}")
            print(f"     📝 Ордеров: {len(data.get('data', {}).get('orders', []))}")
            print(f"     💰 Балансов: {len(data.get('data', {}).get('users', []))}")
            print("  🕐 Восстановление завершено!")
            print("  ℹ️ Это симуляция - данные не были перезаписаны")
            
        except Exception as e:
            print(f"  ❌ Ошибка восстановления: {e}")
    
    # ============================================================
    # 11. Отчет о RPO/RTO
    # ============================================================
    def show_rpo_rto_report(self):
        """Отчет о достижении RPO и RTO"""
        print("\n" + "=" * 70)
        print("📊 ОТЧЕТ О ДОСТИЖЕНИИ RPO/RTO")
        print("=" * 70)
        
        # Проверка наличия бэкапов
        wal_files = [f for f in os.listdir(self.wal_dir) if f.endswith('.json.gz')]
        full_files = [f for f in os.listdir(self.full_dir) if f.endswith('.json.gz')]
        
        # RPO - Recovery Point Objective
        print("\n🎯 RPO (Recovery Point Objective) ≤ 15 минут")
        print("-" * 40)
        
        if wal_files:
            latest_wal = max(wal_files, key=lambda f: os.path.getmtime(os.path.join(self.wal_dir, f)))
            wal_time = datetime.fromtimestamp(os.path.getmtime(os.path.join(self.wal_dir, latest_wal)))
            now = datetime.now()
            age = (now - wal_time).total_seconds() / 60
            
            if age <= 15:
                print(f"  ✅ Достигнут: {age:.1f} минут (цель: ≤ 15 мин)")
            else:
                print(f"  ⚠️ Превышен: {age:.1f} минут (цель: ≤ 15 мин)")
        else:
            print("  ⚠️ Нет WAL-бэкапов")
        
        # RTO - Recovery Time Objective
        print("\n🎯 RTO (Recovery Time Objective) ≤ 4 часа")
        print("-" * 40)
        
        estimated_restore_time = 15  # минут (симуляция)
        if estimated_restore_time <= 240:
            print(f"  ✅ Достигнут: {estimated_restore_time} минут (цель: ≤ 240 мин)")
        else:
            print(f"  ⚠️ Превышен: {estimated_restore_time} минут (цель: ≤ 240 мин)")
        
        # Статистика
        print("\n📈 СТАТИСТИКА")
        print("-" * 40)
        print(f"  Полных бэкапов: {len(full_files)}")
        print(f"  WAL-бэкапов: {len(wal_files)}")
        print(f"  Общий размер бэкапов: {self._get_total_backup_size():.2f} МБ")
        print("=" * 70)
    
    def _get_total_backup_size(self):
        """Общий размер всех бэкапов"""
        total = 0
        for root, dirs, files in os.walk(self.backup_dir):
            for file in files:
                total += os.path.getsize(os.path.join(root, file))
        return total / (1024 * 1024)

# ============================================================
# 12. Главное меню
# ============================================================
def main():
    backup_system = CoinGuardBackupSystem()
    
    while True:
        print("\n" + "=" * 50)
        print("   ГЛАВНОЕ МЕНЮ")
        print("=" * 50)
        print("1. 📦 Создать полный бэкап (Full)")
        print("2. 📝 Создать WAL-бэкап (Incremental)")
        print("3. 🔄 Создать все бэкапы")
        print("4. ⛓️ Бэкап блокчейн-узлов")
        print("5. 🔐 Бэкап HSM ключей")
        print("6. 📋 Показать историю")
        print("7. 🔍 Проверить целостность")
        print("8. 🧹 Очистить старые бэкапы")
        print("9. 🔄 Симуляция восстановления")
        print("10. 📊 Отчет RPO/RTO")
        print("11. 🚪 Выход")
        print("=" * 50)
        
        choice = input("Выберите действие (1-11): ").strip()
        
        if choice == '1':
            backup_system.create_full_backup()
        elif choice == '2':
            backup_system.create_wal_backup()
        elif choice == '3':
            backup_system.create_full_backup()
            backup_system.create_wal_backup()
        elif choice == '4':
            backup_system.backup_blockchain_nodes()
        elif choice == '5':
            backup_system.backup_hsm_keys()
        elif choice == '6':
            backup_system.show_history()
        elif choice == '7':
            backup_system.verify_backups()
        elif choice == '8':
            backup_system.cleanup_old_backups()
        elif choice == '9':
            backup_system.simulate_restore()
        elif choice == '10':
            backup_system.show_rpo_rto_report()
        elif choice == '11':
            print("\n👋 До свидания!")
            break
        else:
            print("\n❌ Неверный выбор. Введите число от 1 до 11.")
        
        input("\nНажмите Enter для продолжения...")

# ============================================================
# Точка входа
# ============================================================
if __name__ == "__main__":
    main()