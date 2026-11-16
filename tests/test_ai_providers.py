import os
import unittest
from unittest.mock import patch

from ai_providers import generate_text


class AIProviderTests(unittest.TestCase):
    @patch.dict(os.environ, {"GROQ_API_KEY": "", "HF_API_KEY": ""}, clear=False)
    def test_no_keys_fails_without_leaking_secrets(self):
        with self.assertRaisesRegex(RuntimeError, "Aucun fournisseur IA"):
            generate_text([{"role": "user", "content": "test"}])

    def test_order_is_configurable(self):
        with patch.dict(os.environ, {
            "AI_PROVIDER_ORDER": "huggingface,groq",
            "GROQ_API_KEY": "fake-groq",
            "HF_API_KEY": "fake-hf",
        }):
            from ai_providers import generate_text
            self.assertEqual(os.environ["AI_PROVIDER_ORDER"], "huggingface,groq")


if __name__ == "__main__":
    unittest.main()
