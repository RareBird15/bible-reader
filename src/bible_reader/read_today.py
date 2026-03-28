"""Read the current day's passage and optionally advance the reading counter.

Displays the day label, reference, and scripture text in the terminal, then prompts
to mark the reading as complete.

Exit codes:
- 0: reading marked complete
- 1: execution or data error
- 2: user chose not to mark complete
"""

import argparse
import logging
import re
import shutil
import sys
import textwrap
from collections.abc import Callable
from pathlib import Path
from typing import TextIO

from filelock import FileLock, Timeout
from xdg_base_dirs import xdg_data_home

DATA_DIR = xdg_data_home() / "bible-reader"
DATA_DIR.mkdir(parents=True, exist_ok=True)

BASE = DATA_DIR / "days"
COMMENTARY_BASE = DATA_DIR / "days-commentary"
COUNTER = DATA_DIR / "current_day.txt"
RUNTIME_LOCK = DATA_DIR / ".bible-reader.lock"

FIRST_FILE = 2
LAST_FILE = 1190
MIN_COMMENTARY_HEADER_LINES = 2
DAY_FILE_RE = re.compile(r"^day(\d+)\.txt$")
EXIT_COMPLETE = 0
EXIT_ERROR = 1
EXIT_USER_DECLINED = 2
EXIT_LOCKED = 3
VERSE_LINE_RE = re.compile(r"^(\d+)\s+(.*)$")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for script behavior."""
    parser = argparse.ArgumentParser(description="Read today's passage.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


logger = logging.getLogger(__name__)


def ensure_error_logging_configured() -> None:
    """Configure fallback error logging when no handlers are set."""
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.ERROR,
            format="%(asctime)s %(levelname)s %(message)s",
        )


def log_unhandled_exception(message: str) -> None:
    """Log unexpected failures even if logging has not been configured yet."""
    ensure_error_logging_configured()
    logger.exception(message)


def write_user_output(text: str = "") -> None:
    """Write plain output to stdout without logging metadata."""
    sys.stdout.write(f"{text}\n")


def get_terminal_width(min_width: int = 20) -> int:
    """Return a safe terminal width for wrapping output lines."""
    columns = shutil.get_terminal_size(fallback=(100, 24)).columns
    # Keep one spare column to avoid terminal-side soft wrapping.
    return max(columns - 1, min_width)


def wrap_for_terminal(line: str, min_width: int = 20) -> list[str]:
    """Wrap one output line to the current terminal width.

    Wrapping in Python avoids terminal soft-wrap edge cases where very long
    lines can appear visually truncated in some prompt/rendering setups.
    """
    if not line:
        return [""]

    width = get_terminal_width(min_width=min_width)
    return textwrap.wrap(
        line,
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    )


def format_scripture_output(line: str) -> list[str]:
    """Format one scripture line for terminal display.

    Verse lines are wrapped with hanging indentation so continuation lines stay
    visually tied to the verse number.
    """
    match = VERSE_LINE_RE.match(line)
    if not match:
        return wrap_for_terminal(line)

    verse_number, verse_text = match.groups()
    prefix = f"{verse_number} "
    continuation = " " * len(prefix)
    width = get_terminal_width()

    return textwrap.wrap(
        verse_text,
        width=width,
        initial_indent=prefix,
        subsequent_indent=continuation,
        break_long_words=False,
        break_on_hyphens=False,
    )


def write_counter(counter_file: TextIO, day_number: int) -> None:
    """Persist the current day value in a normalized single-line format.

    Raises:
        IOError: If file seek, write, truncate, or flush operations fail.

    """
    counter_file.seek(0)
    counter_file.write(f"{day_number}\n")
    counter_file.truncate()
    counter_file.flush()


def get_problem_path(exc: OSError) -> str:
    """Return the file path associated with an OS exception when available."""
    return getattr(exc, "filename", None) or str(exc)


def get_plan_last_day() -> int:
    """Return the largest day number found in commentary files.

    Falls back to LAST_FILE if no matching files are found.
    """
    day_numbers: list[int] = []
    for path in COMMENTARY_BASE.glob("day*.txt"):
        match = DAY_FILE_RE.match(path.name)
        if not match:
            continue
        day_numbers.append(int(match.group(1)))

    if not day_numbers:
        logger.warning(
            "No commentary day files found in %s; using fallback LAST_FILE=%d",
            COMMENTARY_BASE,
            LAST_FILE,
        )
        return LAST_FILE

    return max(day_numbers)


def get_commentary_lines(day: int) -> list[str]:
    """Read and return lines from the commentary file."""
    commentary_file = COMMENTARY_BASE / f"day{day:04}.txt"
    logger.debug("Reading commentary header from %s", commentary_file)
    return [
        line.strip()
        for line in commentary_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def get_scripture_lines(day: int) -> list[str]:
    """Read and return lines from the scripture file."""
    file = BASE / f"day{day:04}.txt"
    logger.debug("Reading scripture from %s", file)
    return [
        line.replace("\u00a0", " ").rstrip()
        for line in file.read_text(encoding="utf-8").splitlines()
    ]


def output_scripture(
    day_label: str,
    reference: str,
    scripture_lines: list[str],
) -> None:
    """Print the formatted scripture to the terminal."""
    write_user_output()
    write_user_output(day_label)
    write_user_output(reference)
    write_user_output()
    for line in scripture_lines:
        for wrapped_line in format_scripture_output(line):
            write_user_output(wrapped_line)
    write_user_output()


def get_and_normalize_counter(counter_file: TextIO, plan_last_day: int) -> int:
    """Read the counter file and normalize it if invalid."""
    counter_file.seek(0)
    counter_raw = counter_file.read().strip()
    if not counter_raw:
        logger.warning(
            "Counter file %s was empty; resetting to first day %d",
            COUNTER,
            FIRST_FILE,
        )
        write_counter(counter_file, FIRST_FILE)
        return FIRST_FILE
    try:
        day = int(counter_raw)
    except ValueError:
        logger.warning(
            "Counter file %s contained non-numeric value %r; resetting to first day %d",
            COUNTER,
            counter_raw,
            FIRST_FILE,
        )
        write_counter(counter_file, FIRST_FILE)
        return FIRST_FILE
    if day < FIRST_FILE:
        logger.warning(
            "Counter file %s had out-of-range day %d (< %d); resetting to first day",
            COUNTER,
            day,
            FIRST_FILE,
        )
        write_counter(counter_file, FIRST_FILE)
        return FIRST_FILE
    max_valid_counter = plan_last_day + 1
    if day > max_valid_counter:
        logger.warning(
            "Counter file %s had out-of-range day %d (> %d); resetting to first day",
            COUNTER,
            day,
            max_valid_counter,
        )
        write_counter(counter_file, FIRST_FILE)
        return FIRST_FILE
    return day


def prompt_and_update_counter(
    counter_file: TextIO,
    day: int,
    plan_last_day: int,
) -> tuple[int, int, int]:
    """Prompt the user and handle advancing the counter file."""
    if day > plan_last_day:
        return (EXIT_COMPLETE, day, plan_last_day)

    commentary_lines = get_commentary_lines(day)
    if len(commentary_lines) < MIN_COMMENTARY_HEADER_LINES:
        logger.error(
            "Commentary file %s must contain at least "
            "%d non-empty lines (day label and reference); "
            "found %d non-empty lines.",
            COMMENTARY_BASE / f"day{day:04}.txt",
            MIN_COMMENTARY_HEADER_LINES,
            len(commentary_lines),
        )
        return (EXIT_ERROR, day, plan_last_day)

    day_label = commentary_lines[0]
    reference = commentary_lines[1]
    scripture_lines = get_scripture_lines(day)

    output_scripture(day_label, reference, scripture_lines)

    try:
        answer = input("Mark this reading complete? (y/n): ").strip().lower()
    except EOFError:
        logger.warning("No interactive input available; treating as decline.")
        answer = ""

    if answer == "y":
        write_counter(counter_file, day + 1)
        logger.info("Advanced to next day.")
        return (EXIT_COMPLETE, day + 1, plan_last_day)

    logger.info("Keeping your place.")
    return (EXIT_USER_DECLINED, day, plan_last_day)


def run_locked_workflow() -> tuple[
    int,
    int,
    int,
]:
    """Execute read/prompt/update while holding the counter lock.

    Returns:
        A tuple of (exit_code, final_day, plan_last_day) where exit_code
        indicates the result (EXIT_COMPLETE, EXIT_ERROR, or EXIT_USER_DECLINED),
        final_day is the current day counter value, and plan_last_day is the
        highest detected day number in the commentary files.

    """
    if not COUNTER.exists():
        COUNTER.write_text(f"{FIRST_FILE}\n", encoding="utf-8")

    plan_last_day = get_plan_last_day()

    with COUNTER.open("r+", encoding="utf-8") as counter_file:
        day = get_and_normalize_counter(counter_file, plan_last_day)
        return prompt_and_update_counter(counter_file, day, plan_last_day)


def run_reading_loop() -> int:
    """Run the reading workflow loop and return an exit code."""
    while True:
        exit_code, final_day, plan_last_day = run_locked_workflow()

        # If the user completed reading and reached the end of the plan,
        # offer to restart from the beginning.
        if final_day > plan_last_day and exit_code == EXIT_COMPLETE:
            write_user_output()
            write_user_output("You have finished the entire reading plan!")
            try:
                answer = input("Restart from the beginning? (y/n): ").strip().lower()
            except EOFError:
                logger.warning("No interactive input available; skipping restart.")
                answer = ""
            if answer == "y":
                # Reset counter to first day; next loop iteration will use it.
                with COUNTER.open("r+", encoding="utf-8") as counter_file:
                    counter_file.seek(0)
                    write_counter(counter_file, FIRST_FILE)
                continue

        # For all other paths, return the workflow exit code.
        return exit_code


def run_with_single_instance_lock(workflow: Callable[[], int]) -> int:
    """Run a workflow under a non-blocking single-instance lock."""
    lock = FileLock(str(RUNTIME_LOCK), timeout=0)
    try:
        with lock:
            # Serialize the full read/prompt/update cycle to prevent concurrent
            # runs from reading the same day and overwriting updates.
            return workflow()
    except Timeout:
        write_user_output(
            "Another Bible reader instance is already running. "
            "Please try again in a moment.",
        )
        logger.info("Skipped run because lock is already held: %s", RUNTIME_LOCK)
        return EXIT_LOCKED


def main() -> None:
    """Run today's reading workflow and optionally advance the counter."""
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    sys.exit(run_with_single_instance_lock(run_reading_loop))


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as exc:
        missing_path = get_problem_path(exc)
        log_unhandled_exception(f"Required reading file was not found: {missing_path}")
        sys.exit(EXIT_ERROR)
    except PermissionError as exc:
        problem_path = get_problem_path(exc)
        log_unhandled_exception(
            f"Permission error while accessing a required file: {problem_path}",
        )
        sys.exit(EXIT_ERROR)
    except OSError as exc:
        problem_path = get_problem_path(exc)
        log_unhandled_exception(
            "Unexpected file system error while accessing a required file: "
            f"{problem_path}",
        )
        sys.exit(EXIT_ERROR)
