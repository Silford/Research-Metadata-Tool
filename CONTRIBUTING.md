# Contributing

Contributions are welcome. The project aims to be a maintainable toolkit for research metadata workflows.

## Development Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -e . pytest
python -m pytest
```

## Guidelines

- Keep UI, business logic, API access, and data loading separate.
- Add new tools as independent modules under `research_metadata_toolkit/toolkit/`.
- Register new CLI workflows in `research_metadata_toolkit/cli.py`.
- Put large configurable datasets in JSON files under `research_metadata_toolkit/data/`.
- Use logging instead of `print()` in reusable modules.
- Add type hints and docstrings for public functions.
- Add tests for parsing, matching, file processing, and error handling.
- Avoid network-dependent unit tests; mock API functions instead.

## Pull Request Checklist

- Existing behavior is preserved or intentionally documented.
- Tests pass with `python -m pytest`.
- New public functions include docstrings and type hints.
- New data/config values are not hardcoded in workflow code.
- Documentation is updated for new workflows.
