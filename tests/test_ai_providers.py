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
            self.assertEqual(os.environ["AI_PROVIDER_ORDER"], "huggingface,groq")


if __name__ == "__main__":
    unittest.main()


    @patch("groq.Groq")
    @patch("huggingface_hub.InferenceClient")
    @patch.dict(os.environ, {
        "GROQ_API_KEY": "test-groq",
        "HF_API_KEY": "test-hf",
        "AI_PROVIDER_ORDER": "groq,huggingface",
    }, clear=False)
    def test_huggingface_is_used_when_groq_fails(self, mock_hf, mock_groq):
        mock_groq.return_value.chat.completions.create.side_effect = RuntimeError("provider down")
        mock_hf.return_value.chat.completions.create.return_value.choices = [
            type("Choice", (), {"message": type("Message", (), {"content": "réponse de secours"})()})()
        ]
        text, provider = generate_text([{"role": "user", "content": "test"}])
        self.assertEqual(text, "réponse de secours")
        self.assertEqual(provider, "huggingface")
