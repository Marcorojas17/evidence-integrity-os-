# Reemplazar todas las apariciones de "src tests scripts" por "src tests"

lint:
	ruff check src tests

format:
	ruff format src tests
	ruff check --fix src tests

# Y en pyproject.toml:
[tool.ruff]
line-length = 100
target-version = "py311"
src = ["src", "tests"]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101", "S105", "S106", "S311"]
