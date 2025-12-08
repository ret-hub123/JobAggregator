FROM python:3.11-slim

# Создаем пользователя
RUN groupadd -r groupdjango && useradd -r -g groupdjango userdj

# Переменные окружения Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# Создаем рабочую директорию
WORKDIR /app

# Сначала копируем только requirements.txt для кэширования
COPY requirements.txt /app/

# Обновляем pip и устанавливаем зависимости
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . /app/

# Собираем статику (если не получается, продолжаем)
RUN python manage.py collectstatic --noinput || echo "Static collection skipped"

# Меняем владельца файлов
RUN chown -R userdj:groupdjango /app

# Переключаемся на непривилегированного пользователя
USER userdj

# Открываем порт
EXPOSE $PORT

# Команда запуска (используем переменную PORT от Render)
CMD gunicorn JobAggregator.wsgi:application --bind 0.0.0.0:$PORT