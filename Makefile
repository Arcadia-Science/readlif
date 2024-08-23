.PHONY: lint
lint:
	ruff check --exit-zero .

.PHONY: format
format:
	ruff format .
	ruff check --fix .
