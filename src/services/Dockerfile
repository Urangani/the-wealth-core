FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src /app/src

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${SERVICE_PORT:-8000} --app-dir /app/src/services/${SERVICE_DIR}"]
