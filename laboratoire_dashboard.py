"""Interface privée locale pour la file de missions NEXORA.

Le serveur écoute uniquement sur 127.0.0.1 et n'est pas destiné à être publié.
"""
from __future__ import annotations

import argparse
import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

import atelier_creation
import atelier_produits
import roadmap_laboratoire
from gestionnaire_missions import MissionQueue

MAX_BODY_BYTES = 16_384
MAX_BATCH_MISSIONS = 3
PROJECTS_DIR = Path(__file__).resolve().parent / ".laboratoire_prive" / "prototypes"

PAGE = """<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>NEXORA — Laboratoire local</title><style>
body{margin:0;padding:18px;background:#f2f4ef;color:#172033;font:15px system-ui}main{max-width:950px;margin:auto}
section{background:white;border:1px solid #dce2d9;border-radius:12px;padding:17px;margin:14px 0}
.warning{background:#fff6e4;border-left:4px solid #b68b38;padding:10px}label{display:block;margin:10px 0 5px;font-weight:650}
input,textarea,select{box-sizing:border-box;width:100%;padding:9px;border:1px solid #cbd2c8;border-radius:7px;font:inherit}
textarea{min-height:70px}.grid{display:grid;grid-template-columns:2fr 1fr 1fr;gap:12px}.agents{display:flex;gap:14px;flex-wrap:wrap}.agents label{display:flex;align-items:center;gap:5px}.agents input{width:auto}
button{padding:9px 12px;border:0;border-radius:7px;background:#2f6243;color:white;font-weight:700;cursor:pointer;margin:4px}
button.secondary{background:#e8eee7;color:#294b34}.mission{border:1px solid #e0e5dd;border-radius:8px;padding:11px;margin:8px 0}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f6f2;padding:10px;border-radius:8px}
@media(max-width:650px){body{padding:9px}.grid{grid-template-columns:1fr}}
</style></head><body><main><h1>NEXORA · Laboratoire local</h1>
<p class="warning"><b>Privé et local :</b> ce tableau de bord écoute uniquement sur 127.0.0.1. Les missions produisent des analyses textuelles bornées ; aucun code généré n'est exécuté et aucun compte externe n'est piloté.</p>
<section><h2>Créer une mission</h2><form id="form">
<label>Objectif</label><textarea id="mission" maxlength="12000" required></textarea>
<label>Contexte facultatif</label><textarea id="context" maxlength="8000"></textarea>
<div class="grid"><div><label>Agents</label><div class="agents">
<label><input type="checkbox" name="agent" value="chercheur" checked>Chercheur</label>
<label><input type="checkbox" name="agent" value="critique" checked>Critique</label>
<label><input type="checkbox" name="agent" value="architecte" checked>Architecte</label><label><input type="checkbox" name="agent" value="redacteur">Rédacteur</label><label><input type="checkbox" name="agent" value="auditeur">Auditeur</label><label><input type="checkbox" name="agent" value="planificateur">Planificateur</label></div></div>
<div><label>Priorité</label><select id="priority"><option>low</option><option selected>normal</option><option>high</option><option>critical</option></select></div>
<div><label>Durée (s)</label><input id="duration" type="number" min="60" max="180" value="180"></div></div>
<label>Échéance facultative</label><input id="deadline" type="datetime-local"><button>Ajouter la mission</button><span id="form-status" role="status"></span></form></section>
<section><h2>File des missions</h2><button class="secondary" id="refresh">Actualiser</button><button id="run-next" type="button">Exécuter la prochaine mission</button><button id="run-batch" class="secondary" type="button">Exécuter jusqu’à 3 missions</button><span id="status" role="status"></span><div id="items"></div></section>
<section><h2>Atelier de création de projets</h2><p>Génère des squelettes de sites, applications, jeux web, logiciels Python, projets Godot 2D/3D, audio et vidéo. Le code est créé dans le dossier privé local ; il n'est jamais exécuté ni publié automatiquement.</p><form id="project-form"><label>Nom du projet</label><input id="project-name" maxlength="50" minlength="2" pattern="[A-Za-z][A-Za-z0-9_-]{1,49}" required><label>Modèle</label><select id="project-template"><option value="site">Site web</option><option value="webapp">Application web</option><option value="jeu-web">Jeu navigateur</option><option value="godot-2d">Godot 2D</option><option value="godot-3d">Godot 3D</option><option value="logiciel-python">Logiciel Python</option><option value="video">Production vidéo</option><option value="audio">Production audio</option></select><button type="submit">Créer le squelette</button><span id="project-status" role="status"></span></form></section>
<section><h2>Portefeuille R&D</h2>
<form id="product-form">
<label>Nom du produit</label><input id="product-name" maxlength="200" required>
<label>Problème à résoudre</label><textarea id="product-problem" maxlength="2000" required></textarea>
<label>Client cible</label><input id="product-customer" maxlength="200" required>
<label>Solution proposée</label><textarea id="product-solution" maxlength="2000" required></textarea>
<label>Type</label><select id="product-type"><option value="software">Logiciel</option><option value="developer_tool">Outil développeur</option><option value="ai_agent">Agent IA</option><option value="game_tool">Outil de jeu vidéo</option><option value="security_tool">Outil de sécurité</option><option value="hardware_research">Recherche matériel</option><option value="digital_service">Service numérique</option></select>
<label>Références de demande (une par ligne, facultatif)</label><textarea id="product-evidence" maxlength="4000"></textarea>
<p>Notes de 1 à 5 : douleur client, preuves de demande, faisabilité, différenciation, coût accessible, accès au marché.</p>
<div class="grid"><label>Douleur<input type="number" min="1" max="5" value="3" id="score-pain"></label><label>Demande<input type="number" min="1" max="5" value="3" id="score-demand"></label><label>Faisabilité<input type="number" min="1" max="5" value="3" id="score-feasibility"></label><label>Différenciation<input type="number" min="1" max="5" value="3" id="score-differentiation"></label><label>Coût<input type="number" min="1" max="5" value="3" id="score-affordability"></label><label>Marché<input type="number" min="1" max="5" value="3" id="score-market"></label></div>
<button type="submit">Enregistrer l'opportunité</button><span id="product-form-status" role="status"></span></form>
<hr><button class="secondary" id="refresh-products" type="button">Actualiser</button><span id="products-status" role="status"></span><div id="products"></div></section>
<section><h2>Feuille de route du projet</h2><p>Priorités conservées localement dans .laboratoire_prive, hors du dépôt et du site publics.</p><button class="secondary" id="refresh-roadmap" type="button">Actualiser</button><span id="roadmap-status" role="status"></span><div id="roadmap-items"></div></section><section><h2>Détail de la mission</h2><pre id="detail">Choisis une mission.</pre></section></main>
<script>
const TOKEN=__TOKEN__;
async function api(path,options={}){const headers={Authorization:"Bearer "+TOKEN,...(options.headers||{})};if(options.body)headers["Content-Type"]="application/json";const r=await fetch(path,{...options,headers,cache:"no-store"});const data=await r.json().catch(()=>({error:"Réponse invalide"}));if(!r.ok)throw Error(data.error||"HTTP "+r.status);return data;}
function el(tag,text,cls){const n=document.createElement(tag);n.textContent=text;if(cls)n.className=cls;return n;}
async function refreshProducts(){const box=document.getElementById("products"),status=document.getElementById("products-status");status.textContent="Chargement…";try{const rows=await api("/api/opportunities");box.replaceChildren();for(const item of rows){const card=el("article","","mission");card.append(el("b",item.name),el("span",item.score_percent+"/100 · "+item.decision));card.append(el("p",item.problem));const select=document.createElement("select");for(const value of ["candidate","research","prototype","validated","rejected"]){const option=el("option",value);option.value=value;option.selected=(item.workflow_status||"candidate")===value;select.append(option);}const save=el("button","Mettre à jour","secondary");save.onclick=async()=>{try{await api("/api/opportunities/"+encodeURIComponent(item.id)+"/status",{method:"POST",body:JSON.stringify({status:select.value})});await refreshProducts();}catch(e){status.textContent=e.message;}};card.append(select,save);box.append(card);}if(!rows.length)box.append(el("p","Aucune opportunité enregistrée dans le laboratoire."));status.textContent=rows.length+" opportunité(s)";}catch(e){status.textContent=e.message;}}

async function refreshRoadmap(){const box=document.getElementById("roadmap-items"),status=document.getElementById("roadmap-status");status.textContent="Chargement…";try{const rows=await api("/api/roadmap");box.replaceChildren();for(const row of rows){const card=el("article","","mission");card.append(el("b",row.title),el("p",row.description),el("span","Priorité : "+row.priority));const select=document.createElement("select");for(const value of ["backlog","in_progress","blocked","done"]){const option=el("option",value==="backlog"?"À faire":value==="in_progress"?"En cours":value==="blocked"?"Bloqué":"Terminé");option.value=value;option.selected=row.status===value;select.append(option);}const due=document.createElement("input");due.type="datetime-local";due.setAttribute("aria-label","Échéance");if(row.due_at){const date=new Date(row.due_at);due.value=new Date(date.getTime()-date.getTimezoneOffset()*60000).toISOString().slice(0,16);}const save=el("button","Enregistrer","secondary");save.onclick=async()=>{try{await api("/api/roadmap/"+encodeURIComponent(row.id)+"/status",{method:"POST",body:JSON.stringify({status:select.value,due_at:due.value?new Date(due.value).toISOString():""})});await refreshRoadmap();}catch(e){status.textContent=e.message;}};card.append(select,due,save);box.append(card);}status.textContent=rows.filter(x=>x.status==="done").length+"/"+rows.length+" tâches terminées";}catch(e){status.textContent=e.message;}}
async function refresh(){const status=document.getElementById("status"),items=document.getElementById("items");status.textContent="Chargement…";try{const rows=await api("/api/missions");items.replaceChildren();for(const row of rows){const card=el("article","","mission");card.append(el("b",row.id.slice(0,10)),el("span",row.status+" · "+row.priority+" · tentatives "+row.attempts+"/3"));if(row.due_at)card.append(el("p","Échéance : "+row.due_at));const detail=el("button","Détail","secondary");detail.onclick=async()=>{try{document.getElementById("detail").textContent=JSON.stringify(await api("/api/missions/"+row.id),null,2);}catch(e){document.getElementById("detail").textContent=e.message;}};card.append(detail);if(["pending","running"].includes(row.status)){const cancel=el("button","Annuler","secondary");cancel.onclick=async()=>{try{await api("/api/missions/"+row.id+"/cancel",{method:"POST",body:"{}"});refresh();}catch(e){status.textContent=e.message;}};card.append(cancel);}if(["failed","partial","interrupted"].includes(row.status)&&row.attempts<3){const retry=el("button","Relancer","secondary");retry.onclick=async()=>{try{await api("/api/missions/"+row.id+"/retry",{method:"POST",body:"{}"});refresh();}catch(e){status.textContent=e.message;}};card.append(retry);}items.append(card);}if(!rows.length)items.append(el("p","Aucune mission enregistrée."));status.textContent=rows.length+" mission(s)";}catch(e){status.textContent=e.message;}}
document.getElementById("project-form").onsubmit=async event=>{event.preventDefault();const status=document.getElementById("project-status");try{const result=await api("/api/projects",{method:"POST",body:JSON.stringify({name:document.getElementById("project-name").value,template:document.getElementById("project-template").value})});status.textContent="Projet créé : "+result.project_name+" · "+result.files.join(", ")+" · "+result.directory;event.target.reset();}catch(e){status.textContent=e.message;}};
document.getElementById("product-form").onsubmit=async event=>{event.preventDefault();const status=document.getElementById("product-form-status");const value=id=>document.getElementById(id).value;const payload={name:value("product-name"),problem:value("product-problem"),target_customer:value("product-customer"),proposed_solution:value("product-solution"),product_type:value("product-type"),evidence:value("product-evidence").split(String.fromCharCode(10)).map(x=>x.trim()).filter(Boolean),scores:{customer_pain:Number(value("score-pain")),demand_evidence:Number(value("score-demand")),feasibility:Number(value("score-feasibility")),differentiation:Number(value("score-differentiation")),affordability:Number(value("score-affordability")),market_access:Number(value("score-market"))}};try{const result=await api("/api/opportunities",{method:"POST",body:JSON.stringify(payload)});status.textContent="Opportunité enregistrée : "+result.id;event.target.reset();await refreshProducts();}catch(e){status.textContent=e.message;}};
document.getElementById("refresh").onclick=refresh;document.getElementById("refresh-products").onclick=refreshProducts;document.getElementById("refresh-roadmap").onclick=refreshRoadmap;document.getElementById("run-batch").onclick=async()=>{const status=document.getElementById("status");status.textContent="Lot borné en cours…";try{const result=await api("/api/worker/run-batch",{method:"POST",body:JSON.stringify({max_items:3})});status.textContent=result.processed+" mission(s) traitée(s) · "+result.status;await refresh();}catch(e){status.textContent=e.message;}};document.getElementById("run-next").onclick=async()=>{const status=document.getElementById("status");status.textContent="Exécution bornée en cours…";try{const result=await api("/api/worker/run-next",{method:"POST",body:"{}"});status.textContent=result.status||"Aucune mission en attente";await refresh();}catch(e){status.textContent=e.message;}};

document.getElementById("form").onsubmit=async event=>{event.preventDefault();const out=document.getElementById("form-status");const deadline=document.getElementById("deadline").value;const payload={mission:document.getElementById("mission").value,context:document.getElementById("context").value,agents:[...document.querySelectorAll('input[name="agent"]:checked')].map(x=>x.value),priority:document.getElementById("priority").value,max_duration_seconds:Number(document.getElementById("duration").value),due_at:deadline?new Date(deadline).toISOString():null};try{const result=await api("/api/missions",{method:"POST",body:JSON.stringify(payload)});out.textContent="Mission ajoutée : "+result.id.slice(0,10);event.target.reset();document.getElementById("duration").value="180";document.querySelectorAll('input[name="agent"]').forEach(x=>x.checked=true);refresh();}catch(e){out.textContent=e.message;}};
refresh();refreshProducts();refreshRoadmap();setInterval(()=>{refresh();refreshProducts();refreshRoadmap();},15000);
</script></body></html>"""


