"""
Модульные тесты для API endpoints ToDo приложения
Версия без conftest.py - все фикстуры внутри файла
"""
import json
import pytest
import sys
import os

# Добавляем корневую директорию в путь Python для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app as flask_app, task_store

# Фикстуры
@pytest.fixture
def app():
    """Фикстура для приложения Flask"""
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    return flask_app

@pytest.fixture
def client(app):
    """Фикстура для тестового клиента Flask"""
    return app.test_client()

@pytest.fixture
def cleanup_tasks():
    """Автоматическая очистка задач перед и после каждого теста"""
    # Сохраняем исходные задачи
    original_tasks = task_store.tasks.copy()

    # Очищаем хранилище
    task_store.clear()

    yield

    # Восстанавливаем исходные задачи
    task_store.tasks = original_tasks

@pytest.fixture
def sample_tasks():
    """Фикстура с тестовыми задачами"""
    return [
        {'id': 1, 'title': 'Test Task 1', 'completed': False, 'priority': 'high', 'created_at': '2024-01-01'},
        {'id': 2, 'title': 'Test Task 2', 'completed': True, 'priority': 'medium', 'created_at': '2024-01-02'},
        {'id': 3, 'title': 'Test Task 3', 'completed': False, 'priority': 'low', 'created_at': '2024-01-03'},
    ]

@pytest.fixture
def populated_store(cleanup_tasks, sample_tasks):
    """Фикстура с заполненным хранилищем задач"""
    for task in sample_tasks:
        task_store.tasks.append(task)
    return task_store

