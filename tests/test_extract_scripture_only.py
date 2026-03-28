"""Tests for extract_scripture_only.py."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bible_reader import extract_scripture_only
from bible_reader.extract_scripture_only import trim_blank_lines


class TrimBlankLinesTests(unittest.TestCase):
    """Tests for line-trimming helper behavior."""

    def test_empty_list_returns_empty(self) -> None:
        self.assertEqual(trim_blank_lines([]), [])

    def test_all_blank_lines_returns_empty(self) -> None:
        self.assertEqual(trim_blank_lines(["", "   ", "\t"]), [])

    def test_internal_blank_lines_are_preserved(self) -> None:
        lines = ["", "Verse 1", "", "Verse 2", "  "]
        self.assertEqual(trim_blank_lines(lines), ["Verse 1", "", "Verse 2"])

    def test_no_outer_blank_lines_returns_original(self) -> None:
        lines = ["Verse 1", "", "Verse 2"]
        self.assertEqual(trim_blank_lines(lines), lines)


class ExtractionTests(unittest.TestCase):
    """Tests for extract_scripture_only.main() file processing pipeline."""

    def _run_main(self, source: Path, dest: Path) -> None:
        """Run extraction with temporary source/destination overrides."""
        with (
            patch.object(extract_scripture_only, "SOURCE", source),
            patch.object(extract_scripture_only, "DEST", dest),
            patch("sys.argv", ["extract_scripture_only.py"]),
        ):
            extract_scripture_only.main()

    def test_extracts_scripture_between_two_headings(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            source.mkdir()
            dest = Path(tmpdir) / "dest"
            (source / "day0001.txt").write_text(
                "Label\n\n## Scripture\nVerse 1\nVerse 2\n## Commentary\n",
                encoding="utf-8",
            )
            self._run_main(source, dest)
            result = (dest / "day0001.txt").read_text(encoding="utf-8")
        self.assertEqual(result, "Verse 1\nVerse 2\n")

    def test_file_with_one_heading_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            source.mkdir()
            dest = Path(tmpdir) / "dest"
            (source / "day0001.txt").write_text(
                "Label\n\n## Only Heading\nSome text\n",
                encoding="utf-8",
            )
            self._run_main(source, dest)
            self.assertFalse((dest / "day0001.txt").exists())

    def test_file_with_no_headings_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            source.mkdir()
            dest = Path(tmpdir) / "dest"
            (source / "day0001.txt").write_text(
                "Label\nSome text without headings\n",
                encoding="utf-8",
            )
            self._run_main(source, dest)
            self.assertFalse((dest / "day0001.txt").exists())

    def test_leading_and_trailing_blank_lines_trimmed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            source.mkdir()
            dest = Path(tmpdir) / "dest"
            (source / "day0001.txt").write_text(
                "Label\n\n## Scripture\n\nVerse 1\n\n## Commentary\n",
                encoding="utf-8",
            )
            self._run_main(source, dest)
            result = (dest / "day0001.txt").read_text(encoding="utf-8")
        self.assertEqual(result, "Verse 1\n")

    def test_multiple_files_all_processed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source"
            source.mkdir()
            dest = Path(tmpdir) / "dest"
            for i in range(1, 4):
                (source / f"day{i:04}.txt").write_text(
                    f"Day {i}\n\n## Scripture\nVerse {i}\n## Commentary\n",
                    encoding="utf-8",
                )
            self._run_main(source, dest)
            for i in range(1, 4):
                result = (dest / f"day{i:04}.txt").read_text(encoding="utf-8")
                self.assertEqual(result, f"Verse {i}\n")


if __name__ == "__main__":
    unittest.main()
