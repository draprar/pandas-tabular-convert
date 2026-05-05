# Contributing

Thanks for taking the time to contribute!

## Quick start

1. Fork the repo and create a feature branch.
2. Install dependencies:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

3. Run checks before opening a PR:

```powershell
pytest --cov=src/file_converter --cov-fail-under=80
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/
python -m bandit -r src/
```

4. Auto-fix formatting issues:

```powershell
ruff check src/ tests/ --fix
ruff format src/ tests/
```

## Pre-commit Hooks (Optional)

Install pre-commit to run checks automatically before commits:

```powershell
pip install pre-commit
pre-commit install
```

By default, pre-commit runs only on staged files. Use pre-commit run --all-files to scan the entire project.

This will run ruff, mypy, bandit, and other checks before each commit.

To run manually on all files:

```powershell
pre-commit run --all-files
```

## Commit Messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/).

**Format:**
```
<type>(<scope>): <short description>
```

**Common types:**
- `feat`
- `fix`
- `docs`
- `test`
- `refactor`
- `ci`
- `chore`
- `perf`

Scope is optional but recommended for larger changes.

**Examples:**
```
feat(cli): add verbose logging
fix(loaders): handle empty CSV files
docs(readme): update installation instructions
```

## PR guidelines

- Keep changes focused and well-scoped.
- Add or update tests for behavior changes.
- Update documentation if you change user-facing behavior.
- Ensure CI is green before requesting review.
- Follow commit message conventions (see above)

## Development

See [README.md](README.md) for project overview.
