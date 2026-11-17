"""Générateur local de squelette Roblox Studio (prototype Rojo).

Le générateur écrit des fichiers Luau statiques ; il ne lance aucun code,
ne se connecte pas à Roblox et ne publie aucun jeu.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TEMPLATES = {"obby"}
FILES = {
    "default.project.json": """{
  "name": "__PROJECT_NAME__",
  "tree": {
    "$className": "DataModel",
    "ReplicatedStorage": {
      "$className": "ReplicatedStorage",
      "Shared": { "$path": "src/shared" }
    },
    "ServerScriptService": {
      "$className": "ServerScriptService",
      "$path": "src/server"
    },
    "StarterPlayer": {
      "$className": "StarterPlayer",
      "StarterPlayerScripts": {
        "$className": "StarterPlayerScripts",
        "$path": "src/client"
      }
    }
  }
}
""",
    "src/shared/Config.lua": """-- Configuration partagée : ne place jamais de secret ici.
return {
    StartingCoins = 0,
    CoinReward = 1,
    CoinRespawnSeconds = 8,
}
""",
    "src/server/PlayerSetup.server.lua": """-- Les statistiques et la monnaie sont créées et contrôlées côté serveur.
local Players = game:GetService("Players")
local Config = require(game:GetService("ReplicatedStorage"):WaitForChild("Shared"):WaitForChild("Config"))

local function setupPlayer(player)
    if player:FindFirstChild("leaderstats") then
        return
    end

    local leaderstats = Instance.new("Folder")
    leaderstats.Name = "leaderstats"

    local coins = Instance.new("IntValue")
    coins.Name = "Coins"
    coins.Value = Config.StartingCoins
    coins.Parent = leaderstats

    leaderstats.Parent = player
end

Players.PlayerAdded:Connect(setupPlayer)
for _, player in Players:GetPlayers() do
    setupPlayer(player)
end
""",
    "src/server/CoinPickup.server.lua": """-- Ajouter le tag CollectionService "CoinPickup" aux pièces dans Roblox Studio.
-- Le serveur valide le personnage et modifie lui-même le compteur.
local Players = game:GetService("Players")
local CollectionService = game:GetService("CollectionService")
local Config = require(game:GetService("ReplicatedStorage"):WaitForChild("Shared"):WaitForChild("Config"))

local function connectCoin(coin)
    if not coin:IsA("BasePart") or coin:GetAttribute("CoinHandlerReady") then
        return
    end
    coin:SetAttribute("CoinHandlerReady", true)

    coin.Touched:Connect(function(hit)
        if coin:GetAttribute("Collected") then
            return
        end
        local character = hit:FindFirstAncestorOfClass("Model")
        local player = character and Players:GetPlayerFromCharacter(character)
        if not player then
            return
        end
        local stats = player:FindFirstChild("leaderstats")
        local coins = stats and stats:FindFirstChild("Coins")
        if not coins or not coins:IsA("IntValue") then
            return
        end

        coin:SetAttribute("Collected", true)
        coins.Value += math.max(0, math.floor(Config.CoinReward))
        task.delay(Config.CoinRespawnSeconds, function()
            if coin.Parent then
                coin:SetAttribute("Collected", false)
            end
        end)
    end)
end

for _, coin in CollectionService:GetTagged("CoinPickup") do
    connectCoin(coin)
end
CollectionService:GetInstanceAddedSignal("CoinPickup"):Connect(connectCoin)
""",
    "src/client/ClientStatus.client.lua": """-- Exemple de point d'entrée client. Aucune monnaie ou donnée sensible n'est modifiée ici.
print("Starter Obby : scripts client initialisés.")
""",
    "README.md": """# __PROJECT_NAME__

Squelette de jeu Roblox de type obby, généré localement.

## Contenu
- src/server/PlayerSetup.server.lua : crée les statistiques joueur côté serveur.
- src/server/CoinPickup.server.lua : attribue les pièces côté serveur aux joueurs qui touchent une pièce taguée CoinPickup.
- src/shared/Config.lua : paramètres du jeu.
- src/client/ClientStatus.client.lua : point d'entrée client minimal.
- default.project.json : configuration de synchronisation Rojo.

## Ouvrir dans Roblox Studio
1. Installer Roblox Studio et l'outil open source Rojo depuis leurs sources officielles.
2. Installer le plugin Rojo dans Roblox Studio.
3. Depuis ce dossier, lancer la commande : rojo serve
4. Dans Roblox Studio, connecter le plugin Rojo au serveur local.
5. Construire les plateformes et ajouter le tag CoinPickup aux pièces via l'éditeur de tags.

Le générateur ne se connecte pas à un compte Roblox et ne publie rien. Il produit uniquement un squelette de fichiers. Tester dans une expérience privée avant tout partage.
"""
}


def project_slug(name: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Le nom du projet est obligatoire.")
    slug = re.sub(r"[^A-Za-z0-9_]+", "_", name.strip()).strip("_")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{1,39}", slug):
        raise ValueError("Nom invalide : utilise 2 à 40 caractères, lettres/chiffres/underscore, en commençant par une lettre.")
    return slug


def generate_project(name: str, output_dir: str | Path, template: str = "obby") -> dict:
    slug = project_slug(name)
    if template not in TEMPLATES:
        raise ValueError("Modèle inconnu.")
    root = Path(output_dir).expanduser().resolve()
    destination = root / slug
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError("Le dossier de destination existe déjà et n'est pas vide.")
    destination.mkdir(parents=True, exist_ok=True)

    created = []
    for relative, template_text in FILES.items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        text = template_text.replace("__PROJECT_NAME__", slug)
        target.write_text(text, encoding="utf-8")
        created.append(relative)

    json.loads((destination / "default.project.json").read_text(encoding="utf-8"))
    return {
        "project_name": slug,
        "template": template,
        "directory": str(destination),
        "files": created,
        "code_executed": False,
        "roblox_account_accessed": False,
        "game_published": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Générer un squelette de projet Roblox Studio.")
    parser.add_argument("name", help="Nom du projet")
    parser.add_argument("--output", default=".laboratoire_prive/prototypes", help="Dossier local de sortie")
    parser.add_argument("--template", default="obby", choices=sorted(TEMPLATES))
    args = parser.parse_args()
    result = generate_project(args.name, args.output, args.template)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
