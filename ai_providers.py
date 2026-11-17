"""Fournisseurs IA interchangeables avec bascule automatique.

Les clés sont lues uniquement depuis l'environnement d'exécution.
Aucune clé n'est écrite dans les fichiers ou les journaux.
"""
import os


def generate_text(messages, max_tokens=1200, temperature=0.25, json_mode=False):
    """Essaie les fournisseurs configurés, sans rendre un fournisseur unique obligatoire."""
    failures = []
    groq_key = os.getenv("GROQ_API_KEY")
    hf_key = os.getenv("HF_API_KEY") or os.getenv("HF_TOKEN")
    order = (os.getenv("AI_PROVIDER_ORDER") or "groq,huggingface").split(",")

    for provider in [item.strip().lower() for item in order]:
        try:
            if provider == "groq" and groq_key:
                from groq import Groq
                kwargs = {}
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                client = Groq(api_key=groq_key, timeout=45, max_retries=1)
                result = client.chat.completions.create(
                    model=os.getenv("GROQ_MODEL") or "openai/gpt-oss-20b",
                    messages=messages,
                    temperature=temperature,
                    max_completion_tokens=max_tokens,
                    reasoning_effort="low",
                    **kwargs,
                )
                content = result.choices[0].message.content or ""
                if content.strip():
                    print("INFO : génération IA via Groq.")
                    return content, "groq"
                raise RuntimeError("réponse vide")

            if provider in ("huggingface", "hf") and hf_key:
                from huggingface_hub import InferenceClient
                client = InferenceClient(
                    model=os.getenv("HF_MODEL") or "Qwen/Qwen2.5-7B-Instruct",
                    token=hf_key,
                    timeout=60,
                )
                result = client.chat.completions.create(
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                content = result.choices[0].message.content or ""
                if content.strip():
                    print("INFO : génération IA via Hugging Face.")
                    return content, "huggingface"
                raise RuntimeError("réponse vide")
        except Exception as exc:  # noqa: BLE001 — exceptions variables selon le fournisseur IA.
            # Le journal ne contient ni clé, ni contenu de requête.
            failures.append(f"{provider}:{type(exc).__name__}")
            print(f"AVERTISSEMENT : fournisseur IA {provider} indisponible ({type(exc).__name__}).")

    raise RuntimeError(
        "Aucun fournisseur IA configuré n'a répondu. "
        "Vérifie les secrets et les quotas. Détails techniques : " + ", ".join(failures or ["aucune clé disponible"])
    )
