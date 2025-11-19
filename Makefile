.PHONY: lint format format-check type-check check quality

lint:
	flake8 .

format:
	isort .
	black .

format-check:
	isort --check-only --diff .
	black --check --diff .

type-check:
	mypy .

check: lint format-check type-check
	echo "All checks passed! ✅"

quality: format check

# Быстрая проверка перед коммитом
pre-commit: format-check lint