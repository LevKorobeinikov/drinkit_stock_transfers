FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install --upgrade pip --quiet \
    && pip install poetry --quiet \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main --no-root
COPY . .
CMD ["python", "main.py"]