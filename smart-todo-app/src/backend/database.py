import sqlite3
import os

# Путь к базе данных (в корне проекта)
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'smart_todo.db')

def init_db():
    """Инициализация базы данных: создание таблиц и заполнение тестовыми данными."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Создание таблицы категорий
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT DEFAULT '#CCCCCC'
        )
    ''')

    # Создание таблицы задач
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            priority TEXT CHECK(priority IN ('низкий', 'средний', 'высокий')) NOT NULL DEFAULT 'средний',
            category_id INTEGER,
            deadline DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_completed BOOLEAN DEFAULT 0,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        )
    ''')

    # Создание индексов
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status_deadline ON tasks (is_completed, deadline)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks (priority)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_category_id ON tasks (category_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON tasks (deadline)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_title ON tasks (title)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks (created_at)')

    # Заполнение тестовыми данными, если таблицы пусты
    if not cursor.execute("SELECT 1 FROM categories LIMIT 1").fetchone():
        insert_test_data(cursor)

    conn.commit()
    conn.close()
    print(f"✅ База данных инициализирована: {DATABASE_PATH}")


def insert_test_data(cursor):
    """Заполняет базу данных тестовыми категориями и задачами."""
    # Категории
    categories = [
        ('Работа', '#FF5733'),
        ('Личное', '#33FF57'),
        ('Учеба', '#3357FF')
    ]
    cursor.executemany("INSERT INTO categories (name, color) VALUES (?, ?)", categories)

    # Получаем ID категорий для связи с задачами
    cursor.execute("SELECT id, name FROM categories")
    category_map = {name: id for id, name in cursor.fetchall()}

    # Задачи
    tasks = [
        ("Подготовить презентацию", "Для встречи с клиентом", "высокий", category_map['Работа'], "2025-12-10 18:00:00", False),
        ("Позвонить маме", "Обсудить планы на выходные", "средний", category_map['Личное'], "2025-12-08 20:00:00", False),
        ("Прочитать главу 5", "По курсу Python", "высокий", category_map['Учеба'], "2025-12-12 23:59:59", False),
        ("Купить продукты", "Молоко, хлеб, яйца", "низкий", category_map['Личное'], None, False),
        ("Отправить отчёт", "За прошлый месяц", "высокий", category_map['Работа'], "2025-12-07 10:00:00", True),  # выполненная
    ]

    cursor.executemany("""
        INSERT INTO tasks (title, description, priority, category_id, deadline, is_completed)
        VALUES (?, ?, ?, ?, ?, ?)
    """, tasks)

    print("📊 Тестовые данные добавлены.")


if __name__ == "__main__":
    # Для тестирования: можно запустить этот файл напрямую
    init_db()