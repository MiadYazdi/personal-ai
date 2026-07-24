from __future__ import annotations

import json
import unittest

from personal_ai.google_grounding import (
    GoogleGroundingConnector,
    GoogleGroundingError,
)


class GoogleGroundingConnectorTests(unittest.TestCase):
    def test_preview_and_fake_execution_use_no_real_network(self) -> None:
        calls: list[tuple[str, dict[str, str], bytes, int]] = []

        def fake_transport(endpoint, headers, body, timeout):
            calls.append((endpoint, headers, body, timeout))
            return (
                200,
                json.dumps(
                    {
                        "output_text": "Synthetic grounded response.",
                        "steps": [
                            {
                                "type": "model_output",
                                "content": [
                                    {
                                        "annotations": [
                                            {
                                                "type": "url_citation",
                                                "title": "Synthetic source",
                                                "url": "https://example.test/source",
                                            }
                                        ]
                                    }
                                ],
                            }
                        ],
                    }
                ).encode("utf-8"),
            )

        connector = GoogleGroundingConnector(
            key_provider=lambda: "synthetic-key",
            transport=fake_transport,
        )
        preview = connector.preview(
            query="Synthetic Google Grounding test only.",
            model_id="gemini-3.5-flash",
        )
        result = connector.execute(
            preview,
            expected_request_sha256=preview.request_sha256,
        )

        self.assertEqual(result.text, "Synthetic grounded response.")
        self.assertEqual(result.sources[0].url, "https://example.test/source")
        self.assertEqual(len(calls), 1)
        self.assertIn(b"google_search", calls[0][2])
        self.assertFalse(preview.to_dict()["network_execution_enabled"])

    def test_missing_local_key_and_digest_change_are_rejected(self) -> None:
        connector = GoogleGroundingConnector(
            key_provider=lambda: None,
            transport=lambda *_: (200, b"{}"),
        )
        preview = connector.preview(
            query="Synthetic query",
            model_id="gemini-3.5-flash",
        )

        with self.assertRaises(GoogleGroundingError):
            connector.execute(
                preview,
                expected_request_sha256=preview.request_sha256,
            )

        with self.assertRaises(GoogleGroundingError):
            connector.execute(
                preview,
                expected_request_sha256="wrong",
            )


if __name__ == "__main__":
    unittest.main()
