import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from connector.src.server import ConnectorHandler


class TestConnectorHandler(unittest.TestCase):

    def test_health_response(self):
        handler = ConnectorHandler

        self.assertIsNotNone(handler)

    def test_filename_pattern_accepts_valid_markdown(self):
        valid_names = [
            "example.md",
            "P001-001 - Test.md",
            "notes_2026.md",
            "Test (1).md",
        ]

        for filename in valid_names:
            self.assertIsNotNone(
                __import__("connector.src.server", fromlist=["FILENAME_PATTERN"])
                .FILENAME_PATTERN.fullmatch(filename)
            )

    def test_filename_pattern_rejects_unsafe_names(self):
        server = __import__(
            "connector.src.server",
            fromlist=["FILENAME_PATTERN"]
        )

        invalid_names = [
            "../evil.md",
            "..\\evil.md",
            "/absolute.md",
            "\\absolute.md",
            "bad/name.md",
            "bad\\name.md",
            ".hidden.md",
            "",
        ]

        for filename in invalid_names:
            self.assertIsNone(
                server.FILENAME_PATTERN.fullmatch(filename)
            )


if __name__ == "__main__":
    unittest.main()