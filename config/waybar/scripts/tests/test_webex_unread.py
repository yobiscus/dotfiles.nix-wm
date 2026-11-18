import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "webex-unread.py"
SPEC = importlib.util.spec_from_file_location("webex_unread", SCRIPT)
webex_unread = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(webex_unread)


class WebexUnreadTest(unittest.TestCase):
    def test_reads_latest_count_and_rejects_bad_logs(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "current_log.txt"
            phrase = "getFilteredItems::all unread messages count in filter is "

            path.write_text(f"{phrase}4\n{phrase}0\n")
            self.assertEqual(0, webex_unread.unread_count(path))

            entry = phrase + "2\n"
            total = 65536 + 110
            path.write_text("x" * 100 + entry + "x" * (total - 100 - len(entry)))
            self.assertEqual(2, webex_unread.unread_count(path))

            path.write_text("unrelated Webex log line\n")
            with self.assertRaisesRegex(ValueError, "no unread count"):
                webex_unread.unread_count(path)

            path.unlink()
            with self.assertRaises(FileNotFoundError):
                webex_unread.unread_count(path)

    def test_preserves_count_across_rotation_and_updates_to_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "current_log.txt"
            cache = root / "cache" / "webex-unread"
            phrase = "all unread messages count in filter is "

            def read_count():
                return webex_unread.cached_unread_count(path, cache)

            path.write_text(f"{phrase}3\n")
            self.assertEqual(3, read_count())
            self.assertEqual("3", cache.read_text())

            path.rename(root / "current_log1.txt")
            self.assertEqual(3, read_count())
            path.write_text("unrelated Webex log line\n")
            self.assertEqual("3", webex_unread.status(lambda: True, read_count)["text"])
            self.assertIn("3 unread spaces", webex_unread.icon(lambda: True, read_count))

            path.write_text(f"{phrase}0\n")
            self.assertEqual(0, read_count())
            path.write_text("")
            self.assertEqual(0, read_count())
            self.assertEqual("0", cache.read_text())
            self.assertEqual("read", webex_unread.status(lambda: True, read_count)["class"])

    def test_requires_a_valid_cached_count_when_log_has_no_count(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "current_log.txt"
            cache = Path(directory) / "webex-unread"
            path.write_text("")
            with self.assertRaisesRegex(ValueError, "no unread count"):
                webex_unread.cached_unread_count(path, cache)

            for value in ("", "invalid", "-1"):
                cache.write_text(value)
                with self.subTest(cache=value), self.assertRaisesRegex(ValueError, "no unread count"):
                    webex_unread.cached_unread_count(path, cache)

            path.unlink()
            with self.assertRaises(FileNotFoundError):
                webex_unread.cached_unread_count(path, cache)

    def test_cache_write_failure_does_not_hide_live_count(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "current_log.txt"
            path.write_text("all unread messages count in filter is 2\n")
            self.assertEqual(2, webex_unread.cached_unread_count(path, path / "cache"))

    def test_status_states(self):
        self.assertEqual("hidden", webex_unread.status(lambda: False)["class"])
        self.assertEqual("", webex_unread.icon(lambda: False))
        self.assertEqual("read", webex_unread.status(lambda: True, lambda: 0)["class"])
        self.assertEqual("unread", webex_unread.status(lambda: True, lambda: 3)["class"])

        error = webex_unread.status(
            lambda: True,
            lambda: (_ for _ in ()).throw(ValueError("bad log")),
        )
        self.assertEqual("!", error["text"])
        self.assertEqual("error", error["class"])
        self.assertIn("bad log", error["tooltip"])


if __name__ == "__main__":
    unittest.main()
