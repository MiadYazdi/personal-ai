from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from personal_ai.online_control import OnlineControlError, OnlineControlPlanner


class OnlineControlPlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_directory.name)
        self.planner = OnlineControlPlanner(self.root)

    def tearDown(self) -> None:
        self.temp_directory.cleanup()

    def test_egress_preview_never_enables_network(self) -> None:
        preview = self.planner.preview_egress(
            provider_id="future-provider",
            model_id="future-model",
            action="online_chat",
            outbound_summary="Synthetic external request preview only.",
            data_categories=["user_declared_text"],
            estimated_bytes=128,
        )

        self.assertFalse(preview.to_dict()["network_execution_enabled"])
        self.assertTrue(preview.to_dict()["requires_fresh_confirmation"])
        self.assertEqual(preview.destination, "future-provider:future-model")

    def test_evolution_preview_is_proposal_only_and_scoped(self) -> None:
        preview = self.planner.preview_evolution(
            repository_scope=self.root,
            proposal_summary="Synthetic code-quality proposal.",
            proposed_diff=(
                "diff --git a/src/example.py b/src/example.py\n"
                "--- a/src/example.py\n"
                "+++ b/src/example.py\n"
                "@@ -1 +1 @@\n"
                "-old\n"
                "+new\n"
            ),
            validation_plan=["Run synthetic tests", "Review diff"],
        )

        self.assertTrue(preview.to_dict()["proposal_only"])
        self.assertFalse(preview.to_dict()["apply_enabled"])
        self.assertEqual(preview.touched_files, ("src/example.py",))

        with self.assertRaises(OnlineControlError):
            self.planner.preview_evolution(
                repository_scope=self.root.parent,
                proposal_summary="Outside root",
                proposed_diff=(
                    "diff --git a/x.py b/x.py\n"
                    "+++ b/x.py\n"
                    "+x\n"
                ),
                validation_plan=["Review"],
            )


if __name__ == "__main__":
    unittest.main()
