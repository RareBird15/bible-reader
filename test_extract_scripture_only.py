import unittest

from extract_scripture_only import trim_blank_lines


class TrimBlankLinesTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
