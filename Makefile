.PHONY: install run lint mypy format test precommit ci
install:
	poetry install
run:
	poetry run python drinkit_stock_transfers/main.py
lint:
	poetry run ruff check .
mypy:
	poetry run mypy --ignore-missing-imports bot drinkit_stock_transfers scheduler main.py
format:
	poetry run ruff check . --fix
test:
	poetry run pytest
precommit:
	poetry run pre-commit run --all-files
ci: lint mypy test