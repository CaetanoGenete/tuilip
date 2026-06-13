.venv:
	uv sync

.PHONY: type-check
develop: .venv

.PHONY: type-check
type-check: develop
	uv run pyright .

.PHONY: lint
lint: develop
	uv run ruff check .

.PHONY: format-check
format-check: develop
	uv run ruff format --check .

.PHONY: format
format: develop
	uv run ruff format .

.PHONY: test
test: develop
	uv run pytest

.PHONY: check
check: format-check lint type-check test

.PHONY: dev-container
dev-container:
	docker build -t tulip .
	docker run --rm -it tulip

.PHONY: clean
clean:
	git clean -dXf
