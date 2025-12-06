#!/bin/bash

echo "🚀 Начинаем настройку проекта..."

# Проверяем наличие Python
if ! command -v python &> /dev/null; then
    echo "❌ Python не найден. Установите Python 3.8+."
    exit 1
fi

# Создаем виртуальное окружение, если ещё не создано
if [ ! -d "venv" ]; then
    echo "📦 Создаём виртуальное окружение..."
    python -m venv venv
else
    echo "✅ Виртуальное окружение уже существует."
fi

# Активируем виртуальное окружение
if [[ "$OSTYPE" == "msys" ]]; then
    # Для Windows (Git Bash)
    source venv/Scripts/activate
elif [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    # Для Linux/macOS
    source venv/bin/activate
else
    echo "⚠️ Неизвестная ОС. Активируйте виртуальное окружение вручную."
fi

# Устанавливаем зависимости
echo "📦 Устанавливаем зависимости из requirements.txt..."
pip install -r requirements.txt

# Проверка установки
echo "✅ Установка завершена!"
echo "💡 Чтобы активировать окружение вручную:"
echo "   - Windows (Git Bash): source venv/Scripts/activate"
echo "   - Linux/macOS: source venv/bin/activate"
echo "   - Windows (PowerShell): .\venv\Scripts\Activate.ps1"

echo "🎉 Готово! Теперь можно запускать приложение."