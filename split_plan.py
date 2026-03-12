"""Split the full plan markdown file into one commentary file per day."""

import argparse
import logging
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_FILE = SCRIPT_DIR / "plan.md"
OUTPUT_DIR = SCRIPT_DIR / "days-commentary"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for script behavior."""
    parser = argparse.ArgumentParser(description="Split reading plan into day files.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


logger = logging.getLogger(__name__)
EXIT_ERROR = 1


def log_unhandled_exception(message: str) -> None:
    """Log unexpected failures even if logging has not been configured yet."""
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.ERROR,
            format="%(asctime)s %(levelname)s %(message)s",
        )
    logger.exception(message)


def main() -> None:
    """Split the plan markdown into per-day commentary files."""
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    OUTPUT_DIR.mkdir(exist_ok=True)

    text = INPUT_FILE.read_text(encoding="utf-8")

    # split on headings like "# Day 1", "# Chapter 1", etc
    sections = re.split(r"\n# ", text)

    count = 1

    for raw_section in sections:
        section = raw_section.strip()
        if not section:
            continue

        output_file = OUTPUT_DIR / f"day{count:04}.txt"

        output_file.write_text(section, encoding="utf-8")
        logger.debug("Wrote %s", output_file)

        count += 1

    logger.info("Created %d reading files.", count - 1)


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, PermissionError):
        log_unhandled_exception(
            "File error while reading input plan or writing output day files",
        )
        sys.exit(EXIT_ERROR)
    # FileNotFoundError/PermissionError are handled above; this catches other
    # OS-level failures (for example, invalid path state or interrupted I/O).
    except OSError:
        log_unhandled_exception(
            (
                "Unexpected OS error while processing plan files "
                "(reading input or writing output day files)"
            ),
        )
        sys.exit(EXIT_ERROR)
