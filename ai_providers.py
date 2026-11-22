"""Fournisseurs IA interchangeables avec bascule automatique.

Les clés sont lues uniquement depuis l'environnement d'exécution.
Aucune clé n'est écrite dans les fichiers ou les journaux.
"""
import math
import os


def generate_text(messages, max_tokens=1200, temperature=0.25, json_mode=False, timeout=60):
    """Essaie les fournisseurs configurés, sans rendre un fournisseur unique obligatoire."""
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Le délai timeout doit être un nombre fini strictement positif.")
    if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or max_tokens < 1:
        raise ValueError("max_tokens doit être un entier strictement positif.")
    failures = []
    groq_key = os.getenv("GROQ_API_KEY")
    hf_key = os.getenv("HF_API_KEY") or os.getenv("HF_TOKEN")
    order = (os.getenv("AI_PROVIDER_ORDER") or "groq,huggingface").split(",")

    providers = list(dict.fromkeys(item.strip().lower() for item in order if item.strip()))
    allowed_providers = {"groq", "huggingface", "hf"}
    unknown = sorted(set(providers) - allowed_providers)
    if unknown or not providers:
        raise ValueError("AI_PROVIDER_ORDER doit contenir groq et/ou huggingface, séparés par des virgules.")
    provider_timeout = max(0.1, timeout / len(providers))
    for provider in providers:
        try:
            if provider == "groq" and groq_key:
                from groq import Groq
                kwargs = {}
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                client = Groq(api_key=groq_key, timeout=provider_timeout, max_retries=0)
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
                    model=os.getenv("HF_MODEL") or "Qwen/Qwen2.5-72B-Instruct",
                    api_key=hf_key,
                    timeout=provider_timeout,
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
            status_code = getattr(exc, "status_code", None)
            detail = f"{type(exc).__name__}:{status_code}" if status_code else type(exc).__name__
            # Extraire uniquement le champ d'erreur serveur, jamais les en-têtes,
            # jetons, requêtes complètes ou réponses générées.
            response = getattr(exc, "response", None)
            if response is not None:
                try:
                    payload = response.json()
                    message = payload.get("error") or payload.get("message") if isinstance(payload, dict) else None
                    if message:
                        message = str(message)
                        for secret in (groq_key, hf_key):
                            if secret:
                                message = message.replace(secret, "[SECRET MASQUÉ]")
                        detail += ":" + message[:180]
                except (ValueError, TypeError, AttributeError):
                    detail += ":response_parse_failed"
            failures.append(f"{provider}:{detail}")
            print(f"AVERTISSEMENT : fournisseur IA {provider} indisponible ({detail}).")

    raise RuntimeError(
        "Aucun fournisseur IA configuré n'a répondu. "
        "Vérifie les secrets et les quotas. Détails techniques : " + ", ".join(failures or ["aucune clé disponible"])
    )
