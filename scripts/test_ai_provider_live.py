"""Test réel isolé d'un fournisseur IA, sans publication et sans afficher la réponse."""
import os

from ai_providers import generate_text


def main() -> int:
    provider = (os.getenv("TEST_PROVIDER") or "").strip().lower()
    if provider not in {"groq", "huggingface"}:
        raise SystemExit("TEST_PROVIDER doit être groq ou huggingface.")

    os.environ["AI_PROVIDER_ORDER"] = provider
    prompt = [{"role": "user", "content": "Réponds uniquement par le mot OK."}]
    answer, used_provider = generate_text(prompt, max_tokens=20, temperature=0)
    if not answer.strip() or used_provider != provider:
        raise SystemExit(f"Échec du test réel pour {provider}.")
    print(f"TEST RÉEL RÉUSSI : {provider}; réponse non vide; contenu non journalisé.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
