# Bible Reader

[![CI](https://github.com/RareBird15/bible-reader/actions/workflows/ci.yml/badge.svg)](https://github.com/RareBird15/bible-reader/actions/workflows/ci.yml)

A lightweight terminal workflow for daily Bible reading.

This project stores a day-by-day reading plan, shows one day at a time, and tracks your progress in a counter file.

## What This Project Does

- Splits a full markdown plan into one file per day with commentary.
- Extracts scripture-only files from commentary files.
- Shows today's reading in the terminal and optionally advances your day counter.
- Includes a shell helper to prompt only once per day.

## Project Structure

- `plan.md`: Source markdown reading plan.
- `days-commentary/`: Per-day files containing label, reference, scripture, and commentary.
- `days/`: Per-day scripture-only files.
- `current_day.txt`: Current day number used by the reader script.
- `split_plan.py`: Builds `days-commentary/` from `plan.md`.
- `extract_scripture_only.py`: Builds `days/` from `days-commentary/`.
- `import_worldbibleplans_epub.py`: Imports a WorldBiblePlans-style EPUB into normalized `plan.md`.
- `read_today.py`: Displays current day and prompts to mark complete.
- `maybe_read_bible.sh`: Shell wrapper that runs `read_today.py` once per day.

## Local State Files

The following files are local runtime state and should not be committed:

- `current_day.txt`: your personal reading position
- `.bible_prompt_last_date`: last date the daily shell prompt completed

These files are intentionally listed in `.gitignore`.

If you ever need to reset your local progress:

```bash
echo 2 > current_day.txt
rm -f .bible_prompt_last_date
```

## Requirements

- Python 3.11+
- Bash (for `maybe_read_bible.sh`)
- `filelock` Python package (see installation)

Locking now uses a Python runtime lock file managed by `filelock`.

## Installation

Clone the repository and move into the project directory:

```bash
git clone https://github.com/RareBird15/bible-reader.git
cd bible-reader
```

Optional but recommended:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
```

Install required dependency:

```bash
python3 -m pip install -r requirements.txt
```

## Project Status

This project is actively developed.

Development cadence may be uneven, and there may be periods of slower progress or pauses due to health limitations. Bug reports and well-scoped contributions are still welcome during those periods.

## Accessibility

Accessibility is a core project goal.

This project aims to provide an easy, low-friction, screen-reader-friendly way to read the Bible in a terminal workflow.

When changing output, prompts, or documentation, prefer:

- plain, readable text over decorative formatting
- predictable headings and labels
- wording that makes sense when read aloud by a screen reader
- output that does not rely on visual alignment, color, or ASCII art to communicate meaning

Contributors should treat regressions in accessibility as real regressions, not cosmetic issues.

## Development Checks

Run these checks locally before committing:

```bash
ruff check .
python3 -m unittest -q
```

## Changelog and Releases

- `CHANGELOG.md` tracks user-visible changes using versioned sections.
- Pushing a tag like `v1.0.0` triggers `.github/workflows/release.yml`.
- The release workflow publishes a GitHub Release and uses the matching `CHANGELOG.md` section as release notes.
- Contribution guidelines live in `CONTRIBUTING.md`.
- This repository is licensed under the MIT License. See `LICENSE`.

Typical release flow:

```bash
# 1) Update CHANGELOG.md with a new version section (for example: ## [1.1.0] - YYYY-MM-DD)
# 2) Commit and push the changelog update
git add CHANGELOG.md
git commit -m "Prepare v1.1.0"
git push origin main

# 3) Create and push the version tag
git tag v1.1.0
git push origin v1.1.0
```

## Note on Day Numbering

The reading counter starts at day 2 (`FIRST_FILE = 2`) because day 1 in the source
file is a cover or introduction page, not a reading day.

`read_today.py` now detects the plan length dynamically from `days-commentary/day*.txt`
and uses `LAST_FILE = 1190` only as a fallback when no day files are found.

## Quick Start

From the project root:

```bash
python3 import_worldbibleplans_epub.py /path/to/plan.epub --output plan.md
python3 split_plan.py
python3 extract_scripture_only.py
python3 read_today.py
```

When prompted:

- Enter `y` to advance to the next day.
- Enter `n` to keep your current day.

## Plan Source and Compatibility

The EPUB import flow is designed for plans from WorldBiblePlans.com:

- <https://worldbibleplans.com/>

Current compatibility target:

- Plans that include full Bible text plus commentary in each day page.

Known-compatible sample:

- `New-Living-Translation-2015-Chuck-Smith-Commentary-Gen-to-Rev-Scriptures-1-Chapter-Daily-Verse-By-Day.epub`

Important limitation:

- Other EPUB layouts (for example, plans without commentary, plans with a different heading structure, or custom/non-WorldBiblePlans files) are not guaranteed to parse correctly because they have not been broadly tested yet.

## Copyright and Content Notice

This repository is intended to distribute tooling only.

- Do not commit or publish copyrighted plan content (for example EPUB source files, generated `plan.md`, `days/`, or `days-commentary/`) unless you have explicit rights to do so.
- The repository ignores those content paths by default so they stay local.
- Users should provide their own plan files and are responsible for ensuring they have permission to use that content.

## Script Usage

### 1) Split Plan Into Day Files

```bash
python3 split_plan.py
```

Debug mode:

```bash
python3 split_plan.py --debug
```

Output:

- Writes `days-commentary/day0001.txt`, `day0002.txt`, and so on.
- Validates each non-cover section has at least two `##` headings.

### 0) Import From EPUB (Optional)

```bash
python3 import_worldbibleplans_epub.py /path/to/plan.epub --output plan.md
```

Debug mode:

```bash
python3 import_worldbibleplans_epub.py /path/to/plan.epub --output plan.md --debug
```

Behavior:

- Reads EPUB spine order from the package document.
- Detects day pages from `h1` headings like `Day N:`.
- Writes normalized sections with scripture and commentary `##` headings for `split_plan.py`.

### 2) Extract Scripture-Only Files

```bash
python3 extract_scripture_only.py
```

Debug mode:

```bash
python3 extract_scripture_only.py --debug
```

Output:

- Writes scripture-only files into `days/` with matching day filenames.

### 3) Read Today and Advance Counter

```bash
python3 read_today.py
```

Debug mode:

```bash
python3 read_today.py --debug
```

Behavior:

- Initializes `current_day.txt` if missing.
- Stops when day exceeds configured `LAST_FILE`.
- Prints day label, reference, and scripture text.
- Prompts to mark complete and increments the counter on `y`.

### 4) Prompt Only Once Per Day (Shell Helper)

```bash
bash maybe_read_bible.sh
```

Behavior:

- Uses `.bible_prompt_last_date` to avoid prompting more than once per date.
- Updates the stamp only when you mark the reading complete in `read_today.py` (exit code 0). If you decline to advance or `read_today.py` fails, the stamp is not updated and you may be re-prompted.
- Uses a non-blocking Python runtime lock in `read_today.py` (`.bible-reader.lock`) as the single lock authority.
- If another run already holds the lock, the second run exits gracefully with a clear message.
- The shell helper stays thin: it handles once-per-day stamp logic and delegates locking to Python.

## Recommended Daily Workflow

### Full Setup From EPUB

Run this sequence when starting from a new WorldBiblePlans EPUB:

```bash
python3 import_worldbibleplans_epub.py /path/to/plan.epub --output plan.md
python3 split_plan.py
python3 extract_scripture_only.py
python3 read_today.py
```

1. Generate/refresh day files when the source plan changes:

   ```bash
   python3 import_worldbibleplans_epub.py /path/to/plan.epub --output plan.md
   ```

   then:

   ```bash
   python3 split_plan.py
   python3 extract_scripture_only.py
   ```

2. Run your daily reading:

   ```bash
   python3 read_today.py
   ```

3. Optional: call once-per-day helper from your shell startup or a scheduled task:

   ```bash
   bash maybe_read_bible.sh
   ```

## Future Ideas

- Broaden EPUB compatibility beyond the currently tested WorldBiblePlans-style layouts.
- Add a small bootstrap command that runs import, split, and extract in one step.
- Add optional tests around shell-wrapper behavior and locking edge cases.
- Add support for alternate reading-plan formats besides EPUB-derived markdown.
- Improve release notes and changelog maintenance with more automation over time.

## Contributing

Contributions are welcome, especially focused bug fixes, test coverage improvements, and importer compatibility work.

Before opening a pull request:

- Read `CONTRIBUTING.md` for development expectations.
- Make sure changes preserve or improve accessibility.
- Avoid committing copyrighted source content or generated plan output.
- Run the local checks listed above.

## Logging

All Python scripts support:

- Default: `INFO` level
- Verbose troubleshooting: `--debug` for `DEBUG` level

Example:

```bash
python3 read_today.py --debug
```
