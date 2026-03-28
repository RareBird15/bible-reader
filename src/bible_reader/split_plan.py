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
MIN_NON_EMPTY_LINES = 2
MIN_H2_HEADINGS_PER_DAY = 2


def log_unhandled_exception(message: str) -> None:
    """Log unexpected failures even if logging has not been configured yet."""
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.ERROR,
            format="%(asctime)s %(levelname)s %(message)s",
        )
    logger.exception(message)


def validate_section(section: str, section_number: int) -> list[str]:
    """Validate a split section against expected day-file structure.

    Section 1 is treated as cover/introduction and only requires non-empty text.
    All later sections must contain at least two non-empty lines and at least two
    H2 headings ("##"), matching downstream parser expectations.
    """
    lines = section.splitlines()
    non_empty_lines = [line for line in lines if line.strip()]
    heading_count = sum(1 for line in lines if line.startswith("##"))

    errors: list[str] = []

    min_non_empty = 1 if section_number == 1 else MIN_NON_EMPTY_LINES
    if len(non_empty_lines) < min_non_empty:
        errors.append(
            f"section {section_number} has {len(non_empty_lines)} non-empty line(s); "
            f"expected at least {min_non_empty}",
        )

    if section_number > 1 and heading_count < MIN_H2_HEADINGS_PER_DAY:
        errors.append(
            f"section {section_number} has {heading_count} '##' heading(s); "
            f"expected at least {MIN_H2_HEADINGS_PER_DAY}",
        )

    return errors


def main() -> None:
    """Split the plan markdown into per-day commentary files."""
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    OUTPUT_DIR.mkdir(exist_ok=True)

    text = INPUT_FILE.read_text(encoding="utf-8")

    # Split on "\n# " so each "# Heading" line becomes the start of a new section.
    # The delimiter requires a preceding newline, so a "# " at the very start of
    # the file would not split — but the source plan always has leading content
    # (cover/TOC) before the first heading, so this is intentional.
    sections = re.split(r"\n# ", text)

    count = 1

    for raw_section in sections:
        section = raw_section.strip()
        if not section:
            continue

        section_errors = validate_section(section, count)
        if section_errors:
            raise ValueError("; ".join(section_errors))

        output_file = OUTPUT_DIR / f"day{count:04}.txt"

        output_file.write_text(section, encoding="utf-8")
        logger.debug("Wrote %s", output_file)

        count += 1

    logger.info("Created %d reading files.", count - 1)


if __name__ == "__main__":
    try:
        main()
    except ValueError:
        if not logging.getLogger().hasHandlers():
            logging.basicConfig(
                level=logging.ERROR,
                format="%(asctime)s %(levelname)s %(message)s",
            )
        # Fix TRY401: Removed string interpolation and exc argument.
        logger.exception("Validation error while splitting plan.")
        sys.exit(EXIT_ERROR)
    except (FileNotFoundError, PermissionError):
        log_unhandled_exception(
            "File error while reading input plan or writing output day files",
        )
        sys.exit(EXIT_ERROR)
    # FileNotFoundError/PermissionError are handled above; this catches other
    # OS-level failures (for example, invalid path state or interrupted I/O).
    except OSError:
        log_unhandled_exception(
            "Unexpected OS error while processing plan files "
            "(reading input or writing output day files)",
        )
        sys.exit(EXIT_ERROR)
