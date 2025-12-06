-- Создание таблицы категорий
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    color TEXT DEFAULT '#CCCCCC' -- HEX-цвет для визуального выделения категории
);

-- Создание таблицы задач
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT CHECK(priority IN ('низкий', 'средний', 'высокий')) NOT NULL DEFAULT 'средний',
    category_id INTEGER,
    deadline DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_completed BOOLEAN DEFAULT 0,

    -- Внешний ключ на таблицу categories
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
);

-- Индексы для часто используемых полей

-- Индекс по статусу выполнения и дедлайну — для фильтрации "не выполненных" и "просроченных"
CREATE INDEX idx_tasks_status_deadline ON tasks (is_completed, deadline);

-- Индекс по приоритету — для быстрой сортировки и фильтрации по важности
CREATE INDEX idx_tasks_priority ON tasks (priority);

-- Индекс по категории — для фильтрации задач по категориям
CREATE INDEX idx_tasks_category_id ON tasks (category_id);

-- Индекс по дедлайну — для поиска ближайших задач
CREATE INDEX idx_tasks_deadline ON tasks (deadline);

-- Индекс по заголовку — для поиска по тексту (LIKE)
CREATE INDEX idx_tasks_title ON tasks (title);

-- Индекс по дате создания — для сортировки по новизне
CREATE INDEX idx_tasks_created_at ON tasks (created_at);


-- Примеры запросов для выборки данных

-- 1. Получить все невыполненные задачи с высоким приоритетом, отсортированные по дедлайну
SELECT t.id, t.title, t.description, t.priority, c.name AS category, t.deadline, t.created_at
FROM tasks t
LEFT JOIN categories c ON t.category_id = c.id
WHERE t.is_completed = 0 AND t.priority = 'высокий'
ORDER BY t.deadline ASC;

-- 2. Найти все задачи, относящиеся к категории "Работа", отсортированные по дате создания
SELECT t.id, t.title, t.description, t.priority, t.deadline, t.created_at
FROM tasks t
JOIN categories c ON t.category_id = c.id
WHERE c.name = 'Работа'
ORDER BY t.created_at DESC;

-- 3. Получить список всех категорий с количеством задач в каждой
SELECT c.name, COUNT(t.id) AS task_count
FROM categories c
LEFT JOIN tasks t ON c.id = t.category_id
GROUP BY c.id, c.name
ORDER BY task_count DESC;

--Пояснения:
--Таблица categories хранит уникальные категории задач с названием и цветом для визуального оформления.
--Таблица tasks содержит основную информацию о задачах, включая связь с категорией через внешний ключ.
--Индексы добавлены для оптимизации производительности при частых операциях: фильтрации по статусу, приоритету, категории, дедлайну и поиске по заголовку.
--Примеры запросов демонстрируют типичные сценарии использования: поиск с фильтрацией, сортировка и агрегация.