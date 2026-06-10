import os
import shutil

# Создаём правильную структуру
os.makedirs("templates/admin", exist_ok=True)
os.makedirs("templates/worker", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Содержимое файлов (скопируйте из ваших существующих файлов)
files = {
    "templates/base.html": '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Интернет-магазин{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
</body>
</html>''',

    "templates/login.html": '''{% extends "base.html" %}

{% block title %}Вход в систему{% endblock %}

{% block content %}
<div class="login-form">
    <h2>🔐 Авторизация</h2>
    <form method="POST">
        <div class="form-group">
            <label>Логин:</label>
            <input type="text" name="login" required placeholder="Введите логин">
        </div>
        <div class="form-group">
            <label>Пароль:</label>
            <input type="password" name="password" required placeholder="Введите пароль">
        </div>
        <div class="form-group">
            <label>🤖 Капча: сколько будет {{ num1 }} + {{ num2 }} ?</label>
            <input type="text" name="captcha" required placeholder="Введите число">
        </div>
        <button type="submit">Войти</button>
    </form>
    <p style="text-align: center; margin-top: 15px; font-size: 12px; color: gray;">
        Тестовые данные: admin/admin123, worker/worker123
    </p>
</div>
{% endblock %}''',

    "templates/admin/dashboard.html": '''{% extends "base.html" %}

{% block title %}Панель администратора{% endblock %}

{% block content %}
<h1>👑 Панель администратора</h1>
<p>Добро пожаловать, <strong>{{ session.login }}</strong>!</p>

<div class="menu">
    <ul>
        <li><a href="{{ url_for('admin_users') }}">📋 Управление пользователями</a></li>
        <li><a href="#">📦 Управление товарами</a></li>
        <li><a href="#">📊 Отчёты и статистика</a></li>
        <li><a href="{{ url_for('logout') }}">🚪 Выход</a></li>
    </ul>
</div>
{% endblock %}''',

    "templates/admin/users.html": '''{% extends "base.html" %}

{% block title %}Управление пользователями{% endblock %}

{% block content %}
<h1>📋 Управление пользователями</h1>
<p>
    <a href="{{ url_for('add_user') }}" class="btn">➕ Добавить пользователя</a>
    <a href="{{ url_for('admin_dashboard') }}" class="btn">← Назад</a>
</p>

<table>
    <thead>
        <tr>
            <th>ID</th>
            <th>Логин</th>
            <th>Роль</th>
            <th>Дата создания</th>
            <th>Действия</th>
        </tr>
    </thead>
    <tbody>
        {% for user in users %}
        <tr>
            <td>{{ user.id_пользователя }}</td>
            <td>{{ user.логин }}</td>
            <td>{% if user.роль == 'admin' %}👑 Админ{% else %}👷 Работник{% endif %}</td>
            <td>{{ user.created_at }}</td>
            <td>
                <a href="{{ url_for('delete_user', user_id=user.id_пользователя) }}"
                   onclick="return confirm('Удалить пользователя {{ user.логин }}?')"
                   style="color: red;">🗑️ Удалить</a>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}''',

    "templates/admin/add_user.html": '''{% extends "base.html" %}

{% block title %}Добавление пользователя{% endblock %}

{% block content %}
<h1>➕ Добавление пользователя</h1>
<a href="{{ url_for('admin_users') }}">← Назад</a>

<form method="POST" style="margin-top: 20px; max-width: 400px;">
    <div class="form-group">
        <label>Логин:</label>
        <input type="text" name="login" required placeholder="Введите логин">
    </div>
    <div class="form-group">
        <label>Пароль:</label>
        <input type="password" name="password" required placeholder="Введите пароль">
    </div>
    <div class="form-group">
        <label>Роль:</label>
        <select name="role">
            <option value="worker">👷 Работник</option>
            <option value="admin">👑 Администратор</option>
        </select>
    </div>
    <button type="submit">✅ Создать пользователя</button>
</form>
{% endblock %}''',

    "templates/worker/dashboard.html": '''{% extends "base.html" %}

{% block title %}Панель работника{% endblock %}

{% block content %}
<h1>👷 Панель работника</h1>
<p>Добро пожаловать, <strong>{{ session.login }}</strong>!</p>
<p>Ваша роль: {% if session.role == 'admin' %}Администратор{% else %}Работник{% endif %}</p>

<div class="menu">
    <ul>
        <li><a href="#">🍕 Просмотр заказов</a></li>
        <li><a href="#">✏️ Изменение статуса заказа</a></li>
        <li><a href="#">📋 Просмотр товаров</a></li>
        <li><a href="{{ url_for('logout') }}">🚪 Выход</a></li>
    </ul>
</div>
{% endblock %}''',

    "static/style.css": '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    padding: 20px;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    background: white;
    border-radius: 15px;
    padding: 30px;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}

.login-form {
    max-width: 400px;
    margin: 50px auto;
    padding: 30px;
    background: white;
    border-radius: 15px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.1);
}

.form-group {
    margin-bottom: 20px;
}

.form-group label {
    display: block;
    margin-bottom: 8px;
    font-weight: 600;
    color: #555;
}

input, select, button {
    width: 100%;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 14px;
}

button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    cursor: pointer;
    font-weight: bold;
}

.alert {
    padding: 12px 20px;
    margin-bottom: 20px;
    border-radius: 8px;
}

.alert-success { background-color: #d4edda; color: #155724; }
.alert-danger { background-color: #f8d7da; color: #721c24; }
.alert-warning { background-color: #fff3cd; color: #856404; }

.menu ul {
    list-style: none;
}

.menu li {
    margin: 15px 0;
}

.menu a {
    display: inline-block;
    padding: 12px 25px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    text-decoration: none;
    border-radius: 8px;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
}

th, td {
    padding: 12px;
    text-align: left;
    border-bottom: 1px solid #ddd;
}

th {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

.btn {
    display: inline-block;
    padding: 10px 20px;
    background: #667eea;
    color: white;
    text-decoration: none;
    border-radius: 8px;
    margin-right: 10px;
}

h1 {
    color: #333;
    margin-bottom: 20px;
}'''
}

# Записываем файлы
for filepath, content in files.items():
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Создан: {filepath}")

print("\n🎉 Все файлы созданы в правильной структуре!")