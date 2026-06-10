"""
Скрипт для создания тестовых пользователей с хешированными паролями
"""
import bcrypt
import mysql.connector

# Подключение к БД
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="zxcpacan$1337",
    database="mydb"
)
cursor = conn.cursor()

# Создаём таблицу пользователей, если её нет
cursor.execute("""
CREATE TABLE IF NOT EXISTS Пользователи (
    id_пользователя INT PRIMARY KEY AUTO_INCREMENT,
    логин VARCHAR(50) UNIQUE NOT NULL,
    пароль_hash VARCHAR(255) NOT NULL,
    роль ENUM('admin', 'worker') DEFAULT 'worker',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Данные для тестовых пользователей
users = [
    ('admin', 'admin123', 'admin'),
    ('worker', 'worker123', 'worker')
]

for login, password, role in users:
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        cursor.execute(
            "INSERT INTO Пользователи (логин, пароль_hash, роль) VALUES (%s, %s, %s)",
            (login, hashed.decode('utf-8'), role)
        )
        print(f"✅ Пользователь '{login}' создан (пароль: {password})")
    except mysql.connector.IntegrityError:
        print(f"⚠️ Пользователь '{login}' уже существует")

conn.commit()
cursor.close()
conn.close()

print("\n📝 Тестовые учётные данные:")
print("   Админ:    admin / admin123")
print("   Работник: worker / worker123")