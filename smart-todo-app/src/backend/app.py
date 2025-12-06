cat > src/backend/app.py <<'EOF'
from flask import Flask, request, jsonify, render_template, redirect
import sqlite3
import os
from datetime import datetime

# Путь к корню проекта
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATABASE_PATH = os.path.join(PROJECT_ROOT, 'smart_todo.db')

# Создаём Flask-приложение и явно указываем папку шаблонов
app = Flask(__name__, template_folder=os.path.join(PROJECT_ROOT, 'templates'))

# --- Вспомогательные функции ---

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            color TEXT DEFAULT '#CCCCCC'
        )
    ''')

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

    # Индексы
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status_deadline ON tasks (is_completed, deadline)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks (priority)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_category_id ON tasks (category_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON tasks (deadline)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_title ON tasks (title)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks (created_at)')

    # Тестовые данные (если пусто)
    if not cursor.execute("SELECT 1 FROM categories LIMIT 1").fetchone():
        cursor.executemany("INSERT INTO categories (name, color) VALUES (?, ?)",
                           [('Работа', '#FF5733'), ('Личное', '#33FF57'), ('Учеба', '#3357FF')])
        cursor.executemany("""
            INSERT INTO tasks (title, description, priority, category_id, deadline, is_completed)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            ("Подготовить презентацию", "Для встречи с клиентом", "высокий", 1, "2025-12-10 18:00:00", False),
            ("Позвонить маме", "Обсудить планы на выходные", "средний", 2, "2025-12-08 20:00:00", False),
            ("Прочитать главу 5", "По курсу Python", "высокий", 3, "2025-12-12 23:59:59", False),
            ("Купить продукты", "Молоко, хлеб, яйца", "низкий", 2, None, False),
            ("Отправить отчёт", "За прошлый месяц", "высокий", 1, "2025-12-07 10:00:00", True),
        ])

    conn.commit()
    conn.close()

# Инициализируем БД при запуске
init_db()

# --- API Endpoints ---

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.*, c.name AS category_name, c.color AS category_color
        FROM tasks t
        LEFT JOIN categories c ON t.category_id = c.id
        ORDER BY t.created_at DESC
    ''')
    tasks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(tasks)

@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.*, c.name AS category_name, c.color AS category_color
        FROM tasks t
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.id = ?
    ''', (task_id,))
    task = cursor.fetchone()
    conn.close()
    if task is None:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(dict(task))

@app.route('/api/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data or 'title' not in data:
        return jsonify({'error': 'Title is required'}), 400

    title = data['title']
    description = data.get('description', '')
    priority = data.get('priority', 'средний')
    category_id = data.get('category_id')
    deadline = data.get('deadline')
    is_completed = data.get('is_completed', False)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tasks (title, description, priority, category_id, deadline, is_completed)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (title, description, priority, category_id, deadline, is_completed))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        'id': task_id,
        'title': title,
        'description': description,
        'priority': priority,
        'category_id': category_id,
        'deadline': deadline,
        'is_completed': is_completed
    }), 201

# --- Web Endpoints ---

@app.route('/', methods=['GET'])
def index():
    conn = get_db_connection()
    cursor = conn.cursor()

    status = request.args.get('status', 'all')
    where_clause = {
        'active': 't.is_completed = 0',
        'completed': 't.is_completed = 1'
    }.get(status, '1=1')

    cursor.execute(f'''
        SELECT t.*, c.name AS category_name, c.color AS category_color
        FROM tasks t
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE {where_clause}
        ORDER BY 
            CASE t.priority WHEN 'высокий' THEN 1 WHEN 'средний' THEN 2 ELSE 3 END,
            t.deadline ASC NULLS LAST,
            t.created_at DESC
    ''')
    tasks = [dict(row) for row in cursor.fetchall()]

    cursor.execute('SELECT COUNT(*) FROM tasks')
    total = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM tasks WHERE is_completed = 1')
    completed = cursor.fetchone()[0]
    conn.close()

    stats = {'total': total, 'completed': completed, 'active': total - completed}
    return render_template('tasks_list.html', tasks=tasks, stats=stats, filter_status=status)

@app.route('/tasks', methods=['POST'])
def web_create_task():
    title = request.form.get('title', '').strip()
    if not title:
        return redirect('/')
    description = request.form.get('description', '').strip()
    priority = request.form.get('priority', 'средний')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tasks (title, description, priority, is_completed) VALUES (?, ?, ?, ?)',
                   (title, description, priority, False))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/tasks/<int:task_id>/toggle', methods=['POST'])
def toggle_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT is_completed FROM tasks WHERE id = ?', (task_id,))
    row = cursor.fetchone()
    if row:
        new_status = 1 - row[0]
        cursor.execute('UPDATE tasks SET is_completed = ? WHERE id = ?', (new_status, task_id))
        conn.commit()
    conn.close()
    return redirect(request.referrer or '/')

@app.route('/tasks/<int:task_id>/delete', methods=['POST'])
def delete_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    return redirect(request.referrer or '/')

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
EOF