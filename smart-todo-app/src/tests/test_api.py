import os
import tempfile
import pytest
from src.backend.app import app, init_db, get_db_connection
from src.backend.database import DATABASE_PATH

# Путь к тестовой базе данных (временная)
TEST_DB_PATH = None


@pytest.fixture(scope="module")
def test_client():
    """Создаёт клиент Flask для тестирования."""
    # Сохраняем оригинальный путь к БД
    original_db_path = app.config.get('DATABASE_PATH', DATABASE_PATH)

    # Создаём временную БД для тестов
    with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
        global TEST_DB_PATH
        TEST_DB_PATH = tmpfile.name

    # Переключаем Flask на тестовую БД
    app.config['DATABASE_PATH'] = TEST_DB_PATH
    app.config['TESTING'] = True

    # Инициализируем тестовую БД
    init_db()

    # Создаём клиент
    with app.test_client() as client:
        yield client

    # После всех тестов удаляем временную БД
    if os.path.exists(TEST_DB_PATH):
        os.unlink(TEST_DB_PATH)

    # Возвращаем обратно путь к основной БД
    app.config['DATABASE_PATH'] = original_db_path


def test_get_tasks_empty(test_client):
    """Тест: GET /api/tasks — возвращает пустой список, если задач нет."""
    response = test_client.get('/api/tasks')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_create_task(test_client):
    """Тест: POST /api/tasks — создаёт новую задачу."""
    new_task = {
        "title": "Тестовая задача",
        "description": "Описание тестовой задачи",
        "priority": "средний",
        "category_id": 1,
        "deadline": "2025-12-31T23:59:59",
        "is_completed": False
    }

    response = test_client.post('/api/tasks', json=new_task)
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data
    assert data['title'] == new_task['title']
    assert data['priority'] == new_task['priority']


def test_get_task_by_id(test_client):
    """Тест: GET /api/tasks/<id> — возвращает задачу по ID."""
    # Сначала создадим задачу
    new_task = {
        "title": "Задача для теста получения",
        "priority": "высокий"
    }
    create_response = test_client.post('/api/tasks', json=new_task)
    task_id = create_response.get_json()['id']

    # Получаем задачу
    response = test_client.get(f'/api/tasks/{task_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == task_id
    assert data['title'] == new_task['title']


def test_get_task_not_found(test_client):
    """Тест: GET /api/tasks/<id> — возвращает 404, если задача не найдена."""
    response = test_client.get('/api/tasks/99999')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert data['error'] == 'Task not found'


def test_create_task_missing_title(test_client):
    """Тест: POST /api/tasks — возвращает 400, если title отсутствует."""
    response = test_client.post('/api/tasks', json={"description": "Без названия"})
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert data['error'] == 'Title is required'


def test_create_task_invalid_priority(test_client):
    """Тест: POST /api/tasks — возвращает 400, если priority неверный."""
    response = test_client.post('/api/tasks', json={
        "title": "Неверный приоритет",
        "priority": "неизвестный"
    })
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'Invalid priority' in data['error']


def test_get_all_tasks_with_data(test_client):
    """Тест: GET /api/tasks — возвращает список задач после добавления."""
    # Добавляем несколько задач
    tasks_to_add = [
        {"title": "Задача 1", "priority": "низкий"},
        {"title": "Задача 2", "priority": "высокий"},
        {"title": "Задача 3", "priority": "средний"}
    ]

    for task in tasks_to_add:
        test_client.post('/api/tasks', json=task)

    response = test_client.get('/api/tasks')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) >= 3  # минимум 3 задачи
    # Проверяем, что есть хотя бы одна с высоким приоритетом
    high_priority_tasks = [t for t in data if t['priority'] == 'высокий']
    assert len(high_priority_tasks) >= 1


def test_create_task_with_category(test_client):
    """Тест: POST /api/tasks — создаёт задачу с категорией."""
    # Сначала создадим категорию (если нет)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO categories (name, color) VALUES (?, ?)", ("Тестовая категория", "#FF0000"))
    category_id = cursor.lastrowid
    conn.commit()
    conn.close()

    new_task = {
        "title": "Задача с категорией",
        "priority": "средний",
        "category_id": category_id
    }

    response = test_client.post('/api/tasks', json=new_task)
    assert response.status_code == 201
    data = response.get_json()
    assert data['category_id'] == category_id


def test_get_task_with_category_info(test_client):
    """Тест: GET /api/tasks/<id> — возвращает информацию о категории."""
    # Создаём категорию
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO categories (name, color) VALUES (?, ?)", ("Категория для теста", "#00FF00"))
    category_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Создаём задачу с этой категорией
    new_task = {
        "title": "Задача с категорией",
        "priority": "средний",
        "category_id": category_id
    }
    create_response = test_client.post('/api/tasks', json=new_task)
    task_id = create_response.get_json()['id']

    # Получаем задачу
    response = test_client.get(f'/api/tasks/{task_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert 'category_name' in data
    assert data['category_name'] == "Категория для теста"
    assert 'category_color' in data
    assert data['category_color'] == "#00FF00"