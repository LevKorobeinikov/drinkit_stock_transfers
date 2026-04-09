.PHONY: install run lint format test precommit

install:
	poetry install

run:
	poetry run python drinkit_stock_transfers/main.py

lint:
	poetry run ruff check .

format:
	poetry run ruff check . --fix

test:
	poetry run pytest

precommit:
	poetry run pre-commit run --all-files