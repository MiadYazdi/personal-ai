from __future__ import annotations

import unittest

from personal_ai.agent.terminal_executor import (
    TerminalExecutionError,
    TerminalRunResult,
    UbuntuStructuredTerminalExecutor,
)


class TerminalExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.calls = []

        def runner(argv, cwd, timeout):
            self.calls.append((argv, cwd, timeout))
            return TerminalRunResult(0, b"synthetic stdout", b"", False, 12)

        self.executor = UbuntuStructuredTerminalExecutor(
            executable_resolver=lambda value: "/usr/bin/synthetic"
            if value == "synthetic"
            else None,
            runner=runner,
        )

    def test_exact_argv_and_bounded_result(self) -> None:
        preview = self.executor.preview(
            ["synthetic", "--safe"],
            "/tmp",
            "Synthetic only",
            30,
        )
        result = self.executor.execute(
            preview,
            expected_request_sha256=preview.request_sha256,
        )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout, "synthetic stdout")
        self.assertEqual(
            self.calls[0][0],
            ("/usr/bin/synthetic", "--safe"),
        )

    def test_shell_and_digest_mismatch_are_rejected(self) -> None:
        with self.assertRaises(TerminalExecutionError):
            self.executor.preview(
                ["bash", "-c", "echo x"],
                "/tmp",
                "Unsafe",
                30,
            )

        preview = self.executor.preview(
            ["synthetic"],
            "/tmp",
            "Synthetic",
            30,
        )

        with self.assertRaises(TerminalExecutionError):
            self.executor.execute(
                preview,
                expected_request_sha256="wrong",
            )
