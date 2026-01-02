# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Устанавливаем зависимости ОС (для сборки библиотек)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Порт
EXPOSE 8000

# Запуск (без --reload в продакшене, но можно оставить для dev)
CMD ["python", "-m", "uvicorn", "core.app:app", "--host", "0.0.0.0", "--port", "8000"]