"""Import a WorldBiblePlans-style EPUB into normalized markdown plan format.

This script extracts day entries from an EPUB and writes a `plan.md`-compatible
markdown document that can be consumed by split_plan.py.
"""

from __future__ import annotations

# cspell:words opendocument rootfile itemref idref

import argparse
import datetime as dt
import logging
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = SCRIPT_DIR / "plan.md"

CONTAINER_PATH = "META-INF/container.xml"
OPF_NS = "http://www.idpf.org/2007/opf"
CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"
DAY_LABEL_RE = re.compile(r"^Day\s+(\d+):$", re.IGNORECASE)
DIVIDER_RE = re.compile(r"^-{3,}$")
BLOCK_TAGS = {"h1", "h2", "h3", "p", "li"}
MIN_H2_HEADINGS = 2
EXIT_ERROR = 1

logger = logging.getLogger(__name__)


class EpubImportError(ValueError):
    """Base class for EPUB import validation errors."""


class RootfileMissingError(EpubImportError):
    """Raised when container.xml does not provide a rootfile entry."""

    def __init__(self) -> None:
        """Initialize with a stable, user-facing validation message."""
        super().__init__("No rootfile entry found in EPUB container.xml")


class RootfilePathMissingError(EpubImportError):
    """Raised when rootfile entry exists but has no full-path."""

    def __init__(self) -> None:
        """Initialize with a stable, user-facing validation message."""
        super().__init__("EPUB rootfile is missing full-path attribute")


