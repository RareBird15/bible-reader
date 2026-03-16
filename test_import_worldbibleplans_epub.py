"""Tests for import_worldbibleplans_epub.py."""

# cspell:words worldbibleplans opendocument rootfiles rootfile OEBPS oebps itemref idref

import tempfile
import unittest
import zipfile
from pathlib import Path

import import_worldbibleplans_epub as importer


def _build_sample_epub(epub_path: Path) -> None:
    """Create a minimal valid sample EPUB with two day entries."""
    container_xml = """<?xml version='1.0' encoding='utf-8'?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile
      full-path="OEBPS/content.opf"
      media-type="application/oebps-package+xml"
    />
  </rootfiles>
</container>
"""

    content_opf = """<?xml version='1.0' encoding='utf-8'?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0">
  <manifest>
    <item id="toc" href="toc.xhtml" media-type="application/xhtml+xml"/>
    <item id="d1" href="day1.xhtml" media-type="application/xhtml+xml"/>
    <item id="d2" href="day2.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="toc"/>
    <itemref idref="d1"/>
    <itemref idref="d2"/>
  </spine>
</package>
"""

    toc_xhtml = """<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <body><h1>Table of Contents</h1></body>
</html>
"""

    day1_xhtml = """<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <body>
    <h1>Day 1:</h1>
    <p>Genesis 1:1 - 1:31</p>
    <p>Genesis Commentary - 1</p>
    <p>------------------------------</p>
    <h2>Genesis 1:1 - 1:31</h2>
    <p>Verse one.</p>
    <h2>Genesis Commentary 1</h2>
    <p>Commentary one.</p>
  </body>
</html>
"""

    day2_xhtml = """<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <body>
    <h1>Day 2:</h1>
    <p>Genesis 2:1 - 2:25</p>
    <p>Genesis Commentary - 2</p>
    <h2>Genesis 2:1 - 2:25</h2>
    <p>Verse two.</p>
    <h2>Genesis Commentary 2</h2>
    <p>Commentary two.</p>
  </body>
</html>
"""

    with zipfile.ZipFile(epub_path, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr("META-INF/container.xml", container_xml)
        zf.writestr("OEBPS/content.opf", content_opf)
        zf.writestr("OEBPS/toc.xhtml", toc_xhtml)
        zf.writestr("OEBPS/day1.xhtml", day1_xhtml)
        zf.writestr("OEBPS/day2.xhtml", day2_xhtml)


class ImportEpubTests(unittest.TestCase):
    """Tests for EPUB parsing and markdown import output."""

    def test_parse_day_entry_returns_normalized_section(self) -> None:
        xhtml = """<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <body>
    <h1>Day 7:</h1>
    <p>Reference text</p>
    <p>Commentary title</p>
    <h2>Reference text</h2>
    <p>Verse A</p>
    <h2>Commentary title</h2>
    <p>Commentary A</p>
  </body>
</html>
"""
        parsed = importer.parse_day_entry(xhtml)
        self.assertIsNotNone(parsed)
        if parsed is None:
            self.fail("Expected parsed day entry")
        day_number, section = parsed
        self.assertEqual(day_number, 7)
        self.assertIn("## Reference text", section)
        self.assertIn("## Commentary title", section)

    def test_import_epub_writes_sorted_day_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            epub_path = root / "sample.epub"
            out_path = root / "plan.md"
            _build_sample_epub(epub_path)

            count = importer.import_epub_to_plan(epub_path, out_path)
            self.assertEqual(count, 2)

            text = out_path.read_text(encoding="utf-8")
            self.assertIn("Imported reading plan", text)
            self.assertIn("# Day 1:", text)
            self.assertIn("# Day 2:", text)
            self.assertIn("## Genesis 1:1 - 1:31", text)
            self.assertIn("## Genesis Commentary 1", text)

    def test_no_days_raises_value_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            epub_path = root / "empty.epub"
            out_path = root / "plan.md"

            with zipfile.ZipFile(epub_path, "w") as zf:
                zf.writestr("mimetype", "application/epub+zip")
                zf.writestr(
                    "META-INF/container.xml",
                    """<?xml version='1.0' encoding='utf-8'?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
""",
                )
                zf.writestr(
                    "content.opf",
                    """<?xml version='1.0' encoding='utf-8'?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0">
  <manifest>
    <item id="toc" href="toc.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="toc"/>
  </spine>
</package>
""",
                )
                zf.writestr(
                    "toc.xhtml",
                    "<?xml version='1.0' encoding='utf-8'?><html xmlns='http://www.w3.org/1999/xhtml'><body><h1>TOC</h1></body></html>",
                )

            with self.assertRaises(ValueError):
                importer.import_epub_to_plan(epub_path, out_path)


if __name__ == "__main__":
    unittest.main()
