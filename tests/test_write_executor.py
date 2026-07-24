from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from personal_ai.agent.write_executor import (
    WriteFileError,
    UbuntuWriteFileExecutor,
)


class WriteFileExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.scope = Path(self.temp_directory.name) / "scope"
        self.scope.mkdir()
        self.target = self.scope / "synthetic.txt"
        self.target.write_text("old synthetic text\n", encoding="utf-8")
        self.calls: list[tuple[Path, bytes, int, bool]] = []

        def fake_atomic_writer(target, content, mode, create_only):
            self.calls.append((target, content, mode, create_only))

        self.executor = UbuntuWriteFileExecutor(
            atomic_writer=fake_atomic_writer,
        )

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_overwrite_preview_has_hash_diff_and_fake_write_only(self) -> None:
        preview = self.executor.preview(
            self.scope,
            self.target,
            "new synthetic text\n",
        )

        self.assertEqual(preview.operation, "overwrite")
        self.assertIsNotNone(preview.old_sha256)
        self.assertIn("-old synthetic text", preview.diff)
        self.assertIn("+new synthetic text", preview.diff)

        result = self.executor.execute(
            preview,
            expected_request_sha256=preview.request_sha256,
        )

        self.assertEqual(result.operation, "overwrite")
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][0], self.target)
        self.assertFalse(self.calls[0][3])
        self.assertEqual(
            self.target.read_text(encoding="utf-8"),
            "old synthetic text\n",
        )

    def test_create_uses_new_file_mode_and_scope_is_enforced(self) -> None:
        preview = self.executor.preview(
            self.scope,
            "new-synthetic.txt",
            "created only in a fake writer\n",
        )

        self.assertEqual(preview.operation, "create")
        self.assertEqual(preview.resulting_mode, "0o600")

        self.executor.execute(
            preview,
            expected_request_sha256=preview.request_sha256,
        )
        self.assertTrue(self.calls[0][3])
        self.assertEqual(self.calls[0][2], 0o600)

        with self.assertRaises(WriteFileError):
            self.executor.preview(
                self.scope,
                self.scope.parent / "outside.txt",
                "outside selected scope",
            )

    def test_changed_target_and_digest_mismatch_are_rejected(self) -> None:
        preview = self.executor.preview(
            self.scope,
            self.target,
            "new synthetic text\n",
        )

        with self.assertRaises(WriteFileError):
            self.executor.execute(
                preview,
                expected_request_sha256="wrong",
            )

        self.target.write_text("changed after preview\n", encoding="utf-8")
        with self.assertRaises(WriteFileError):
            self.executor.execute(
                preview,
                expected_request_sha256=preview.request_sha256,
            )

        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
