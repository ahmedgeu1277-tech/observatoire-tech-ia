"""Interface privée locale pour la file de missions NEXORA.

Le serveur écoute uniquement sur 127.0.0.1 et n'est pas destiné à être publié.
"""
from __future__ import annotations

import argparse
import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote

import atelier_produits\nfrom gestionnaire_missions import MissionQueue

MAX_BODY_BYTES = 16_384

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
<label><input type="checkbox" name="agent" value="architecte" checked>Architecte</label></div></div>
<div><label>Priorité</label><select id="priority"><option>low</option><option selected>normal</option><option>high</option><option>critical</option></select></div>
<div><label>Durée (s)</label><input id="duration" type="number" min="60" max="180" value="180"></div></div>
<label>Échéance facultative</label><input id="deadline" type="datetime-local"><button>Ajouter la mission</button><span id="form-status" role="status"></span></form></section>
<section><h2>File des missions</h2><button class="secondary" id="refresh">Actualiser</button><button id="run-next" type="button">Exécuter la prochaine mission</button><span id="status" role="status"></span><div id="items"></div></section>
<section><h2>Portefeuille R&D</h2><button class="secondary" id="refresh-products" type="button">Actualiser</button><span id="products-status" role="status"></span><div id="products"></div></section>
<section><h2>Détail de la mission</h2><pre id="detail">Choisis une mission.</pre></section></main>
<script>
const TOKEN=__TOKEN__;
async function api(path,options={}){const headers={Authorization:"Bearer "+TOKEN,...(options.headers||{})};if(options.body)headers["Content-Type"]="application/json";const r=await fetch(path,{...options,headers,cache:"no-store"});const data=await r.json().catch(()=>({error:"Réponse invalide"}));if(!r.ok)throw Error(data.error||"HTTP "+r.status);return data;}
function el(tag,text,cls){const n=document.createElement(tag);n.textContent=text;if(cls)n.className=cls;return n;}
async function refreshProducts(){const box=document.getElementById("products"),status=document.getElementById("products-status");status.textContent="Chargement…";try{const rows=await api("/api/opportunities");box.replaceChildren();for(const item of rows){const card=el("article","","mission");card.append(el("b",item.name),el("span",item.score_percent+"/100 · "+item.decision));card.append(el("p",item.problem));const select=document.createElement("select");for(const value of ["candidate","research","prototype","validated","rejected"]){const option=el("option",value);option.value=value;option.selected=(item.workflow_status||"candidate")===value;select.append(option);}const save=el("button","Mettre à jour","secondary");save.onclick=async()=>{try{await api("/api/opportunities/"+encodeURIComponent(item.id)+"/status",{method:"POST",body:JSON.stringify({status:select.value})});await refreshProducts();}catch(e){status.textContent=e.message;}};card.append(select,save);box.append(card);}if(!rows.length)box.append(el("p","Aucune opportunité enregistrée dans le laboratoire."));status.textContent=rows.length+" opportunité(s)";}catch(e){status.textContent=e.message;}}

async function refresh(){const status=document.getElementById("status"),items=document.getElementById("items");status.textContent="Chargement…";try{const rows=await api("/api/missions");items.replaceChildren();for(const row of rows){const card=el("article","","mission");card.append(el("b",row.id.slice(0,10)),el("span",row.status+" · "+row.priority));if(row.due_at)card.append(el("p","Échéance : "+row.due_at));const detail=el("button","Détail","secondary");detail.onclick=async()=>{try{document.getElementById("detail").textContent=JSON.stringify(await api("/api/missions/"+row.id),null,2);}catch(e){document.getElementById("detail").textContent=e.message;}};card.append(detail);if(["pending","running"].includes(row.status)){const cancel=el("button","Annuler","secondary");cancel.onclick=async()=>{try{await api("/api/missions/"+row.id+"/cancel",{method:"POST",body:"{}"});refresh();}catch(e){status.textContent=e.message;}};card.append(cancel);}items.append(card);}if(!rows.length)items.append(el("p","Aucune mission enregistrée."));status.textContent=rows.length+" mission(s)";}catch(e){status.textContent=e.message;}}
document.getElementById("refresh").onclick=refresh;document.getElementById("refresh-products").onclick=refreshProducts;document.getElementById("run-next").onclick=async()=>{const status=document.getElementById("status");status.textContent="Exécution bornée en cours…";try{const result=await api("/api/worker/run-next",{method:"POST",body:"{}"});status.textContent=result.status||"Aucune mission en attente";await refresh();}catch(e){status.textContent=e.message;}};

document.getElementById("form").onsubmit=async event=>{event.preventDefault();const out=document.getElementById("form-status");const deadline=document.getElementById("deadline").value;const payload={mission:document.getElementById("mission").value,context:document.getElementById("context").value,agents:[...document.querySelectorAll('input[name="agent"]:checked')].map(x=>x.value),priority:document.getElementById("priority").value,max_duration_seconds:Number(document.getElementById("duration").value),due_at:deadline?new Date(deadline).toISOString():null};try{const result=await api("/api/missions",{method:"POST",body:JSON.stringify(payload)});out.textContent="Mission ajoutée : "+result.id.slice(0,10);event.target.reset();document.getElementById("duration").value="180";document.querySelectorAll('input[name="agent"]').forEach(x=>x.checked=true);refresh();}catch(e){out.textContent=e.message;}};
refresh();refreshProducts();setInterval(()=>{refresh();refreshProducts();},15000);
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
            if self.path == "/api/missions":
                self.send_json(200, mission_queue.list_missions())
            if self.path == "/api/opportunities":
                self.send_json(200, atelier_produits.list_opportunities(atelier_produits.DEFAULT_PRODUCTS_DIR))
                return
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
                if self.path == "/api/missions":
                    mission_id = mission_queue.enqueue(body)
                    self.send_json(201, {"id": mission_id, "status": "pending"})
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
