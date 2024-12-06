.PHONY: install test lint format up down clean

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

lint:
	flake8 app/
	mypy app/
	black --check app/
	isort --check-only app/

format:
	black app/
	isort app/

up:
	docker compose up --build -d

down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete 