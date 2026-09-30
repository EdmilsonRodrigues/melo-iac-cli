.PHONY: all format lint test build clean help

all: format lint test

format:
	poetry run isort .
	poetry run black .

lint:
	poetry run isort --check .
	poetry run black --check .
	poetry run flake8 .
	poetry run bandit -c pyproject.toml -r src
	poetry run zuban check

test:
	poetry run python -m unittest discover -s tests -p "*_test.py"

build:
	poetry build

clean:
	rm -rf dist/ build/ *.egg-info .zuban_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
