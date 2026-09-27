# Contributing to datasift-py

Thanks for your interest in contributing!

## Development setup

```bash
git clone https://github.com/sarahsalary/datasift-py.git
cd datasift-py
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

## Running tests

```bash
pytest
```

Run a specific test file:

```bash
pytest tests/test_data.py
```

Run tests with verbose output:

```bash
pytest -v
```

## Code style

- Follow PEP 8.
- Use type hints.
- Keep zero dependencies (standard library only).
- Add tests for new features.
- Keep functions small and focused.

## Pull request process

1. Fork the repository.
2. Create a feature branch:

   ```bash
   git checkout -b feature/my-new-feature
   ```

3. Write tests for your change.
4. Ensure all tests pass:

   ```bash
   pytest
   ```

5. Update documentation if needed.
6. Submit a pull request.

## Reporting issues

Please include:

- Python version
- datasift-py version
- Minimal reproducible example
- Expected vs actual behavior

## Adding a new format

1. Create `src/datasift/formats/myformat_io.py` with `loads`, `dumps`, `read`, `write`.
2. Register it in `src/datasift/formats/__init__.py`.
3. Add tests in `tests/test_formats.py`.
4. Update `docs/formats.md`.