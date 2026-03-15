# Bible Reader

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

- Python 3.10+
- POSIX-compatible OS (Linux/macOS) for locking support in `read_today.py`
- Bash (for `maybe_read_bible.sh`)

No third-party Python packages are required.

## Note on Day Numbering

The reading counter starts at day 2 (`FIRST_FILE = 2`) because day 1 in the source
file is a cover or introduction page, not a reading day.

`read_today.py` now detects the plan length dynamically from `days-commentary/day*.txt`
and uses `LAST_FILE = 1190` only as a fallback when no day files are found.

## Quick Start

From the project root:

```bash
python3 split_plan.py
python3 extract_scripture_only.py
python3 read_today.py
```

When prompted:

- Enter `y` to advance to the next day.
- Enter `n` to keep your current day.

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
- Uses layered locks by design: `maybe_read_bible.sh` serializes prompt/stamp workflow with a shell lock directory.
- `read_today.py` separately serializes `current_day.txt` counter read/modify/write with a file lock.
- These locks protect different resources and are intentionally separate.

## Recommended Daily Workflow

1. Generate/refresh day files when the source plan changes:

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

## Logging

All Python scripts support:

- Default: `INFO` level
- Verbose troubleshooting: `--debug` for `DEBUG` level

Example:

```bash
python3 read_today.py --debug
```
