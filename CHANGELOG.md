# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [Unreleased]

## [1.1.0] - 2026-03-17

### Added

- Add license file with MIT License text.
- Add issue templates for bug reports and feature requests.
- Add config file to enable blank issues and set up a discussion link.
- Add pull request template to guide contributors in providing necessary information and context.
- Add CONTRIBUTING.md with development setup instructions, contribution guidelines, and accessibility expectations.
- Update scripts with docstrings and typing annotations for better readability and maintainability.

### Fixed

- Fix a missing command in the Quick Start section of the README for the full setup from EPUB workflow.

### Changed

- Replace POSIX `fcntl` locking in `read_today.py` with non-blocking `filelock` runtime locking.
- Simplify `maybe_read_bible.sh` by removing manual PID/stale lock-directory handling and delegating lock ownership to Python.

## [1.0.1] - 2026-03-15

### Added

- Create a changelog file to track user-visible changes in a structured format.
- Set up a release workflow that triggers on version tag pushes and publishes GitHub Releases with notes from the changelog.

## [1.0.0] - 2026-03-15

### Added

- EPUB importer script for WorldBiblePlans-style inputs (`import_worldbibleplans_epub.py`).
- Unit test coverage for importer parsing and error scenarios.
- CI workflow for linting and unit tests on pushes and pull requests.
- Ruff configuration to enforce consistent style in source and tests.

### Changed

- Fixed daily counter handling in `read_today.py` to avoid accidental value corruption.
- Improved day-count detection to derive plan length dynamically from day files.
- Hardened shell locking and prompt-stamp flow in `maybe_read_bible.sh`.
- Expanded README with compatibility notes, workflow guidance, and public-use disclaimers.

### Security

- Updated repository policy to keep local runtime state and copyrighted source content out of version control.

[unreleased]: https://github.com/RareBird15/bible-reader/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/RareBird15/bible-reader/releases/tag/v1.1.0
[1.0.1]: https://github.com/RareBird15/bible-reader/releases/tag/v1.0.1
[1.0.0]: https://github.com/RareBird15/bible-reader/releases/tag/v1.0.0