def create_server(port: int = 8765, queue: MissionQueue | None = None, token: str | None = None):
    if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValueError("Port invalide.")
    mission_queue = queue or MissionQueue()
    access_token = token or secrets.token_urlsafe(32)

    class Handler(BaseHTTPRequestHandler):
        server_version = "NEXORA-local"
        sys_version = ""

        def log_message(self, _format, *_args):
            return

        def send_data(self, status, body, content_type="application/json; charset=utf-8"):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def send_json(self, status, value):
            self.send_data(status, json.dumps(value, ensure_ascii=False).encode(), "application/json; charset=utf-8")

        def authorized(self):
            value = self.headers.get("Authorization", "")
            return value.startswith("Bearer ") and secrets.compare_digest(value[7:], access_token)

        def valid_origin(self):
            origin = self.headers.get("Origin")
            return not origin or secrets.compare_digest(origin.rstrip("/"), f"http://127.0.0.1:{self.server.server_port}")

        def read_json(self):
            size = self.headers.get("Content-Length", "")
            if not size.isdigit() or not 1 <= int(size) <= MAX_BODY_BYTES:
                raise ValueError("Taille de requête invalide.")
            return json.loads(self.rfile.read(int(size)).decode("utf-8"))

        def do_GET(self):
            if self.path == "/":
                body = PAGE.replace("__TOKEN__", json.dumps(access_token)).encode()
                self.send_data(200, body, "text/html; charset=utf-8")
                return
            if not self.authorized():
                self.send_json(401, {"error": "Authentification locale requise."})
                return
            if self.path == "/api/templates":
                labels = {
                    "site": "Site web", "webapp": "Application web", "jeu-web": "Jeu navigateur",
                    "godot-2d": "Godot 2D", "godot-3d": "Godot 3D",
                    "logiciel-python": "Logiciel Python", "video": "Production vidéo", "audio": "Production audio",
                }
                self.send_json(200, [{"id": key, "label": labels.get(key, key)} for key in atelier_creation.TEMPLATES])
                return
            if self.path == "/api/missions":
                self.send_json(200, mission_queue.list_missions())
                return
            if self.path == "/api/opportunities":
                self.send_json(200, atelier_produits.list_opportunities(atelier_produits.DEFAULT_PRODUCTS_DIR))
                return
            if self.path == "/api/roadmap":
                self.send_json(200, roadmap_laboratoire.list_tasks())
                return
            if self.path.startswith("/api/missions/"):
                mission_id = unquote(self.path.removeprefix("/api/missions/"))
                item = mission_queue.get_mission(mission_id) if "/" not in mission_id else None
                self.send_json(200 if item else 404, item or {"error": "Mission introuvable."})
                return
            self.send_json(404, {"error": "Route introuvable."})

        def do_POST(self):
            if not self.authorized():
                self.send_json(401, {"error": "Authentification locale requise."})
                return
            if not self.valid_origin():
                self.send_json(403, {"error": "Origine refusée."})
                return
            try:
                body = self.read_json()
                if not isinstance(body, dict):
                    raise ValueError("Le corps JSON doit être un objet.")
                if self.path == "/api/projects":
                    name = body.get("name")
                    template = body.get("template")
                    if not isinstance(name, str) or not isinstance(template, str):
                        raise ValueError("Nom et modèle de projet obligatoires.")
                    private_root = PROJECTS_DIR.parent
                    if private_root.is_symlink() or PROJECTS_DIR.is_symlink():
                        raise ValueError("Le dossier privé de projets ne peut pas être un lien symbolique.")
                    result = atelier_creation.generate_project(name, PROJECTS_DIR, template)
                    self.send_json(201, result)
                    return
                if self.path == "/api/missions":
                    mission_id = mission_queue.enqueue(body)
                    self.send_json(201, {"id": mission_id, "status": "pending"})
                    return
                if self.path == "/api/opportunities":
                    report = atelier_produits.evaluate_opportunity(body)
                    atelier_produits.save_opportunity(report, atelier_produits.DEFAULT_PRODUCTS_DIR)
                    self.send_json(201, {"id": report["id"], "score_percent": report["score_percent"], "decision": report["decision"]})
                    return
                if self.path.startswith("/api/roadmap/") and self.path.endswith("/status"):
                    task_id = unquote(self.path[len("/api/roadmap/"):-len("/status")].strip("/"))
                    if "/" in task_id:
                        self.send_json(404, {"error": "Tâche introuvable."})
                        return
                    task = roadmap_laboratoire.update_status(
                        roadmap_laboratoire.DEFAULT_ROADMAP_PATH,
                        task_id,
                        body.get("status"),
                        body.get("due_at"),
                    )
                    self.send_json(200, task)
                    return
                if self.path.startswith("/api/opportunities/") and self.path.endswith("/status"):
                    opportunity_id = unquote(self.path[len("/api/opportunities/"):-len("/status")].strip("/"))
                    if "/" in opportunity_id:
                        self.send_json(404, {"error": "Opportunité introuvable."})
                        return
                    report = atelier_produits.update_opportunity_status(
                        atelier_produits.DEFAULT_PRODUCTS_DIR,
                        opportunity_id,
                        body.get("status"),
                        body.get("note"),
                    )
                    self.send_json(200, {"id": report["id"], "workflow_status": report["workflow_status"]})
                    return
                if self.path == "/api/worker/run-next":
                    result = mission_queue.run_next()
                    self.send_json(200, result or {"status": "idle"})
                    return
                if self.path == "/api/worker/run-batch":
                    maximum = body.get("max_items", MAX_BATCH_MISSIONS)
                    if isinstance(maximum, bool) or not isinstance(maximum, int) or not 1 <= maximum <= MAX_BATCH_MISSIONS:
                        self.send_json(400, {"error": "Le lot doit contenir entre 1 et 3 missions."})
                        return
                    results = []
                    for _ in range(maximum):
                        result = mission_queue.run_next()
                        if result is None:
                            break
                        results.append(result)
                        if result.get("status") != "completed":
                            break
                    self.send_json(200, {
                        "processed": len(results),
                        "status": results[-1].get("status") if results else "idle",
                        "results": results,
                    })
                    return
                if self.path.startswith("/api/missions/") and self.path.endswith("/retry"):
                    mission_id = unquote(self.path[len("/api/missions/"):-len("/retry")].strip("/"))
                    if "/" not in mission_id and mission_queue.retry(mission_id):
                        self.send_json(200, {"requeued": True})
                    else:
                        self.send_json(409, {"requeued": False})
                    return
                if self.path.startswith("/api/missions/") and self.path.endswith("/cancel"):
                    mission_id = unquote(self.path[len("/api/missions/"):-len("/cancel")].strip("/"))
                    if "/" not in mission_id and mission_queue.cancel(mission_id):
                        self.send_json(200, {"cancelled": True})
                    else:
                        self.send_json(409, {"cancelled": False})
                    return
                self.send_json(404, {"error": "Route introuvable."})
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                self.send_json(400, {"error": str(exc)[:200]})

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    server.nexora_token = access_token
    return server


def main() -> int:
    parser = argparse.ArgumentParser(description="Tableau de bord privé, local uniquement.")
    parser.add_argument("--port", type=int, default=8765)
    server = create_server(parser.parse_args().port)
    print(f"Tableau de bord local : http://127.0.0.1:{server.server_port}/")
    print("Arrête le serveur avec Ctrl+C ; l'adresse d'écoute reste 127.0.0.1.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt demandé.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
