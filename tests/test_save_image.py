import base64
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "save_image.py"
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+X"
    "2ioAAAAASUVORK5CYII="
)


class SaveImageTests(unittest.TestCase):
    def test_saves_image_from_completed_job(self):
        with tempfile.TemporaryDirectory() as directory:
            response = Path(directory) / "response.json"
            image = Path(directory) / "image.png"
            response.write_text(
                json.dumps({"status": "COMPLETED", "output": {"image_base64": base64.b64encode(PNG).decode()}}),
                encoding="utf-8",
            )

            result = subprocess.run([sys.executable, str(SCRIPT), str(response), str(image)], capture_output=True, text=True)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(image.read_bytes(), PNG)

    def test_rejects_failed_or_invalid_output(self):
        cases = [
            {"status": "IN_QUEUE"},
            {"status": "FAILED", "error": "prompt is required"},
            {"status": "COMPLETED", "output": {"error": "prompt is required"}},
            {"status": "COMPLETED", "output": {"image_base64": base64.b64encode(b"not a png").decode()}},
        ]
        with tempfile.TemporaryDirectory() as directory:
            response = Path(directory) / "response.json"
            image = Path(directory) / "image.png"
            for data in cases:
                with self.subTest(data=data):
                    response.write_text(json.dumps(data), encoding="utf-8")
                    result = subprocess.run([sys.executable, str(SCRIPT), str(response), str(image)], capture_output=True, text=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(image.exists())


if __name__ == "__main__":
    unittest.main()
