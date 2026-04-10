# Bible Reader

- [![CI Status](https://github.com/RareBird15/bible-reader/actions/workflows/ci.yml/badge.svg)](https://github.com/RareBird15/bible-reader/actions/workflows/ci.yml)
- [![PyPI version](https://badge.fury.io/py/bible-reader.svg)](https://badge.fury.io/py/bible-reader)

A lightweight terminal workflow for daily Bible reading.

This project stores a day-by-day reading plan, shows one day at a time, and tracks your progress using standard Linux (XDG) directories.

## What This Project Does

- Imports a WorldBiblePlans-style EPUB into a normalized markdown plan.
- Splits a full markdown plan into one file per day with commentary.
- Extracts scripture-only files from commentary files.
- Shows today's reading in the terminal and optionally advances your day counter.
- Includes a command to prompt you to read only once per day, perfect for your shell startup file.

## Project Structure

- `plan.md`: Source markdown reading plan (generated or provided by you).
- `days-commentary/`: Per-day files containing label, reference, scripture, and commentary.
- `days/`: Per-day scripture-only files.
- `src/bible_reader/`: The core Python package containing all script logic.
- `tests/`: Unit tests for the package.

## Local State Files (XDG Standards)

This project respects standard Linux directory structures to keep your home folder clean. Your reading progress and prompt history are stored here:

- **Reading Progress:** `~/.local/share/bible-reader/current_day.txt`
- **Daily Prompt Stamp:** `~/.local/state/bible-reader/last_prompt_date.txt`

If you ever need to reset your local progress, you can edit or delete those specific files.

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (Recommended for installation and dependency management)

## Installation

The easiest way to install the Bible Reader is using [uv](https://github.com/astral-sh/uv). This installs the tools globally so you can use them anywhere.

```bash
uv tool install bible-reader
```

If you prefer using standard `pip`:

```bash
pip install bible-reader
```

## Project Status

This project is actively developed.

Development cadence may be uneven, and there may be periods of slower progress or pauses due to health limitations. Bug reports and well-scoped contributions are still welcome during those periods.

## Accessibility

Accessibility is a core project goal.

This project aims to provide an easy, low-friction, screen-reader-friendly way to read the Bible in a terminal workflow.

When changing output, prompts, or documentation, prefer:

- plain, readable text over decorative formatting.
- predictable headings and labels.
- wording that makes sense when read aloud by a screen reader.
- output that does not rely on visual alignment, color, or ASCII art to communicate meaning.

Contributors should treat regressions in accessibility as real regressions, not cosmetic issues.

## Development Checks

Run these checks locally before committing:

```bash
uv run ruff check .
uv run python3 -m unittest discover tests -v
```

## Quick Start (Daily Workflow)

Because this is a Python package, you no longer need to type `python3 path/to/script.py`. You can use the installed commands from anywhere in your terminal.

### 1. One-Time Setup (From EPUB)

If you are starting from a new WorldBiblePlans EPUB, create a folder for your plan and run this sequence:

```bash
import-epub /path/to/plan.epub --output plan.md
split-plan
extract-scripture
```

### 2\. Daily Reading

To read today's passage:

```bash
bible-reader
```

When prompted:

- Enter `y` to mark the reading complete and advance to the next day.
- Enter `n` to keep your current day.

### 3\. Shell Integration (Read Once Per Day)

If you want your terminal to prompt you to read when you open it, but only once per day, add this command to your `.bashrc` or `.zshrc`:

```bash
maybe-read-bible
```

## Command Reference

All commands support a `--debug` flag for verbose troubleshooting output.

### `import-epub`

**Usage:** `import-epub /path/to/plan.epub --output plan.md`

- Reads EPUB spine order from the package document.
- Detects day pages from `h1` headings like `Day N:`.
- Writes normalized sections with scripture and commentary `##` headings.

### `split-plan`

**Usage:** `split-plan`

- Splits `plan.md` and writes `days-commentary/day0001.txt`, `day0002.txt`, etc.
- Validates each non-cover section has at least two `##` headings.

### `extract-scripture`

**Usage:** `extract-scripture`

- Extracts the text between the first and second `##` headings from the commentary files.
- Writes scripture-only files into `days/` with matching day filenames.

### `bible-reader`

**Usage:** `bible-reader`

- Initializes `current_day.txt` in your XDG Data directory if missing.
- Prints the day label, reference, and scripture text.
- Prompts to mark complete and increments the counter on `y`.
- Uses a file lock to prevent multiple terminal tabs from overwriting your progress concurrently.

### `maybe-read-bible`

**Usage:** `maybe-read-bible`

- Uses a date stamp in your XDG State directory to avoid prompting more than once per calendar date.
- Updates the stamp only when you mark the reading complete (`y`).
- Delegates locking and reading logic to the main `bible-reader` workflow.

## Plan Source and Compatibility

The EPUB import flow is designed specifically for plans from WorldBiblePlans.com:

- [https://worldbibleplans.com/](https://worldbibleplans.com/)

Current compatibility target:

- Plans that include full Bible text plus commentary in each day page.

Known-compatible sample:

- `New-Living-Translation-2015-Chuck-Smith-Commentary-Gen-to-Rev-Scriptures-1-Chapter-Daily-Verse-By-Day.epub`

**Important limitation:** Other EPUB layouts (e.g., plans without commentary, alternate heading structures) are not guaranteed to parse correctly as they have not been broadly tested.

## Copyright and Content Notice

This repository is intended to distribute tooling only.

- Do not commit or publish copyrighted plan content (for example EPUB source files, generated `plan.md`, `days/`, or `days-commentary/`) unless you have explicit rights to do so.
- The repository ignores those content paths by default so they stay local.
- Users should provide their own plan files and are responsible for ensuring they have permission to use that content.

## Request Support

If a specific Bible plan from World Bible Plans is not working with this tool, I would like to help.

Because I use a screen reader, please provide information as **plain text** or **Markdown**. Please do not send screenshots of the error or the plan.

1. **Check your file:** Ensure your plan has "Day" headings (like `Day 1:`) and section headings (like `## Scripture`).
2. **Open an Issue:** Go to the "Issues" tab on GitHub and describe what happened.
3. **Paste a sample:** If possible, paste a small section of the text from the EPUB that is causing the error.
