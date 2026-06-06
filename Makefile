.venv:
	uv sync

.PHONY: type-check
type-check: .venv
	uv run pyright .

.PHONY: lint
lint: .venv
	uv run ruff check .

.PHONY: format-check
format-check: .venv
	uv run ruff format --check .

.PHONY: format
format: .venv
	uv run ruff format .

.PHONY: test
test: .venv
	uv run pytest

.PHONY: check
check: format-check lint type-check test
