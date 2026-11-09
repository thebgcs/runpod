import base64
import contextlib
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from handler import MODEL_ID, generate_image


PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+X"
    "2ioAAAAASUVORK5CYII="
)


class FakeImage:
    def save(self, target, format):
        if format != "PNG":
            raise ValueError("Expected PNG format")
        target.write(PNG)


class HandlerTests(unittest.TestCase):
    def setUp(self):
        self.generator = Mock()
        self.generator.manual_seed.return_value = self.generator
        self.torch = SimpleNamespace(
            Generator=Mock(return_value=self.generator),
            inference_mode=contextlib.nullcontext,
        )
        result = SimpleNamespace(images=[FakeImage()], nsfw_content_detected=[False])
        self.pipeline = Mock(return_value=result)

    def test_valid_request_returns_a_png_and_seed(self):
        result = generate_image(
            {"input": {"prompt": "  A lighthouse  ", "seed": 42}},
            self.pipeline,
            self.torch,
        )

        self.assertEqual(base64.b64decode(result["image_base64"]), PNG)
        self.assertEqual(result["content_type"], "image/png")
        self.assertEqual(result["model"], MODEL_ID)
        self.assertEqual(result["seed"], 42)
        self.assertFalse(result["nsfw_content_detected"])
        self.torch.Generator.assert_called_once_with(device="cuda")
        self.generator.manual_seed.assert_called_once_with(42)
        self.assertEqual(self.pipeline.call_args.kwargs["prompt"], "A lighthouse")

    def test_missing_seed_is_generated(self):
        with patch("handler.secrets.randbits", return_value=123):
            result = generate_image({"input": {"prompt": "A lighthouse"}}, self.pipeline, self.torch)

        self.assertEqual(result["seed"], 123)
        self.generator.manual_seed.assert_called_once_with(123)

    def test_invalid_input_does_not_call_the_model(self):
        invalid_jobs = [
            {},
            {"input": None},
            {"input": []},
            {"input": {}},
            {"input": {"prompt": "   "}},
            {"input": {"prompt": 42}},
        ]
        for job in invalid_jobs:
            with self.subTest(job=job):
                self.assertIn("error", generate_image(job, self.pipeline, self.torch))

        self.pipeline.assert_not_called()
        self.torch.Generator.assert_not_called()

    def test_invalid_seed_does_not_call_the_model(self):
        for seed in [True, -1, 4294967296, 1.2, "42"]:
            with self.subTest(seed=seed):
                result = generate_image(
                    {"input": {"prompt": "A lighthouse", "seed": seed}},
                    self.pipeline,
                    self.torch,
                )
                self.assertIn("error", result)

        self.pipeline.assert_not_called()
        self.torch.Generator.assert_not_called()

    def test_model_failure_is_not_hidden(self):
        self.pipeline.side_effect = RuntimeError("model failed")

        with self.assertRaisesRegex(RuntimeError, "model failed"):
            generate_image({"input": {"prompt": "A lighthouse", "seed": 1}}, self.pipeline, self.torch)


if __name__ == "__main__":
    unittest.main()
