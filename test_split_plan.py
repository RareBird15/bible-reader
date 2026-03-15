"""Tests for split_plan.py splitting and validation behavior."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import split_plan


class SplitPlanTests(unittest.TestCase):
    def _run_main(self, input_file: Path, output_dir: Path) -> None:
        with (
            patch.object(split_plan, "INPUT_FILE", input_file),
            patch.object(split_plan, "OUTPUT_DIR", output_dir),
            patch("sys.argv", ["split_plan.py"]),
        ):
            split_plan.main()

    def test_writes_sections_to_day_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_file = root / "plan.md"
            output_dir = root / "days-commentary"
            input_file.write_text(
                "Cover page\n\n# Day 1\nref\n## Scripture\nA\n## Commentary\nB\n"
                "# Day 2\nref\n## Scripture\nC\n## Commentary\nD\n",
                encoding="utf-8",
            )

            self._run_main(input_file, output_dir)

            self.assertTrue((output_dir / "day0001.txt").exists())
            self.assertTrue((output_dir / "day0002.txt").exists())
            self.assertTrue((output_dir / "day0003.txt").exists())

    def test_validation_rejects_non_cover_section_without_two_h2(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_file = root / "plan.md"
            output_dir = root / "days-commentary"
            input_file.write_text(
                "Cover page\n\n# Day 1\nref\n## Scripture\nA\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                self._run_main(input_file, output_dir)

    def test_cover_section_may_omit_h2_headings(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            input_file = root / "plan.md"
            output_dir = root / "days-commentary"
            input_file.write_text(
                "Simple cover text\n\n# Day 1\nref\n## Scripture\nA\n## Commentary\nB\n",
                encoding="utf-8",
            )

            self._run_main(input_file, output_dir)
            self.assertTrue((output_dir / "day0001.txt").exists())
            self.assertTrue((output_dir / "day0002.txt").exists())


if __name__ == "__main__":
    unittest.main()
