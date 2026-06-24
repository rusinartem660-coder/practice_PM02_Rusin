"""
Выполнил: Русин Артём
Группа 24ИС
Дата: 2026-06-10
"""

import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error
import csv
from datetime import datetime


def connect_db():
    """Подключение к базе данных MySQL"""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="zxcpacan$1337",
            database="mydb"
        )
        return connection
    except Error as e:
        messagebox.showerror("Ошибка БД", f"Не удалось подключиться: {e}")
        return None


class DatabaseApp:
    """Главный класс приложения для работы с БД"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Управление интернет-магазином")
        self.root.geometry("1000x700")
        
        # Словарь с конфигурациями таблиц
        self.tables_config = {
            "Товары": {
                "columns": [
                    {"name": "id_товара", "label": "ID", "pk": True, "auto_increment": True},
                    {"name": "Название", "label": "Название", "required": True},
                    {"name": "цена", "label": "Цена", "required": True},
                    {"name": "остаток", "label": "Остаток", "required": True},
                    {"name": "описание", "label": "Описание", "required": False}
                ]
            },
            "Категории": {
                "columns": [
                    {"name": "idКатегории", "label": "ID", "pk": True, "auto_increment": True},
                    {"name": "название", "label": "Название категории", "required": True},
                    # Важно: имя колонки с пробелом нужно будет экранировать
                    {"name": "Родительская категория", "label": "Родительская категория", "required": False}
                ]
            },
            "Покупатели": {
                "columns": [
                    {"name": "id_Покупателя", "label": "ID", "pk": True, "auto_increment": True},
                    {"name": "логин", "label": "Логин", "required": True},
                    {"name": "email", "label": "Email", "required": True},
                    {"name": "телефон", "label": "Телефон", "required": False},
                    {"name": "адрес", "label": "Адрес", "required": False}
                ]
            },
            "Заказы": {
                "columns": [
                    {"name": "id_Заказы", "label": "ID заказа", "pk": True, "auto_increment": True},
                    {"name": "дата", "label": "Дата", "required": True},
                    {"name": "статус", "label": "Статус", "required": False},
                    {"name": "сумма", "label": "Сумма", "required": False},
                    {"name": "id_покупателя", "label": "ID покупателя", "required": True}
                ]
            },
            "Отзывы": {
                "columns": [
                    {"name": "id_отзыва", "label": "ID отзыва", "pk": True, "auto_increment": True},
                    {"name": "текст", "label": "Текст отзыва", "required": False},
                    {"name": "оценка", "label": "Оценка (1-5)", "required": False},
                    {"name": "дата", "label": "Дата", "required": False},
                    {"name": "id_товара", "label": "ID товара", "required": True},
                    {"name": "id_покупателя", "label": "ID покупателя", "required": True}
                ]
            }
        }
        
        self.current_table = tk.StringVar(value="Товары")
        self.current_config = None
        self.app_frame = None
        self.entries = {}
        self.tree = None
        self.search_entry = None
        
        self.create_menu()
        self.load_table()
    
    def create_menu(self):
        """Создание меню для выбора таблицы"""
        menu_frame = tk.Frame(self.root, bg="#f0f0f0", relief=tk.RAISED, bd=2)
        menu_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        tk.Label(menu_frame, text="Выберите таблицу:", bg="#f0f0f0", 
                font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=10)
        
        for table_name in self.tables_config.keys():
            btn = tk.Button(menu_frame, text=table_name, 
                          command=lambda t=table_name: self.switch_table(t),
                          width=15, bg="#4CAF50", fg="white")
            btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(menu_frame, text="Выход", command=self.root.quit,
                 width=10, bg="#f44336", fg="white").pack(side=tk.RIGHT, padx=10)
    
    def switch_table(self, table_name):
        """Переключение между таблицами"""
        self.current_table.set(table_name)
        self.load_table()
    
    def escape_column_name(self, col_name):
        """Экранирует имя колонки, если оно содержит пробелы или спецсимволы"""
        if ' ' in col_name or '-' in col_name or '(' in col_name:
            return f"`{col_name}`"
        return col_name
    
    def load_table(self):
        """Загрузка интерфейса для выбранной таблицы"""
        if self.app_frame:
            self.app_frame.destroy()
        
        self.app_frame = tk.Frame(self.root)
        self.app_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Заголовок
        tk.Label(self.app_frame, text=f"Управление таблицей: {self.current_table.get()}",
                font=("Arial", 16, "bold"), fg="#2196F3").pack(pady=10)
        
        # Загружаем конфигурацию
        self.current_config = self.tables_config[self.current_table.get()]
        
        # Создаем интерфейс
        self.create_input_fields()
        self.create_buttons()
        self.create_search_frame()
        self.create_treeview()
        
        # Загружаем данные
        self.refresh_table()
    
    def create_input_fields(self):
        """Создание полей ввода"""
        input_frame = tk.LabelFrame(self.app_frame, text="Ввод данных", 
                                    font=("Arial", 10, "bold"))
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.entries = {}
        row = 0
        col = 0
        
        for col_config in self.current_config["columns"]:
            # Пропускаем PK с auto_increment
            if col_config.get('pk') and col_config.get('auto_increment'):
                continue
            
            # Метка
            label_text = col_config['label']
            if col_config.get('required'):
                label_text += " *"
            
            label = tk.Label(input_frame, text=f"{label_text}:",
                            font=("Arial", 10))
            label.grid(row=row, column=col*2, padx=5, pady=5, sticky="e")
            
            # Поле ввода
            entry = tk.Entry(input_frame, width=25, font=("Arial", 10))
            entry.grid(row=row, column=col*2+1, padx=5, pady=5)
            self.entries[col_config['name']] = entry
            
            col += 1
            if col > 2:  # 3 колонки в ряду
                col = 0
                row += 1
        
        # Если нет полей (только PK), показываем сообщение
        if not self.entries:
            tk.Label(input_frame, text="Нет полей для ввода (авто-инкремент)", 
                    font=("Arial", 10), fg="gray").grid(row=0, column=0, padx=10, pady=10)
    
    def create_buttons(self):
        """Создание кнопок управления"""
        button_frame = tk.Frame(self.app_frame)
        button_frame.pack(pady=10)
        
        buttons = [
            ("➕ Добавить", self.add_record, "#4CAF50"),
            ("✏️ Обновить", self.update_record, "#FFC107"),
            ("🗑️ Удалить", self.delete_record, "#f44336"),
            ("🧹 Очистить", self.clear_entries, "#9E9E9E"),
            ("🔄 Обновить", self.refresh_table, "#2196F3"),
            ("📊 Статистика", self.show_stats, "#9C27B0"),
            ("📁 Экспорт CSV", self.export_to_csv, "#FF9800")
        ]
        
        for i, (text, command, color) in enumerate(buttons):
            btn = tk.Button(button_frame, text=text, command=command,
                           bg=color, fg="white", font=("Arial", 10, "bold"),
                           width=12, padx=5, pady=3)
            btn.grid(row=0, column=i, padx=5)
    
    def create_search_frame(self):
        """Создание строки поиска"""
        search_frame = tk.Frame(self.app_frame)
        search_frame.pack(pady=5)
        
        tk.Label(search_frame, text="🔍 Поиск:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame, width=40, font=("Arial", 10))
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<Return>', lambda e: self.search())
        
        tk.Button(search_frame, text="Найти", command=self.search,
                 bg="#2196F3", fg="white", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Сброс", command=self.refresh_table,
                 bg="#9E9E9E", fg="white", font=("Arial", 10)).pack(side=tk.LEFT)
    
    def create_treeview(self):
        """Создание таблицы Treeview"""
        tree_frame = tk.Frame(self.app_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Скроллбары
        scroll_y = tk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scroll_x = tk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Определяем колонки
        columns_display = [col['name'] for col in self.current_config["columns"]]
        
        self.tree = ttk.Treeview(tree_frame, columns=columns_display, show="headings",
                                yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        
        # Настраиваем заголовки и ширину колонок
        for col in self.current_config["columns"]:
            self.tree.heading(col['name'], text=col['label'])
            # Устанавливаем ширину в зависимости от названия поля
            if col['name'] in ['описание', 'текст', 'адрес']:
                width = 250
            elif col['name'] in ['название', 'Родительская категория']:
                width = 180
            else:
                width = 100
            self.tree.column(col['name'], width=width, anchor="center", minwidth=80)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Привязываем событие выбора строки
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
    
    def refresh_table(self):
        """Обновление данных в таблице"""
        # Очищаем текущие данные
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        conn = connect_db()
        if not conn:
            return
        
        cursor = conn.cursor()
        table_name = self.current_table.get()
        columns_names = [self.escape_column_name(col['name']) for col in self.current_config["columns"]]
        query = f"SELECT {', '.join(columns_names)} FROM {table_name}"
        
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            
            if not rows:
                print(f"В таблице {table_name} нет данных")
            
            for row in rows:
                # Преобразуем None в пустую строку для отображения
                row_display = [str(val) if val is not None else "" for val in row]
                self.tree.insert("", tk.END, values=row_display)
        except Error as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def on_select(self, event):
        """Заполнение полей при выборе строки"""
        selected = self.tree.selection()
        if not selected:
            return
        
        values = self.tree.item(selected[0])['values']
        
        # Заполняем поля ввода
        for i, col in enumerate(self.current_config["columns"]):
            col_name = col['name']
            if col_name in self.entries and i < len(values):
                self.entries[col_name].delete(0, tk.END)
                if values[i] and str(values[i]) != '':
                    self.entries[col_name].insert(0, values[i])
    
    def get_pk_name(self):
        """Возвращает имя первичного ключа"""
        for col in self.current_config["columns"]:
            if col.get('pk'):
                return col['name']
        return None
    
    def get_pk_value_from_selection(self):
        """Получает значение PK из выбранной строки"""
        selected = self.tree.selection()
        if not selected:
            return None
        
        values = self.tree.item(selected[0])['values']
        pk_name = self.get_pk_name()
        if not pk_name:
            return None
        
        # Находим индекс колонки PK
        for i, col in enumerate(self.current_config["columns"]):
            if col['name'] == pk_name:
                if i < len(values):
                    return values[i]
        return None
    
    def add_record(self):
        """Добавление новой записи"""
        # Собираем значения
        values = {}
        for col_name, entry in self.entries.items():
            value = entry.get().strip()
            if value:
                # Специальная обработка для числовых полей
                if col_name in ['цена', 'сумма']:
                    try:
                        value = float(value)
                    except ValueError:
                        messagebox.showerror("Ошибка", f"Поле '{col_name}' должно быть числом")
                        return
                elif col_name in ['остаток', 'id_покупателя', 'id_товара', 'id_Заказы', 'оценка']:
                    try:
                        value = int(value)
                    except ValueError:
                        messagebox.showerror("Ошибка", f"Поле '{col_name}' должно быть целым числом")
                        return
                elif col_name == 'дата' and value:
                    try:
                        datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        try:
                            datetime.strptime(value, '%Y-%m-%d')
                        except ValueError:
                            messagebox.showerror("Ошибка", "Дата должна быть в формате ГГГГ-ММ-ДД или ГГГГ-ММ-ДД ЧЧ:ММ:СС")
                            return
            
            values[col_name] = value if value else None
        
        # Проверка обязательных полей
        for col in self.current_config["columns"]:
            col_name = col['name']
            if col.get('required') and col_name in self.entries and not values.get(col_name):
                messagebox.showwarning("Ошибка", f"Поле '{col['label']}' обязательно для заполнения")
                return
        
        conn = connect_db()
        if not conn:
            return
        
        cursor = conn.cursor()
        table_name = self.current_table.get()
        columns_names = [self.escape_column_name(col_name) for col_name in values.keys()]
        
        if not columns_names:
            messagebox.showwarning("Ошибка", "Нет полей для добавления")
            return
            
        placeholders = ", ".join(["%s"] * len(columns_names))
        query = f"INSERT INTO {table_name} ({', '.join(columns_names)}) VALUES ({placeholders})"
        
        try:
            cursor.execute(query, list(values.values()))
            conn.commit()
            messagebox.showinfo("Успех", "Запись добавлена")
            self.clear_entries()
            self.refresh_table()
        except Error as e:
            messagebox.showerror("Ошибка БД", str(e))
        finally:
            cursor.close()
            conn.close()
    
    def update_record(self):
        """Обновление выбранной записи"""
        pk_value = self.get_pk_value_from_selection()
        if not pk_value:
            messagebox.showwarning("Предупреждение", "Выберите запись для обновления")
            return
        
        # Собираем новые значения
        new_values = {}
        for col_name, entry in self.entries.items():
            value = entry.get().strip()
            new_values[col_name] = value if value else None
        
        if not new_values:
            messagebox.showwarning("Предупреждение", "Нет данных для обновления")
            return
        
        conn = connect_db()
        if not conn:
            return
        
        cursor = conn.cursor()
        pk_name = self.get_pk_name()
        escaped_pk_name = self.escape_column_name(pk_name)
        table_name = self.current_table.get()
        
        set_clause = ", ".join([f"{self.escape_column_name(col)} = %s" for col in new_values.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {escaped_pk_name} = %s"
        
        try:
            params = list(new_values.values()) + [pk_value]
            cursor.execute(query, params)
            conn.commit()
            messagebox.showinfo("Успех", "Запись обновлена")
            self.refresh_table()
        except Error as e:
            messagebox.showerror("Ошибка БД", str(e))
        finally:
            cursor.close()
            conn.close()
    
    def delete_record(self):
        """Удаление выбранной записи"""
        pk_value = self.get_pk_value_from_selection()
        if not pk_value:
            messagebox.showwarning("Предупреждение", "Выберите запись для удаления")
            return
        
        if not messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить запись?"):
            return
        
        conn = connect_db()
        if not conn:
            return
        
        cursor = conn.cursor()
        pk_name = self.get_pk_name()
        escaped_pk_name = self.escape_column_name(pk_name)
        table_name = self.current_table.get()
        query = f"DELETE FROM {table_name} WHERE {escaped_pk_name} = %s"
        
        try:
            cursor.execute(query, (pk_value,))
            conn.commit()
            messagebox.showinfo("Успех", "Запись удалена")
            self.clear_entries()
            self.refresh_table()
        except Error as e:
            messagebox.showerror("Ошибка БД", str(e))
        finally:
            cursor.close()
            conn.close()
    
    def clear_entries(self):
        """Очистка полей ввода"""
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        
        # Снимаем выделение в таблице
        selection = self.tree.selection()
        if selection:
            self.tree.selection_remove(selection[0])
    
    def search(self):
        """Поиск по таблице"""
        keyword = self.search_entry.get().strip()
        if not keyword:
            self.refresh_table()
            return
        
        conn = connect_db()
        if not conn:
            return
        
        cursor = conn.cursor()
        table_name = self.current_table.get()
        columns_names = [self.escape_column_name(col['name']) for col in self.current_config["columns"]]
        
        # Ищем по всем текстовым полям
        text_columns = [col['name'] for col in self.current_config["columns"] 
                       if not col.get('pk') and col['name'] not in ['цена', 'сумма', 'остаток', 'оценка']]
        
        if not text_columns:
            self.refresh_table()
            return
        
        escaped_text_columns = [self.escape_column_name(col) for col in text_columns]
        conditions = " OR ".join([f"{col} LIKE %s" for col in escaped_text_columns])
        query = f"SELECT {', '.join(columns_names)} FROM {table_name} WHERE {conditions}"
        
        try:
            cursor.execute(query, tuple([f"%{keyword}%"] * len(text_columns)))
            rows = cursor.fetchall()
            
            # Очищаем таблицу
            for row in self.tree.get_children():
                self.tree.delete(row)
            
            # Заполняем результатами
            for row in rows:
                row_display = [str(val) if val is not None else "" for val in row]
                self.tree.insert("", tk.END, values=row_display)
            
            messagebox.showinfo("Результаты", f"Найдено {len(rows)} записей")
        except Error as e:
            messagebox.showerror("Ошибка", str(e))
        finally:
            cursor.close()
            conn.close()
    
    def export_to_csv(self):
        """Экспорт данных в CSV"""
        filename = f"{self.current_table.get()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        conn = connect_db()
        if not conn:
            return
        
        cursor = conn.cursor()
        table_name = self.current_table.get()
        columns_names = [self.escape_column_name(col['name']) for col in self.current_config["columns"]]
        query = f"SELECT {', '.join(columns_names)} FROM {table_name}"
        
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            
            with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                # Заголовки на русском
                writer.writerow([col['label'] for col in self.current_config["columns"]])
                # Данные
                writer.writerows(rows)
            
            messagebox.showinfo("Успех", f"Данные экспортированы в файл: {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
        finally:
            cursor.close()
            conn.close()
    
    def show_stats(self):
        """Показ статистики по таблице"""
        conn = connect_db()
        if not conn:
            return
        
        cursor = conn.cursor()
        table_name = self.current_table.get()
        
        try:
            # Получаем количество записей
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            # Дополнительная статистика для разных таблиц
            stats_text = f"📊 Статистика таблицы '{table_name}':\n\n"
            stats_text += f"📝 Всего записей: {count}\n"
            
            if table_name == "Товары":
                cursor.execute("SELECT SUM(остаток), AVG(цена), MIN(цена), MAX(цена) FROM Товары")
                result = cursor.fetchone()
                if result and result[0] is not None:
                    total, avg, min_price, max_price = result
                    stats_text += f"💰 Общая стоимость запасов: {total}\n"
                    stats_text += f"📈 Средняя цена: {avg:.2f}\n" if avg else "📈 Средняя цена: 0\n"
                    stats_text += f"📉 Минимальная цена: {min_price or 0}\n"
                    stats_text += f"📊 Максимальная цена: {max_price or 0}\n"
                else:
                    stats_text += "💰 Нет данных о товарах\n"
            
            elif table_name == "Заказы":
                cursor.execute("SELECT SUM(сумма), AVG(сумма) FROM Заказы WHERE статус = 'завершен'")
                result = cursor.fetchone()
                if result:
                    total_sum, avg_sum = result
                    stats_text += f"💰 Общая сумма завершенных заказов: {total_sum or 0}\n"
                    stats_text += f"📈 Средняя сумма заказа: {avg_sum or 0:.2f}\n"
                else:
                    stats_text += "💰 Нет завершенных заказов\n"
            
            messagebox.showinfo("Статистика", stats_text)
        except Error as e:
            messagebox.showerror("Ошибка", str(e))
        finally:
            cursor.close()
            conn.close()


def main():
    """Запуск приложения"""
    root = tk.Tk()
    app = DatabaseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()