"""Atelier de démarrage multi-format : web, jeu web, vidéo, audio et logiciel Python.

Produit des squelettes lisibles ; n'exécute aucun code et ne publie rien.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TEMPLATES: dict[str, dict[str, str]] = {
    "site": {
        "index.html": """<!doctype html>
<html lang="fr">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__NAME__</title><link rel="stylesheet" href="style.css"></head>
<body><main><h1>__NAME__</h1><p>Votre site commence ici.</p></main></body>
</html>
""",
        "style.css": """* { box-sizing: border-box; }
body { margin: 0; font: 1rem/1.5 system-ui, sans-serif; color: #172033; }
main { width: min(100% - 2rem, 70rem); margin: 4rem auto; }
""",
        "README.md": "# __NAME__\n\nSite web statique de départ. Vérifier les liens, l'accessibilité et l'affichage mobile avant publication.\n",
    },
    "webapp": {
        "index.html": """<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__NAME__</title><link rel="stylesheet" href="style.css"></head>
<body><main><h1>__NAME__</h1><button id="action" type="button">Tester l'application</button><output id="result" aria-live="polite"></output></main>
<script type="module" src="app.js"></script></body></html>
""",
        "style.css": "body { font: 1rem system-ui; margin: 2rem; } main { max-width: 48rem; margin: auto; } button { padding: .7rem 1rem; }\n",
        "app.js": """const button = document.querySelector("#action");
const output = document.querySelector("#result");
button.addEventListener("click", () => { output.textContent = "Application initialisée."; });
""",
        "README.md": "# __NAME__\n\nApplication web front-end de départ. Toute authentification, donnée privée et limitation par IP nécessite un backend ou un service edge ; ne jamais placer de secret dans le navigateur.\n",
    },
    "jeu-web": {
        "index.html": """<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__NAME__</title><link rel="stylesheet" href="style.css"></head><body><main><h1>__NAME__</h1><p>Déplace le carré avec les flèches.</p><canvas id="game" width="640" height="360" aria-label="Zone de jeu"></canvas></main><script src="game.js" defer></script></body></html>
""",
        "style.css": "body { margin: 1rem; font: 1rem system-ui; } canvas { display: block; max-width: 100%; height: auto; border: 1px solid; }\n",
        "game.js": """const canvas = document.querySelector("#game");
const ctx = canvas.getContext("2d");
const player = { x: 40, y: 40, size: 24 };
const keys = new Set();
addEventListener("keydown", event => keys.add(event.key));
addEventListener("keyup", event => keys.delete(event.key));
function frame() {
  if (keys.has("ArrowLeft")) player.x -= 2;
  if (keys.has("ArrowRight")) player.x += 2;
  if (keys.has("ArrowUp")) player.y -= 2;
  if (keys.has("ArrowDown")) player.y += 2;
  player.x = Math.max(0, Math.min(canvas.width - player.size, player.x));
  player.y = Math.max(0, Math.min(canvas.height - player.size, player.y));
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillRect(player.x, player.y, player.size, player.size);
  requestAnimationFrame(frame);
}
frame();
""",
        "README.md": "# __NAME__\n\nPrototype de jeu 2D navigateur minimal. Ce n'est pas un moteur complet ; ajouter collisions, sons, niveaux et tests de gameplay.\n",
    },
    "godot-2d": {
        "project.godot": """config_version=5

[application]
config/name="__NAME__"
run/main_scene="res://scenes/main.tscn"

[display]
window/size/viewport_width=960
window/size/viewport_height=540

[rendering]
renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
""",
        "scenes/main.tscn": """[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/main.gd" id="1"]

[node name="Main" type="Node2D"]
script = ExtResource("1")
""",
        "scripts/main.gd": """extends Node2D

var player_position := Vector2(480, 270)
const SPEED := 260.0

func _process(delta: float) -> void:
    player_position += Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down") * SPEED * delta
    player_position.x = clampf(player_position.x, 20.0, 940.0)
    player_position.y = clampf(player_position.y, 20.0, 520.0)
    queue_redraw()

func _draw() -> void:
    draw_circle(player_position, 18.0, Color(0.32, 0.65, 0.48))
    draw_string(ThemeDB.fallback_font, Vector2(24, 36), "Move with arrow keys", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color(0.14, 0.21, 0.17))
""",
        "README.md": """# __NAME__ — Godot 2D

Prototype minimal pour Godot 4. Ouvre ce dossier dans Godot Engine, puis lance scenes/main.tscn.
Le carré se déplace avec les flèches. Le modèle ne télécharge pas le moteur, n'exécute aucun code ici et ne publie rien.
Godot est un moteur libre ; la compilation et les tests de jeu doivent être effectués dans Godot.
"""
    },
    "godot-3d": {
        "project.godot": """config_version=5

[application]
config/name="__NAME__"
run/main_scene="res://scenes/main.tscn"

[display]
window/size/viewport_width=960
window/size/viewport_height=540

[rendering]
renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
""",
        "scenes/main.tscn": """[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/main.gd" id="1"]

[node name="Main" type="Node3D"]
script = ExtResource("1")
""",
        "scripts/main.gd": """extends Node3D

var cube: MeshInstance3D

func _ready() -> void:
    cube = MeshInstance3D.new()
    var mesh := BoxMesh.new()
    mesh.size = Vector3.ONE
    var material := StandardMaterial3D.new()
    material.albedo_color = Color(0.32, 0.65, 0.48)
    mesh.material = material
    cube.mesh = mesh
    add_child(cube)

    var camera := Camera3D.new()
    camera.position = Vector3(3.2, 2.6, 4.2)
    camera.look_at(Vector3.ZERO)
    add_child(camera)
    camera.current = true

    var light := DirectionalLight3D.new()
    light.rotation_degrees = Vector3(-45, -30, 0)
    add_child(light)

func _process(delta: float) -> void:
    if is_instance_valid(cube):
        cube.rotate_y(delta * 0.7)
""",
        "README.md": """# __NAME__ — Godot 3D

Prototype 3D minimal pour Godot 4. Ouvre ce dossier dans Godot Engine, puis lance scenes/main.tscn.
Une boîte 3D tourne devant une caméra et une lumière directionnelle. Le modèle ne télécharge pas le moteur, n'exécute aucun code ici et ne publie rien.
Godot est un moteur libre ; la compilation et les tests de jeu doivent être effectués dans Godot.
"""
    },
    "video": {
        "README.md": "# __NAME__ — dossier de production vidéo\n\nCe modèle prépare le travail éditorial ; il ne rend pas de fichier vidéo.\n",
        "concept.md": "# Concept\n\n- Public cible :\n- Sujet :\n- Durée visée :\n- Format et résolution :\n- Sources et droits :\n",
        "storyboard.md": "# Storyboard\n\n| Temps | Image / plan | Voix / texte | Son | Ressources et droits |\n|---|---|---|---|---|\n| 00:00 | Introduction | | | |\n",
        "script.md": "# Script\n\n[Introduction]\n\n[Partie 1]\n\n[Conclusion]\n",
    },
    "audio": {
        "README.md": "# __NAME__ — dossier de production audio\n\nPréparation éditoriale uniquement ; aucun enregistrement ni synthèse vocale n'est lancé.\n",
        "script.md": "# Script audio\n\n- Public :\n- Durée cible :\n- Ton :\n- Sources :\n\n[Introduction]\n\n[Développement]\n\n[Conclusion]\n",
        "mixage.md": "# Plan audio\n\n- Voix :\n- Musique autorisée :\n- Effets sonores autorisés :\n- Niveau et normalisation :\n- Vérification des droits :\n",
    },
    "logiciel-python": {
        "main.py": '"""Point d’entrée de __NAME__."""\n\ndef main() -> int:\n    print("Projet initialisé : __NAME__")\n    return 0\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n',
        "tests/test_smoke.py": "import unittest\n\nclass SmokeTests(unittest.TestCase):\n    def test_project_has_entrypoint(self):\n        from pathlib import Path\n        self.assertTrue(Path('main.py').is_file())\n\nif __name__ == '__main__':\n    unittest.main()\n",
        "README.md": "# __NAME__\n\nLogiciel Python de départ. Installer les dépendances explicitement, ajouter des tests et examiner le code avant exécution.\n",
    },
}


def project_slug(name: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Le nom du projet est obligatoire.")
    if "/" in name or chr(92) in name or ".." in name:
        raise ValueError("Le nom ne doit pas contenir de chemin ou de séquence de traversée.")
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", name.strip()).strip("-_")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{1,49}", slug):
        raise ValueError("Nom invalide : 2 à 50 caractères, commencer par une lettre.")
    return slug


def generate_project(name: str, output_dir: str | Path, template: str) -> dict:
    slug = project_slug(name)
    if template not in TEMPLATES:
        raise ValueError("Modèle inconnu. Modèles : " + ", ".join(sorted(TEMPLATES)))
    raw_root = Path(output_dir).expanduser()
    if raw_root.exists() and raw_root.is_symlink():
        raise ValueError("Le dossier racine ne peut pas être un lien symbolique.")
    root = raw_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    destination = root / slug
    if destination.is_symlink() or (destination.exists() and (not destination.is_dir() or any(destination.iterdir()))):
        raise FileExistsError("Dossier de destination non vide, lien symbolique ou fichier.")
    destination.mkdir(parents=True, exist_ok=True)
    created = []
    for relative, template_text in TEMPLATES[template].items():
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() or target.is_symlink():
            raise FileExistsError("Un fichier cible existe déjà : " + relative)
        target.write_text(template_text.replace("__NAME__", slug), encoding="utf-8")
        created.append(relative)
    return {"project_name": slug, "template": template, "directory": str(destination),
            "files": created, "code_executed": False, "published": False}


def main() -> int:
    parser = argparse.ArgumentParser(description="Créer un squelette de site, application, jeu web, vidéo, audio ou logiciel.")
    parser.add_argument("name")
    parser.add_argument("--type", choices=sorted(TEMPLATES), required=True)
    parser.add_argument("--output", default=".laboratoire_prive/prototypes")
    args = parser.parse_args()
    print(json.dumps(generate_project(args.name, args.output, args.type), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
