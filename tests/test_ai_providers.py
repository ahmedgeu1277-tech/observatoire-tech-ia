import os
import unittest
from unittest.mock import patch

from ai_providers import generate_text


class AIProviderTests(unittest.TestCase):
    @patch.dict(os.environ, {"GROQ_API_KEY": "", "HF_API_KEY": "", "HF_TOKEN": ""}, clear=False)
    def test_no_keys_fails_without_leaking_secrets(self):
        with self.assertRaisesRegex(RuntimeError, "Aucun fournisseur IA"):
            generate_text([{"role": "user", "content": "test"}])

    def test_rejects_non_positive_timeout(self):
        for timeout in (0, -1, float("nan"), float("inf"), True):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                generate_text([], timeout=timeout)

    def test_rejects_invalid_max_tokens(self):
        for value in (0, -1, 1.5, True):
            with self.subTest(max_tokens=value), self.assertRaises(ValueError):
                generate_text([], max_tokens=value)

    def test_rejects_unknown_provider_order(self):
        with patch.dict(os.environ, {"AI_PROVIDER_ORDER": "groq,unknown"}):
            with self.assertRaisesRegex(ValueError, "AI_PROVIDER_ORDER"):
                generate_text([])

    def test_rejects_empty_provider_order(self):
        with patch.dict(os.environ, {"AI_PROVIDER_ORDER": " , "}):
            with self.assertRaisesRegex(ValueError, "AI_PROVIDER_ORDER"):
                generate_text([])

    def test_order_is_configurable(self):
        with patch.dict(os.environ, {
            "AI_PROVIDER_ORDER": "huggingface,groq",
            "GROQ_API_KEY": "fake-groq",
            "HF_API_KEY": "fake-hf",
        }):
            self.assertEqual(os.environ["AI_PROVIDER_ORDER"], "huggingface,groq")

    @patch("groq.Groq")
    @patch("huggingface_hub.InferenceClient")
    @patch.dict(os.environ, {
        "GROQ_API_KEY": "test-groq",
        "HF_API_KEY": "test-hf",
        "HF_TOKEN": "",
        "AI_PROVIDER_ORDER": "groq,huggingface",
    }, clear=False)
    def test_huggingface_is_used_when_groq_fails(self, mock_hf, mock_groq):
        mock_groq.return_value.chat.completions.create.side_effect = RuntimeError("provider down")
        mock_hf.return_value.chat.completions.create.return_value.choices = [
            type("Choice", (), {"message": type("Message", (), {"content": "réponse de secours"})()})()
        ]
        generated, provider = generate_text([{"role": "user", "content": "test"}])
        self.assertEqual(generated, "réponse de secours")
        self.assertEqual(provider, "huggingface")
        mock_hf.assert_called_once()

    @patch("groq.Groq")
    @patch.dict(os.environ, {
        "GROQ_API_KEY": "test-groq",
        "HF_API_KEY": "",
        "HF_TOKEN": "",
        "AI_PROVIDER_ORDER": "groq",
    }, clear=False)
    def test_groq_returns_provider_name(self, mock_groq):
        mock_groq.return_value.chat.completions.create.return_value.choices = [
            type("Choice", (), {"message": type("Message", (), {"content": "réponse Groq"})()})()
        ]
        generated, provider = generate_text([{"role": "user", "content": "test"}])
        self.assertEqual(generated, "réponse Groq")
        self.assertEqual(provider, "groq")


if __name__ == "__main__":
    unittest.main()
