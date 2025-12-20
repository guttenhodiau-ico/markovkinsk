from flask import Flask, render_template, request, redirect, url_for, jsonify
from datetime import datetime

app = Flask(__name__)


# Глобальное хранилище задач
class TaskStore:
    def __init__(self):
        self.tasks = []
        self._load_initial_data()

    def _load_initial_data(self):
        """Загрузка начальных данных только если список пуст"""
        if not self.tasks:
            self.tasks = [
                {'id': 1, 'title': 'Изучить Flask', 'completed': True, 'priority': 'high', 'created_at': '2024-01-20'},
                {'id': 2, 'title': 'Написать ToDo приложение', 'completed': False, 'priority': 'medium',
                 'created_at': '2024-01-21'},
                {'id': 3, 'title': 'Добавить стили', 'completed': False, 'priority': 'high',
                 'created_at': '2024-01-22'},
                {'id': 4, 'title': 'Протестировать приложение', 'completed': False, 'priority': 'low',
                 'created_at': '2024-01-22'},
            ]

    def get_all(self):
        return self.tasks

    def get_by_id(self, task_id):
        for task in self.tasks:
            if task['id'] == task_id:
                return task
        return None

    def add(self, title, priority='medium'):
        task_id = max(task['id'] for task in self.tasks) + 1 if self.tasks else 1
        new_task = {
            'id': task_id,
            'title': title.strip(),
            'completed': False,
            'priority': priority,
            'created_at': datetime.now().strftime('%Y-%m-%d')
        }
        self.tasks.append(new_task)
        return new_task

    def update(self, task_id, **kwargs):
        for task in self.tasks:
            if task['id'] == task_id:
                for key, value in kwargs.items():
                    task[key] = value
                return task
        return None

    def delete(self, task_id):
        self.tasks = [task for task in self.tasks if task['id'] != task_id]
        return True

    def clear(self):
        self.tasks = []

    def count(self):
        return len(self.tasks)

    def count_completed(self):
        return len([task for task in self.tasks if task['completed']])

    def count_active(self):
        return len([task for task in self.tasks if not task['completed']])


# Создаем глобальный экземпляр
task_store = TaskStore()


@app.route('/')
def index():
    filter_type = request.args.get('filter', 'all')

    # Фильтрация задач
    if filter_type == 'active':
        filtered_tasks = [task for task in task_store.get_all() if not task['completed']]
    elif filter_type == 'completed':
        filtered_tasks = [task for task in task_store.get_all() if task['completed']]
    else:
        filtered_tasks = task_store.get_all()

    # Статистика
    total = task_store.count()
    completed = task_store.count_completed()
    active = task_store.count_active()

    return render_template('tasks_list.html',
                           tasks=filtered_tasks,
                           filter_type=filter_type,
                           stats={'total': total, 'completed': completed, 'active': active})


@app.route('/tasks', methods=['POST'])
def create_task():
    title = request.form.get('title')
    priority = request.form.get('priority', 'medium')

    if title and title.strip():
        task_store.add(title, priority)

    return redirect(url_for('index'))


@app.route('/tasks/<int:task_id>/toggle', methods=['POST'])
def toggle_task(task_id):
    task = task_store.get_by_id(task_id)
    if task:
        task_store.update(task_id, completed=not task['completed'])
    return redirect(url_for('index'))


@app.route('/tasks/<int:task_id>/delete', methods=['POST'])
def delete_task(task_id):
    task_store.delete(task_id)
    return redirect(url_for('index'))


# API endpoints для тестирования
@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    """API endpoint для получения всех задач"""
    filter_type = request.args.get('filter', 'all')

    if filter_type == 'active':
        tasks = [task for task in task_store.get_all() if not task['completed']]
    elif filter_type == 'completed':
        tasks = [task for task in task_store.get_all() if task['completed']]
    else:
        tasks = task_store.get_all()

    return jsonify({
        'tasks': tasks,
        'count': len(tasks),
        'total': task_store.count(),
        'completed': task_store.count_completed(),
        'active': task_store.count_active()
    })


@app.route('/api/tasks', methods=['POST'])
def api_create_task():
    """API endpoint для создания задачи"""
    data = request.get_json()
    if not data:
        data = request.form

    title = data.get('title')

    if not title or not title.strip():
        return jsonify({'error': 'Title is required'}), 400

    priority = data.get('priority', 'medium')
    task = task_store.add(title, priority)

    return jsonify({
        'message': 'Task created successfully',
        'task': task
    }), 201


@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def api_get_task(task_id):
    """API endpoint для получения конкретной задачи"""
    task = task_store.get_by_id(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    return jsonify({'task': task})


@app.route('/api/tasks/<int:task_id>/toggle', methods=['POST'])
def api_toggle_task(task_id):
    """API endpoint для переключения статуса задачи"""
    task = task_store.get_by_id(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    updated_task = task_store.update(task_id, completed=not task['completed'])
    return jsonify({
        'message': 'Task toggled successfully',
        'task': updated_task
    })


@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def api_delete_task(task_id):
    """API endpoint для удаления задачи"""
    task = task_store.get_by_id(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    task_store.delete(task_id)
    return jsonify({'message': 'Task deleted successfully'})


if __name__ == '__main__':
    app.run(debug=True)