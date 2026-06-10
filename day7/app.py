"""
ДЕНЬ 7. Доработка приложения: авторизация, роли пользователей, капча
Выполнил: Русин Артём
Группа: 24ИС
Дата: 2026-06-10
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import bcrypt
from functools import wraps
import random

app = Flask(__name__)
app.secret_key = 'supersecretkey_replace_in_production_2026'

# Настройки MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'zxcpacan$1337'  # Ваш пароль
app.config['MYSQL_DB'] = 'mydb'                  # Ваша БД
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


# ========== ДЕКОРАТОРЫ ДЛЯ ПРОВЕРКИ ДОСТУПА ==========

def login_required(f):
    """Требует авторизации пользователя"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Требует роли администратора"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Доступ запрещён. Требуется роль администратора.', 'danger')
            return redirect(url_for('worker_dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# ========== СТРАНИЦЫ ==========

@app.route('/')
def index():
    """Главная страница - перенаправляет на вход или дашборд"""
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('worker_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа с капчей"""
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        captcha_user = request.form['captcha']

        # Проверка капчи
        if int(captcha_user) != session.get('captcha_result'):
            flash('Неверно введена капча', 'danger')
            return redirect(url_for('login'))

        # Поиск пользователя в БД
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM Пользователи WHERE логин = %s", (login,))
        user = cur.fetchone()
        cur.close()

        if user:
            stored_hash = user['пароль_hash']
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                # Успешный вход
                session['user_id'] = user['id_пользователя']
                session['login'] = user['логин']
                session['role'] = user['роль']
                flash(f'Добро пожаловать, {user["логин"]}!', 'success')

                if user['роль'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('worker_dashboard'))
            else:
                flash('Неверный логин или пароль', 'danger')
        else:
            flash('Неверный логин или пароль', 'danger')

    # Генерация капчи (простое сложение)
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    session['captcha_result'] = num1 + num2

    return render_template('login.html', num1=num1, num2=num2)


@app.route('/logout')
def logout():
    """Выход из системы"""
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Панель администратора"""
    return render_template('admin/dashboard.html')


@app.route('/worker/dashboard')
@login_required
def worker_dashboard():
    """Панель работника"""
    return render_template('worker/dashboard.html')


@app.route('/admin/users')
@admin_required
def admin_users():
    """Управление пользователями (только админ)"""
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_пользователя, логин, роль, created_at FROM Пользователи")
    users = cur.fetchall()
    cur.close()
    return render_template('admin/users.html', users=users)


@app.route('/admin/add_user', methods=['GET', 'POST'])
@admin_required
def add_user():
    """Добавление нового пользователя"""
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        role = request.form['role']

        # Хеширование пароля
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cur = mysql.connection.cursor()
        try:
            cur.execute(
                "INSERT INTO Пользователи (логин, пароль_hash, роль) VALUES (%s, %s, %s)",
                (login, hashed.decode('utf-8'), role)
            )
            mysql.connection.commit()
            flash(f'Пользователь {login} успешно создан', 'success')
        except Exception as e:
            flash(f'Ошибка: пользователь с таким логином уже существует', 'danger')
        finally:
            cur.close()
        return redirect(url_for('admin_users'))

    return render_template('admin/add_user.html')


@app.route('/admin/delete_user/<int:user_id>')
@admin_required
def delete_user(user_id):
    """Удаление пользователя"""
    if user_id == session['user_id']:
        flash('Нельзя удалить самого себя', 'danger')
        return redirect(url_for('admin_users'))

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM Пользователи WHERE id_пользователя = %s", (user_id,))
    mysql.connection.commit()
    cur.close()
    flash('Пользователь удалён', 'success')
    return redirect(url_for('admin_users'))


if __name__ == '__main__':
    app.run(debug=True)