# Тесты
class TestTaskAPI:
    """Тесты для API endpoints задач"""

    def test_get_tasks_empty(self, client, cleanup_tasks):
        """Тест получения задач из пустого хранилища"""
        response = client.get('/api/tasks')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'tasks' in data
        assert isinstance(data['tasks'], list)
        assert len(data['tasks']) == 0
        assert data['count'] == 0
        assert data['total'] == 0
        assert data['completed'] == 0
        assert data['active'] == 0

    def test_get_tasks_with_data(self, client, populated_store):
        """Тест получения задач из заполненного хранилища"""
        response = client.get('/api/tasks')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert len(data['tasks']) == 3
        assert data['count'] == 3
        assert data['total'] == 3
        assert data['completed'] == 1
        assert data['active'] == 2

        # Проверяем структуру задач
        for task in data['tasks']:
            assert 'id' in task
            assert 'title' in task
            assert 'completed' in task
            assert 'priority' in task
            assert 'created_at' in task

    def test_get_tasks_filter_all(self, client, populated_store):
        """Тест фильтрации всех задач"""
        response = client.get('/api/tasks?filter=all')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 3

    def test_get_tasks_filter_active(self, client, populated_store):
        """Тест фильтрации активных задач"""
        response = client.get('/api/tasks?filter=active')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 2  # 2 активные задачи
        for task in data['tasks']:
            assert not task['completed']

    def test_get_tasks_filter_completed(self, client, populated_store):
        """Тест фильтрации выполненных задач"""
        response = client.get('/api/tasks?filter=completed')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 1  # 1 выполненная задача
        for task in data['tasks']:
            assert task['completed']

    def test_create_task_success(self, client, cleanup_tasks):
        """Тест успешного создания задачи"""
        task_data = {
            'title': 'New Test Task',
            'priority': 'high'
        }

        # Отправляем JSON
        response = client.post(
            '/api/tasks',
            data=json.dumps(task_data),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = json.loads(response.data)

        assert data['message'] == 'Task created successfully'
        assert 'task' in data
        assert data['task']['title'] == 'New Test Task'
        assert data['task']['completed'] == False
        assert data['task']['priority'] == 'high'
        assert 'id' in data['task']
        assert 'created_at' in data['task']

        # Проверяем, что задача добавлена в хранилище
        response = client.get('/api/tasks')
        data = json.loads(response.data)
        assert data['count'] == 1

    def test_create_task_missing_title(self, client, cleanup_tasks):
        """Тест создания задачи без заголовка"""
        response = client.post(
            '/api/tasks',
            data=json.dumps({'priority': 'high'}),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'Title is required'

    def test_create_task_empty_title(self, client, cleanup_tasks):
        """Тест создания задачи с пустым заголовком"""
        response = client.post(
            '/api/tasks',
            data=json.dumps({'title': '   ', 'priority': 'high'}),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'Title is required'

    def test_get_task_success(self, client, populated_store):
        """Тест получения конкретной задачи"""
        task_id = 1
        response = client.get(f'/api/tasks/{task_id}')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'task' in data
        assert data['task']['id'] == task_id
        assert data['task']['title'] == 'Test Task 1'

    def test_get_task_not_found(self, client, cleanup_tasks):
        """Тест получения несуществующей задачи"""
        response = client.get('/api/tasks/999')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'Task not found'

    def test_toggle_task_success(self, client, populated_store):
        """Тест переключения статуса задачи"""
        task_id = 1

        # Получаем исходное состояние
        response = client.get(f'/api/tasks/{task_id}')
        original_completed = json.loads(response.data)['task']['completed']

        # Переключаем статус
        response = client.post(f'/api/tasks/{task_id}/toggle')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['message'] == 'Task toggled successfully'
        assert data['task']['completed'] == (not original_completed)

    def test_toggle_task_not_found(self, client, cleanup_tasks):
        """Тест переключения несуществующей задачи"""
        response = client.post('/api/tasks/999/toggle')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'Task not found'

    def test_delete_task_success(self, client, populated_store):
        """Тест успешного удаления задачи"""
        task_id = 1

        # Проверяем, что задача существует
        response = client.get(f'/api/tasks/{task_id}')
        assert response.status_code == 200

        # Удаляем задачу
        response = client.delete(f'/api/tasks/{task_id}')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Task deleted successfully'

        # Проверяем, что задача удалена
        response = client.get(f'/api/tasks/{task_id}')
        assert response.status_code == 404

    def test_delete_task_not_found(self, client, cleanup_tasks):
        """Тест удаления несуществующей задачи"""
        response = client.delete('/api/tasks/999')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert data['error'] == 'Task not found'

class TestWebEndpoints:
    """Тесты для веб endpoints (рендеринг HTML)"""

    def test_index_page(self, client, cleanup_tasks):
        """Тест главной страницы"""
        response = client.get('/')

        assert response.status_code == 200
        # Проверяем наличие ключевых элементов
        assert b'<!DOCTYPE html>' in response.data

    def test_index_with_filter_all(self, client, populated_store):
        """Тест главной страницы с фильтром all"""
        response = client.get('/?filter=all')
        assert response.status_code == 200

    def test_index_with_filter_active(self, client, populated_store):
        """Тест главной страницы с фильтром active"""
        response = client.get('/?filter=active')
        assert response.status_code == 200

    def test_index_with_filter_completed(self, client, populated_store):
        """Тест главной страницы с фильтром completed"""
        response = client.get('/?filter=completed')
        assert response.status_code == 200

    def test_create_task_web(self, client, cleanup_tasks):
        """Тест создания задачи через веб-форму"""
        response = client.post('/tasks', data={
            'title': 'Web Form Task',
            'priority': 'low'
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b'Web Form Task' in response.data

    def test_create_task_web_empty_title(self, client, cleanup_tasks):
        """Тест создания задачи с пустым заголовком через веб-форму"""
        # Запись количества задач до отправки формы
        response = client.get('/api/tasks')
        data_before = json.loads(response.data)
        count_before = data_before['count']

        # Отправляем форму с пустым заголовком
        response = client.post('/tasks', data={
            'title': '   ',
            'priority': 'low'
        }, follow_redirects=True)

        assert response.status_code == 200

        # Проверяем, что задача не добавилась
        response = client.get('/api/tasks')
        data_after = json.loads(response.data)
        assert data_after['count'] == count_before

    def test_toggle_task_web(self, client, populated_store):
        """Тест переключения задачи через веб"""
        task_id = 1

        response = client.post(f'/tasks/{task_id}/toggle', follow_redirects=True)

        assert response.status_code == 200

    def test_delete_task_web(self, client, populated_store):
        """Тест удаления задачи через веб"""
        task_id = 1

        # Получаем количество задач до удаления
        response = client.get('/api/tasks')
        data_before = json.loads(response.data)
        count_before = data_before['count']

        response = client.post(f'/tasks/{task_id}/delete', follow_redirects=True)

        assert response.status_code == 200

        # Проверяем, что задача удалена
        response = client.get('/api/tasks')
        data_after = json.loads(response.data)
        assert data_after['count'] == count_before - 1

class TestStatistics:
    """Тесты для статистики"""

    def test_statistics_counters(self, client, populated_store):
        """Тест счетчиков статистики"""
        response = client.get('/api/tasks')
        data = json.loads(response.data)

        assert data['total'] == 3
        assert data['completed'] == 1
        assert data['active'] == 2
        assert data['count'] == 3

    def test_statistics_after_operations(self, client, populated_store):
        """Тест статистики после операций с задачами"""
        # Создаем новую задачу
        response = client.post('/api/tasks',
                   data=json.dumps({'title': 'New Task'}),
                   content_type='application/json')
        assert response.status_code == 201

        response = client.get('/api/tasks')
        data = json.loads(response.data)
        assert data['total'] == 4
        assert data['active'] == 3

        # Переключаем задачу
        response = client.post('/api/tasks/1/toggle')
        assert response.status_code == 200

        response = client.get('/api/tasks')
        data = json.loads(response.data)
        assert data['completed'] == 2
        assert data['active'] == 2

        # Удаляем задачу
        response = client.delete('/api/tasks/2')
        assert response.status_code == 200

        response = client.get('/api/tasks')
        data = json.loads(response.data)
        assert data['total'] == 3

class TestTaskValidation:
    """Тесты валидации задач"""

    def test_priority_validation_high(self, client, cleanup_tasks):
        """Тест создания задачи с высоким приоритетом"""
        response = client.post(
            '/api/tasks',
            data=json.dumps({'title': 'Task with high priority', 'priority': 'high'}),
            content_type='application/json'
        )
        assert response.status_code == 201

    def test_priority_validation_medium(self, client, cleanup_tasks):
        """Тест создания задачи со средним приоритетом"""
        response = client.post(
            '/api/tasks',
            data=json.dumps({'title': 'Task with medium priority', 'priority': 'medium'}),
            content_type='application/json'
        )
        assert response.status_code == 201

    def test_priority_validation_low(self, client, cleanup_tasks):
        """Тест создания задачи с низким приоритетом"""
        response = client.post(
            '/api/tasks',
            data=json.dumps({'title': 'Task with low priority', 'priority': 'low'}),
            content_type='application/json'
        )
        assert response.status_code == 201

    def test_title_trimming(self, client, cleanup_tasks):
        """Тест обрезки пробелов в заголовке"""
        response = client.post(
            '/api/tasks',
            data=json.dumps({'title': '  Task with spaces  ', 'priority': 'medium'}),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['task']['title'] == 'Task with spaces'  # Без лишних пробелов

def test_main_app_runs():
    """Тест что основное приложение может быть запущено"""
    from app import app
    assert app is not None
    assert hasattr(app, 'route')

    # Проверяем некоторые маршруты
    rules = [rule.rule for rule in app.url_map.iter_rules()]
    assert '/' in rules
    assert '/tasks' in rules
    assert '/api/tasks' in rules

def test_task_store_methods():
    """Тест методов хранилища задач"""
    from app import task_store

    # Сохраняем исходное состояние
    original_tasks = task_store.tasks.copy()
    task_store.clear()

    try:
        # Тест добавления задачи
        task = task_store.add("Test task", "high")
        assert task['title'] == "Test task"
        assert task['priority'] == "high"
        assert task['completed'] == False
        assert task_store.count() == 1

        # Тест получения задачи по ID
        fetched = task_store.get_by_id(task['id'])
        assert fetched is not None
        assert fetched['id'] == task['id']

        # Тест обновления задачи
        updated = task_store.update(task['id'], completed=True, title="Updated task")
        assert updated['completed'] == True
        assert updated['title'] == "Updated task"

        # Тест подсчета выполненных задач
        task_store.add("Another task", "medium")
        task_store.add("Completed task", "low")
        task_store.update(3, completed=True)

        assert task_store.count() == 3
        assert task_store.count_completed() == 2  # Первая и третья задачи выполнены
        assert task_store.count_active() == 1     # Вторая задача активна

        # Тест удаления задачи
        result = task_store.delete(task['id'])
        assert result == True
        assert task_store.count() == 2

        # Тест получения несуществующей задачи
        assert task_store.get_by_id(999) is None

        # Тест получения всех задач
        all_tasks = task_store.get_all()
        assert len(all_tasks) == 2
        assert isinstance(all_tasks, list)

    finally:
        # Восстанавливаем исходное состояние
        task_store.tasks = original_tasks

def test_app_initial_data():
    """Тест начальных данных приложения"""
    from app import task_store

    # Проверяем что начальные данные загружаются
    initial_count = task_store.count()
    assert initial_count >= 0  # Может быть 0 или больше в зависимости от состояния

    # Добавляем задачу и проверяем что счетчик увеличивается
    task_store.add("Test for initial data")
    assert task_store.count() == initial_count + 1

if __name__ == '__main__':
    # Запуск тестов напрямую
    pytest.main([__file__, '-v', '--tb=short'])