# Contributing

Thanks for contributing.

## Scope

This repository distributes tooling, not copyrighted plan content.

- Do not commit EPUB source files unless you have explicit rights to publish them.
- Do not commit generated `plan.md`, `days/`, or `days-commentary/` content unless you have explicit rights to publish that content.
- Focus contributions on scripts, tests, workflows, and documentation.

## Development Setup

This project uses `uv` for dependency management and packaging.

```bash
git clone [https://github.com/RareBird15/bible-reader.git](https://github.com/RareBird15/bible-reader.git)
cd bible-reader
uv sync
```

This will automatically create a virtual environment and install the package in editable mode along with its dependencies.

## Local Checks

Run these before opening a pull request:

```bash
uvx ruff check .
uv run python -m unittest discover tests -v
```

## Contribution Guidelines

- Keep changes focused and minimal.
- Prefer fixes at the root cause over surface-level workarounds.
- Add or update tests when behavior changes.
- Update `README.md` and `CHANGELOG.md` when user-visible behavior changes.
- Preserve the repository's tooling-only distribution model.

## Accessibility Expectations

Accessibility is a major goal of this project.

Contributions should preserve or improve the ability to read content comfortably with screen readers and other assistive tools.

- Prefer plain, readable text over decorative ASCII or other formatting that adds noise.
- Do not rely on visual alignment, color, spacing tricks, or symbols alone to communicate meaning.
- Keep prompts, labels, and headings predictable and easy to understand when read aloud.
- If output formatting changes, consider how it will sound in a screen reader, not just how it looks in a terminal.
- Treat accessibility regressions as product regressions.

## Pull Requests

- Use clear commit messages and PR titles.
- Explain the problem, the change, and any tradeoffs.
- Include validation notes when relevant.

## Issues

Bug reports are useful when they include:

- what command you ran
- what you expected
- what happened instead
- sample input structure, if the issue involves EPUB parsing

## Release Notes

If your change is user-visible, add it to `CHANGELOG.md` under `Unreleased` unless the release is being prepared immediately.
