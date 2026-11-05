FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# requirements-dev.txt (adds the test tools) in docker-compose.yml, requirements.txt in production
ARG REQUIREMENTS=requirements.txt
COPY requirements*.txt .
RUN pip install -r ${REQUIREMENTS}

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn main:app --host 0.0.0.0 --port 8000"]
