from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from personal_ai.agent.readonly_executor import (
    MAX_TEXT_BYTES,
    PathScopeError,
    SensitiveModelShareConfirmationRequired,
    SensitiveReadConfirmationRequired,
    TextLimitError,
    UbuntuReadOnlyExecutor,
)


class UbuntuReadOnlyExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_directory.name)
        self.scope = self.root / "scope"
        self.scope.mkdir()
        self.text_file = self.scope / "note.txt"
        self.text_file.write_text("Synthetic text fixture", encoding="utf-8")
        self.outside = self.root / "outside.txt"
        self.outside.write_text("Synthetic outside fixture", encoding="utf-8")
        self.executor = UbuntuReadOnlyExecutor()

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_metadata_and_text_use_selected_canonical_scope(self) -> None:
        preview = self.executor.preview(self.scope, self.text_file, "read_text")
        self.assertEqual(preview.size_bytes, len("Synthetic text fixture"))
        self.assertFalse(preview.sensitive)
        metadata = self.executor.read_metadata(self.scope, self.text_file)
        self.assertEqual(metadata.file_type, "regular_file")
        text = self.executor.read_text(self.scope, self.text_file)
        self.assertEqual(text.content, "Synthetic text fixture")
        self.assertFalse(text.share_with_model)

    def test_outside_path_and_symlink_escape_are_rejected(self) -> None:
        with self.assertRaises(PathScopeError):
            self.executor.read_metadata(self.scope, self.outside)
        link = self.scope / "outside-link.txt"
        try:
            link.symlink_to(self.outside)
        except OSError as error:
            self.skipTest(f"Symlinks unavailable: {error}")
        with self.assertRaises(PathScopeError):
            self.executor.read_metadata(self.scope, link)

    def test_text_limit_and_binary_content_are_rejected(self) -> None:
        large = self.scope / "large.txt"
        large.write_bytes(b"a" * (MAX_TEXT_BYTES + 1))
        with self.assertRaises(TextLimitError):
            self.executor.read_text(self.scope, large)
        binary = self.scope / "binary.bin"
        binary.write_bytes(b"text\x00binary")
        with self.assertRaises(TextLimitError):
            self.executor.read_text(self.scope, binary)

    def test_sensitive_read_and_model_share_need_separate_confirmation(self) -> None:
        secret_dir = self.scope / ".ssh"
        secret_dir.mkdir()
        secret_file = secret_dir / "id_rsa"
        secret_file.write_text("synthetic secret fixture", encoding="utf-8")
        preview = self.executor.preview(self.scope, secret_file, "read_text")
        self.assertTrue(preview.sensitive)
        self.assertTrue(preview.requires_sensitive_confirmation)
        with self.assertRaises(SensitiveReadConfirmationRequired):
            self.executor.read_text(self.scope, secret_file)
        with self.assertRaises(SensitiveModelShareConfirmationRequired):
            self.executor.read_text(
                self.scope,
                secret_file,
                sensitive_confirmed=True,
                share_with_model=True,
            )
        result = self.executor.read_text(
            self.scope,
            secret_file,
            sensitive_confirmed=True,
            share_with_model=True,
            model_share_confirmed=True,
        )
        self.assertEqual(result.content, "synthetic secret fixture")
        self.assertTrue(result.share_with_model)


if __name__ == "__main__":
    unittest.main()
