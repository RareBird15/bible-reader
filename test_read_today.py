"""Tests for read_today.py reading workflow and counter management."""

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import read_today
from read_today import (
    EXIT_COMPLETE,
    EXIT_USER_DECLINED,
    FIRST_FILE,
    LAST_FILE,
    get_plan_last_day,
    write_counter,
)


class WriteCounterTests(unittest.TestCase):
    def test_writes_day_number(self) -> None:
        buf = io.StringIO()
        write_counter(buf, 42)
        buf.seek(0)
        self.assertEqual(buf.read(), "42\n")

    def test_overwrites_existing_content(self) -> None:
        buf = io.StringIO()
        write_counter(buf, 5)
        write_counter(buf, 10)
        buf.seek(0)
        self.assertEqual(buf.read(), "10\n")

    def test_writes_first_file_value(self) -> None:
        buf = io.StringIO()
        write_counter(buf, FIRST_FILE)
        buf.seek(0)
        self.assertEqual(buf.read(), f"{FIRST_FILE}\n")


def _make_day_files(base: Path, commentary_base: Path, day: int) -> None:
    """Create minimal valid day files for the given day number."""
    (commentary_base / f"day{day:04}.txt").write_text(
        f"Day {day} Label\nDay {day} Reference\n\n## Heading\nScripture text\n",
        encoding="utf-8",
    )
    (base / f"day{day:04}.txt").write_text("Scripture text\n", encoding="utf-8")


def _run_workflow(
    tmpdir: Path,
    counter_value: str,
    user_input: str = "n",
) -> tuple:
    """Run run_locked_workflow with patched paths and mocked input/output."""
    counter = tmpdir / "current_day.txt"
    counter.write_text(counter_value, encoding="utf-8")
    commentary_base = tmpdir / "commentary"
    commentary_base.mkdir(exist_ok=True)
    base = tmpdir / "days"
    base.mkdir(exist_ok=True)
    _make_day_files(base, commentary_base, FIRST_FILE)
    with (
        patch.object(read_today, "COUNTER", counter),
        patch.object(read_today, "COMMENTARY_BASE", commentary_base),
        patch.object(read_today, "BASE", base),
        patch("read_today.write_user_output"),
        patch("builtins.input", return_value=user_input),
    ):
        return read_today.run_locked_workflow()


class CounterValidationTests(unittest.TestCase):
    """Counter is reset to FIRST_FILE on invalid or out-of-range values."""

    def test_non_numeric_counter_resets_to_first_day(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _, final_day, _ = _run_workflow(Path(tmpdir), "garbage")
        self.assertEqual(final_day, FIRST_FILE)

    def test_empty_counter_resets_to_first_day(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _, final_day, _ = _run_workflow(Path(tmpdir), "")
        self.assertEqual(final_day, FIRST_FILE)

    def test_counter_below_first_file_resets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _, final_day, _ = _run_workflow(Path(tmpdir), str(FIRST_FILE - 1))
        self.assertEqual(final_day, FIRST_FILE)

    def test_counter_way_above_last_file_resets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _, final_day, _ = _run_workflow(Path(tmpdir), "9999")
        self.assertEqual(final_day, FIRST_FILE)


class PlanLengthDetectionTests(unittest.TestCase):
    def test_detects_max_day_from_commentary_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            commentary = Path(tmpdir)
            (commentary / "day0002.txt").write_text("x\n", encoding="utf-8")
            (commentary / "day0010.txt").write_text("x\n", encoding="utf-8")
            (commentary / "day0099.txt").write_text("x\n", encoding="utf-8")
            with patch.object(read_today, "COMMENTARY_BASE", commentary):
                detected = get_plan_last_day()
        self.assertEqual(detected, 99)

    def test_falls_back_when_no_day_files_exist(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            commentary = Path(tmpdir)
            with patch.object(read_today, "COMMENTARY_BASE", commentary):
                detected = get_plan_last_day()
        self.assertEqual(detected, LAST_FILE)


class ReadingWorkflowTests(unittest.TestCase):
    """Tests for reading prompt, counter advancement, and EOFError handling."""

    def setUp(self) -> None:
        self._tmpdir_obj = tempfile.TemporaryDirectory()
        tmpdir = Path(self._tmpdir_obj.name)
        self.counter = tmpdir / "current_day.txt"
        self.counter.write_text(f"{FIRST_FILE}\n", encoding="utf-8")
        self.commentary_base = tmpdir / "commentary"
        self.commentary_base.mkdir()
        self.base = tmpdir / "days"
        self.base.mkdir()
        _make_day_files(self.base, self.commentary_base, FIRST_FILE)

    def tearDown(self) -> None:
        self._tmpdir_obj.cleanup()

    def _run(self, user_input: str) -> tuple:
        with (
            patch.object(read_today, "COUNTER", self.counter),
            patch.object(read_today, "COMMENTARY_BASE", self.commentary_base),
            patch.object(read_today, "BASE", self.base),
            patch("read_today.write_user_output"),
            patch("builtins.input", return_value=user_input),
        ):
            return read_today.run_locked_workflow()

    def test_y_advances_counter_and_returns_complete(self) -> None:
        exit_code, final_day, plan_last_day = self._run("y")
        self.assertEqual(exit_code, EXIT_COMPLETE)
        self.assertEqual(final_day, FIRST_FILE + 1)
        self.assertEqual(plan_last_day, FIRST_FILE)
        self.assertEqual(
            self.counter.read_text(encoding="utf-8").strip(),
            str(FIRST_FILE + 1),
        )

    def test_n_keeps_counter_and_returns_declined(self) -> None:
        exit_code, final_day, plan_last_day = self._run("n")
        self.assertEqual(exit_code, EXIT_USER_DECLINED)
        self.assertEqual(final_day, FIRST_FILE)
        self.assertEqual(plan_last_day, FIRST_FILE)
        self.assertEqual(
            self.counter.read_text(encoding="utf-8").strip(),
            str(FIRST_FILE),
        )

    def test_eof_on_reading_prompt_treated_as_decline(self) -> None:
        with (
            patch.object(read_today, "COUNTER", self.counter),
            patch.object(read_today, "COMMENTARY_BASE", self.commentary_base),
            patch.object(read_today, "BASE", self.base),
            patch("read_today.write_user_output"),
            patch("builtins.input", side_effect=EOFError),
        ):
            exit_code, final_day, _ = read_today.run_locked_workflow()
        self.assertEqual(exit_code, EXIT_USER_DECLINED)
        self.assertEqual(final_day, FIRST_FILE)
        # Counter should not have been advanced.
        self.assertEqual(
            self.counter.read_text(encoding="utf-8").strip(),
            str(FIRST_FILE),
        )

    def test_counter_past_detected_plan_last_day_returns_complete(self) -> None:
        """When counter is already past plan_last_day, workflow returns complete."""
        extra_day = FIRST_FILE + 1
        _make_day_files(self.base, self.commentary_base, extra_day)
        self.counter.write_text(f"{extra_day + 1}\n", encoding="utf-8")
        with (
            patch.object(read_today, "COUNTER", self.counter),
            patch.object(read_today, "COMMENTARY_BASE", self.commentary_base),
            patch.object(read_today, "BASE", self.base),
        ):
            exit_code, final_day, plan_last_day = read_today.run_locked_workflow()
        self.assertEqual(exit_code, EXIT_COMPLETE)
        self.assertEqual(plan_last_day, extra_day)
        self.assertEqual(final_day, extra_day + 1)


if __name__ == "__main__":
    unittest.main()
