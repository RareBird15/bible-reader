"""Prompt the user to read the Bible only once per day."""

import argparse
import datetime as dt
import logging
import sys

from xdg_base_dirs import xdg_state_home

from . import read_today

logger = logging.getLogger(__name__)

# Follow XDG Standards: Store history/state files in ~/.local/state/bible-reader/
STATE_DIR = xdg_state_home() / "bible-reader"
STAMP_FILE = STATE_DIR / "last_prompt_date.txt"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for script behavior."""
    parser = argparse.ArgumentParser(
        description="Read today's passage if not already prompted today.",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def get_today_str() -> str:
    """Return today's date as a string (YYYY-MM-DD)."""
    # Use a timezone-aware datetime to satisfy Ruff's DTZ rules
    return dt.datetime.now(tz=dt.timezone.utc).astimezone().date().isoformat()


def has_prompted_today() -> bool:
    """Check if the user has already been prompted today."""
    if not STAMP_FILE.exists():
        return False
    try:
        last_stamp = STAMP_FILE.read_text(encoding="utf-8").strip()
        return last_stamp == get_today_str()
    except OSError:
        return False


def mark_prompted_today() -> None:
    """Write today's date to the stamp file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STAMP_FILE.write_text(get_today_str() + "\n", encoding="utf-8")


def main() -> None:
    """Check the date stamp and conditionally run the reading workflow."""
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    if has_prompted_today():
        logger.debug("Already prompted today. Exiting silently.")
        sys.exit(0)

    # Run the reading workflow directly via the imported Python function
    try:
        exit_code = read_today.run_with_single_instance_lock(
            read_today.run_reading_loop,
        )
    except Exception:
        logger.exception("Unexpected error running the reader")
        sys.exit(read_today.EXIT_ERROR)

    # Handle the exit logic exactly like the old bash script
    if exit_code == read_today.EXIT_COMPLETE:
        # Reading was marked complete; record completion for today.
        mark_prompted_today()
        sys.exit(0)
    elif exit_code == read_today.EXIT_USER_DECLINED:
        # User chose not to mark complete; do not stamp.
        sys.exit(read_today.EXIT_USER_DECLINED)
    elif exit_code == read_today.EXIT_LOCKED:
        # Another instance already holds the Python lock; skip quietly.
        sys.exit(0)
    else:
        # Real error in read_today.py; do not stamp and propagate failure.
        logger.error("read_today failed with exit code %d", exit_code)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
