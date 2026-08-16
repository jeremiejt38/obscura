# Tests — Obscura

## Validation commands

```bash
python -m py_compile obscura/*.py
python -m pytest
```

The test suite covers configuration persistence, redaction modes and categories, output paths, sensitive-pattern detection, update-check caching and directory-watch behavior.

## Rules

- Do not remove or weaken an existing test without an explicit reason.
- Add or update tests whenever detection, clipboard, folder-monitoring or update behavior changes.
- Use temporary files and mocked OCR/network responses in tests; never use a real clipboard image, external service or production data.
- A bug fix should include a regression test when practical.
- All validation commands must pass before merging into `main`.
