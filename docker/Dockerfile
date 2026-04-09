FROM python:3.13-slim
WORKDIR /app
RUN mkdir -p /app/drinkit_stock_transfers
COPY pyproject.toml poetry.lock /app/
COPY main.py /app/
COPY bot /app/bot
COPY scheduler /app/scheduler
COPY drinkit_stock_transfers /app/drinkit_stock_transfers
RUN pip install --upgrade pip \
    && pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi
CMD ["python", "main.py"]