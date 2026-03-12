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
import sys
from pathlib import Path
from typing import TextIO

try:
    import fcntl
except ImportError:  # pragma: no cover - platform-dependent import
    fcntl = None

SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPT_NAME = Path(__file__).name
BASE = SCRIPT_DIR / "days"
COUNTER = SCRIPT_DIR / "current_day.txt"
COUNTER_LOCK = SCRIPT_DIR / ".current_day.lock"
COMMENTARY_BASE = SCRIPT_DIR / "days-commentary"

FIRST_FILE = 2
LAST_FILE = 1190
MIN_COMMENTARY_HEADER_LINES = 2
EXIT_COMPLETE = 0
EXIT_ERROR = 1
EXIT_USER_DECLINED = 2


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


def run_locked_workflow() -> tuple[int, int]:
    """Execute read/prompt/update while holding the counter lock.

    Returns:
        A tuple of (exit_code, final_day) where exit_code indicates the result
        (EXIT_COMPLETE, EXIT_ERROR, or EXIT_USER_DECLINED) and final_day is the
        current day counter value.

    """
    if not COUNTER.exists():
        COUNTER.write_text(f"{FIRST_FILE}\n", encoding="utf-8")

    # Open in append+read mode (which creates the file if needed) and seek to the
    # start to read/update the counter.
    with COUNTER.open("a+", encoding="utf-8") as counter_file:
        # NOTE: This function is expected to be called while the external
        # COUNTER_LOCK file lock on the counter is already held by main();
        # no additional per-file advisory lock is acquired here to avoid
        # nested locking complexity.
        counter_file.seek(0)
        counter_raw = counter_file.read().strip()
        if not counter_raw:
            logger.warning(
                "Counter file %s was empty; resetting to first day %d",
                COUNTER,
                FIRST_FILE,
            )
            day = FIRST_FILE
            write_counter(counter_file, FIRST_FILE)
        else:
            day = int(counter_raw)

        if day > LAST_FILE:
            return (EXIT_COMPLETE, day)

        commentary_file = COMMENTARY_BASE / f"day{day:04}.txt"
        logger.debug("Reading commentary header from %s", commentary_file)
        commentary_lines = [
            line.strip()
            for line in commentary_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        if len(commentary_lines) < MIN_COMMENTARY_HEADER_LINES:
            logger.error(
                (
                    "Commentary file %s must contain at least "
                    "%d non-empty lines (day label and reference); "
                    "found %d non-empty lines."
                ),
                commentary_file,
                MIN_COMMENTARY_HEADER_LINES,
                len(commentary_lines),
            )
            return (EXIT_ERROR, day)
        day_label = commentary_lines[0]
        reference = commentary_lines[1]

        file = BASE / f"day{day:04}.txt"
        logger.debug("Reading scripture from %s", file)
        # Normalize non-breaking spaces and trim trailing whitespace.
        scripture_lines = [
            line.replace("\u00a0", " ").rstrip()
            for line in file.read_text(encoding="utf-8").splitlines()
        ]

        write_user_output()
        write_user_output(day_label)
        write_user_output(reference)
        write_user_output()

        for line in scripture_lines:
            write_user_output(line)

        write_user_output()

        answer = input("Mark this reading complete? (y/n): ").strip().lower()

        if answer == "y":
            write_counter(counter_file, day + 1)
            logger.info("Advanced to next day.")
            return (EXIT_COMPLETE, day + 1)

        logger.info("Keeping your place.")
        # User intentionally kept current day; this is not an execution error.
        return (EXIT_USER_DECLINED, day)


def main() -> None:
    """Run today's reading workflow and optionally advance the counter."""
    if fcntl is None:
        ensure_error_logging_configured()
        logger.error(
            "%s requires a POSIX-compatible platform (Linux/macOS); "
            "the fcntl module is not available on this platform. "
            "Please run this script on Linux or macOS, or on Windows via WSL "
            "(Windows Subsystem for Linux) or another POSIX-compatible environment.",
            SCRIPT_NAME,
        )
        sys.exit(EXIT_ERROR)

    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    with COUNTER_LOCK.open("w", encoding="utf-8") as lock_file:
        # Serialize the full read/prompt/update cycle to prevent concurrent
        # runs from reading the same day and overwriting updates.
        # This lock coordinates counter state only; maybe_read_bible.sh uses a
        # separate shell-level lock to avoid duplicate prompt/stamp workflows.
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            while True:
                exit_code, final_day = run_locked_workflow()

                # If the user completed reading and reached the end of the plan,
                # offer to restart from the beginning.
                if final_day > LAST_FILE and exit_code == EXIT_COMPLETE:
                    write_user_output()
                    write_user_output("You have finished the entire reading plan!")
                    answer = (
                        input("Restart from the beginning? (y/n): ").strip().lower()
                    )
                    if answer == "y":
                        # Reset counter to first day; next loop iteration will use it.
                        with COUNTER.open("a+", encoding="utf-8") as counter_file:
                            counter_file.seek(0)
                            write_counter(counter_file, FIRST_FILE)
                        continue

                # For all other paths, exit with the returned exit code.
                sys.exit(exit_code)
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


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