class NoDayEntriesError(EpubImportError):
    """Raised when no day pages can be extracted from the EPUB."""

    def __init__(self) -> None:
        """Initialize with guidance for unsupported or malformed EPUB input."""
        super().__init__(
            "No day entries were detected in the EPUB. "
            "Verify this is a WorldBiblePlans-style file.",
        )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for EPUB import."""
    parser = argparse.ArgumentParser(
        description=(
            "Import a WorldBiblePlans EPUB into normalized markdown plan format."
        ),
    )
    parser.add_argument("epub", type=Path, help="Path to source EPUB")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output markdown file path (default: ./plan.md)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def local_name(tag: str) -> str:
    """Return XML local tag name without namespace prefix."""
    return tag.split("}", 1)[-1] if "}" in tag else tag


def normalize_text(text: str) -> str:
    """Normalize whitespace and non-breaking spaces in extracted text."""
    clean = text.replace("\u00a0", " ")
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def get_package_document_path(epub_zip: zipfile.ZipFile) -> PurePosixPath:
    """Read container.xml and return the OPF package document path."""
    root = ET.fromstring(epub_zip.read(CONTAINER_PATH))  # noqa: S314
    rootfile = root.find(
        ".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile",
    )
    if rootfile is None:
        raise RootfileMissingError

    full_path = rootfile.get("full-path")
    if not full_path:
        raise RootfilePathMissingError

    return PurePosixPath(full_path)


def get_spine_items(
    epub_zip: zipfile.ZipFile,
    package_path: PurePosixPath,
) -> list[PurePosixPath]:
    """Return content document paths in spine reading order."""
    root = ET.fromstring(epub_zip.read(str(package_path)))  # noqa: S314
    ns = {"opf": OPF_NS}

    manifest: dict[str, str] = {}
    for item in root.findall(".//opf:manifest/opf:item", ns):
        item_id = item.get("id")
        href = item.get("href")
        media_type = item.get("media-type", "")
        if not item_id or not href:
            continue
        if media_type not in {"application/xhtml+xml", "text/html"}:
            continue
        manifest[item_id] = href

    base_dir = package_path.parent
    spine_paths: list[PurePosixPath] = []
    for itemref in root.findall(".//opf:spine/opf:itemref", ns):
        idref = itemref.get("idref")
        if not idref or idref not in manifest:
            continue
        spine_paths.append(base_dir / manifest[idref])

    return spine_paths


def extract_block_tokens(xhtml: str) -> list[tuple[str, str]]:
    """Extract normalized block-level tokens (tag, text) from XHTML body."""
    root = ET.fromstring(xhtml)  # noqa: S314
    body = root.find(".//{http://www.w3.org/1999/xhtml}body")
    if body is None:
        return []

    tokens: list[tuple[str, str]] = []
    for elem in body.iter():
        name = local_name(elem.tag).lower()
        if name not in BLOCK_TAGS:
            continue
        text = normalize_text("".join(elem.itertext()))
        if text:
            tokens.append((name, text))

    return tokens


def parse_day_entry(xhtml: str) -> tuple[int, str] | None:
    """Parse a day entry from one XHTML document.

    Returns:
        (day_number, markdown_section_without_heading) if this file is a day page,
        otherwise None.

    """
    tokens = extract_block_tokens(xhtml)
    if not tokens:
        return None

    day_idx = -1
    day_label = ""
    day_number = 0

    for idx, (tag, text) in enumerate(tokens):
        if tag != "h1":
            continue
        match = DAY_LABEL_RE.match(text)
        if match:
            day_idx = idx
            day_label = text
            day_number = int(match.group(1))
            break

    if day_idx < 0:
        return None

    h2_positions = [i for i, (tag, _) in enumerate(tokens) if tag == "h2"]
    if len(h2_positions) < MIN_H2_HEADINGS:
        logger.debug("Skipping day %d: fewer than two h2 headings", day_number)
        return None

    first_h2 = h2_positions[0]
    second_h2 = h2_positions[1]

    header_candidates = [
        text
        for _, text in tokens[day_idx + 1 : first_h2]
        if text and not DIVIDER_RE.match(text)
    ]

    scripture_heading = tokens[first_h2][1]
    commentary_heading = tokens[second_h2][1]

    reference = header_candidates[0] if header_candidates else scripture_heading
    commentary_title = (
        header_candidates[1] if len(header_candidates) > 1 else commentary_heading
    )

    scripture_lines = [
        text
        for _, text in tokens[first_h2 + 1 : second_h2]
        if text and not DIVIDER_RE.match(text)
    ]
    commentary_lines = [
        text
        for _, text in tokens[second_h2 + 1 :]
        if text and not DIVIDER_RE.match(text)
    ]

    section_lines: list[str] = [
        day_label,
        "",
        reference,
        commentary_title,
        "------------------------------",
        "",
        f"## {scripture_heading}",
        "",
    ]

    section_lines.extend(scripture_lines)
    section_lines.extend(["", f"## {commentary_heading}", ""])
    section_lines.extend(commentary_lines)

    return day_number, "\n".join(section_lines).strip()


def import_epub_to_plan(epub_path: Path, output_path: Path) -> int:
    """Import EPUB day pages and write a normalized markdown plan file.

    Returns:
        Number of day sections written.

    """
    seen_days: set[int] = set()
    sections: list[tuple[int, str]] = []

    with zipfile.ZipFile(epub_path) as epub_zip:
        package_path = get_package_document_path(epub_zip)
        spine_items = get_spine_items(epub_zip, package_path)
        logger.debug("Processing %d spine item(s)", len(spine_items))

        for item in spine_items:
            try:
                xhtml = epub_zip.read(str(item)).decode("utf-8", "ignore")
            except KeyError:
                logger.debug("Skipping missing spine file: %s", item)
                continue

            parsed = parse_day_entry(xhtml)
            if parsed is None:
                continue

            day_number, section_text = parsed
            if day_number in seen_days:
                logger.warning(
                    "Duplicate day %d encountered in %s; keeping first occurrence",
                    day_number,
                    item,
                )
                continue

            seen_days.add(day_number)
            sections.append((day_number, section_text))

    if not sections:
        raise NoDayEntriesError

    sections.sort(key=lambda item: item[0])

    generated_at = dt.datetime.now(tz=dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    cover = [
        "Imported reading plan",
        f"Source EPUB: {epub_path.name}",
        f"Generated: {generated_at}",
        f"Detected days: {sections[0][0]}-{sections[-1][0]} ({len(sections)} total)",
    ]

    parts = ["\n".join(cover).strip()]
    for day_number, section in sections:
        day_heading = f"Day {day_number}:"
        section_lines = section.splitlines()
        if section_lines and DAY_LABEL_RE.match(section_lines[0]):
            body = "\n".join(section_lines[1:]).lstrip("\n")
        else:
            body = section
        parts.append(f"# {day_heading}\n\n{body}")

    output_path.write_text("\n\n".join(parts).strip() + "\n", encoding="utf-8")
    return len(sections)


def main() -> None:
    """Run EPUB import CLI."""
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    epub_path = args.epub
    output_path = args.output

    if not epub_path.exists():
        raise FileNotFoundError(epub_path)

    section_count = import_epub_to_plan(epub_path, output_path)
    logger.info("Wrote %d day section(s) to %s", section_count, output_path)


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, PermissionError):
        logging.basicConfig(
            level=logging.ERROR,
            format="%(asctime)s %(levelname)s %(message)s",
        )
        logger.exception("File error during EPUB import")
        sys.exit(EXIT_ERROR)
    except (OSError, ValueError, ET.ParseError, zipfile.BadZipFile):
        logging.basicConfig(
            level=logging.ERROR,
            format="%(asctime)s %(levelname)s %(message)s",
        )
        logger.exception("EPUB import failed")
        sys.exit(EXIT_ERROR)
