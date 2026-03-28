"""Extracts scripture from reading plan files containing both scripture and commentary.

Extracts only the scripture portion from each day's commentary file and saves it to a
new file in the 'days' directory. The scripture portion is defined as the text
between the first and second '##' headings in each file. Leading and trailing blank
lines are removed from the extracted scripture.
"""

import argparse
import logging
import sys

from xdg_base_dirs import xdg_data_home


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for script behavior."""
    parser = argparse.ArgumentParser(description="Extract scripture-only files.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


logger = logging.getLogger(__name__)

# Read and write from the standard XDG Data directory
DATA_DIR = xdg_data_home() / "bible-reader"
SOURCE = DATA_DIR / "days-commentary"
DEST = DATA_DIR / "days"

# The scripture is located between the first and second '##' headings in each file.
MIN_HEADING_COUNT = 2
EXIT_ERROR = 1


def log_unhandled_exception(message: str) -> None:
    """Log failures even when logging is not configured yet."""
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.ERROR,
            format="%(asctime)s %(levelname)s %(message)s",
        )
    logger.exception(message)


def trim_blank_lines(lines: list[str]) -> list[str]:
    """Return lines with only leading and trailing blank lines removed."""
    if not lines:
        return []

    start = 0
    end = len(lines) - 1

    while start <= end and not lines[start].strip():
        start += 1

    while end >= start and not lines[end].strip():
        end -= 1

    return lines[start : end + 1] if start <= end else []


def main() -> None:
    """Run scripture extraction from commentary day files."""
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    logger.info("Starting extraction from %s to %s", SOURCE, DEST)

    DEST.mkdir(exist_ok=True)
    skipped_files = 0

    for file in sorted(SOURCE.glob("day*.txt")):
        logger.debug("Processing file %s", file.name)
        lines = file.read_text(encoding="utf-8").splitlines()

        heading_count = 0
        start_idx = None
        end_idx = None

        for idx, line in enumerate(lines):
            if line.startswith("##"):
                heading_count += 1
                if heading_count == 1:
                    # Scripture starts after the first heading
                    start_idx = idx + 1
                elif heading_count == MIN_HEADING_COUNT:
                    # Scripture ends just before the second heading
                    end_idx = idx
                    break

        if heading_count < MIN_HEADING_COUNT:
            logger.warning(
                "File %s has %d heading(s), expected at least %d; skipping output file",
                file.name,
                heading_count,
                MIN_HEADING_COUNT,
            )
            skipped_files += 1
            continue

        scripture = trim_blank_lines(lines[start_idx:end_idx])

        out_file = DEST / file.name
        out_file.write_text("\n".join(scripture) + "\n", encoding="utf-8")
        logger.debug(
            "Processed %s: extracted %d lines of scripture",
            file.name,
            len(scripture),
        )

    logger.info("Created scripture-only files in: %s", DEST)
    logger.info("Skipped %d file(s) due to insufficient headings", skipped_files)


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError:
        log_unhandled_exception(
            "File not found during scripture extraction "
            "(check source/commentary files and destination directory)",
        )
        sys.exit(EXIT_ERROR)
    except PermissionError:
        log_unhandled_exception(
            "Permission error during scripture extraction "
            "(insufficient rights to read source or write destination)",
        )
        sys.exit(EXIT_ERROR)
    except OSError:
        log_unhandled_exception(
            "File operation error during scripture extraction",
        )
        sys.exit(EXIT_ERROR)
