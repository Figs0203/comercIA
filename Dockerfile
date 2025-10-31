FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    locales \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV DJANGO_SETTINGS_MODULE=comercia.settings \
    PORT=8000

EXPOSE 8000

CMD ["bash", "-lc", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn comercia.wsgi:application --bind 0.0.0.0:${PORT}"]


