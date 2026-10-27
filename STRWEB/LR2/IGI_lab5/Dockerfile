FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p logs media staticfiles

ENV DJANGO_SETTINGS_MODULE=cosmet_center.settings
ENV PYTHONUNBUFFERED=1

RUN python manage.py collectstatic --no-input 2>/dev/null || true

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
