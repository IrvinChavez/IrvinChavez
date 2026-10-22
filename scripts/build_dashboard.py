#!/usr/bin/env python3
"""Genera los SVG del README del perfil con datos reales de GitHub.

Sin dependencias externas. Lo ejecuta a diario
.github/workflows/update-dashboard.yml y escribe en ./assets.
Produce: summary.svg (resumen) y proj-*.svg (tarjetas de proyectos).
"""
import json, os, sys, textwrap
import urllib.request
from datetime import datetime
from html import escape

USER = os.environ.get("GH_USER", "IrvinChavez")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT, exist_ok=True)

FONT = 'font-family="-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif"'
CARD, LINE, TXT, MUT, GRN = "#0d1117", "#21262d", "#e6edf3", "#8b949e", "#3fb950"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

# (repositorio, descripcion de una linea, tecnologias principales)
PROJECTS = [
    ("SYSTEM", "App móvil y web multiplataforma con respaldo en Firebase.",
     "Expo · React Native · TypeScript"),
    ("PAGEMY", "Sitio web con animaciones, publicado en Netlify.",
     "React · Vite · Tailwind CSS"),
    ("POPSTAR", "Tienda en línea con carrito de compras y contacto.",
     "HTML · CSS · JavaScript"),
    ("POKEAPI", "App móvil construida con Expo Router.",
     "Expo · React Native · TypeScript"),
]


def api(path):
    h = {"User-Agent": "profile-dashboard", "Accept": "application/vnd.github+json"}
    if TOKEN:
        h["Authorization"] = "Bearer " + TOKEN
    req = urllib.request.Request("https://api.github.com" + path, headers=h)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def save(name, svg):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)


def head(w, h, r=10, fill=CARD):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img"><rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" '
            f'rx="{r}" fill="{fill}" stroke="{LINE}"/>')


def text(x, y, s, size=13, fill=TXT, weight="400", anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" fill="{fill}" {FONT} font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" {extra}>{escape(str(s))}</text>')


repos_all = api(f"/users/{USER}/repos?per_page=100&sort=pushed")
repos = [r for r in repos_all if not r["fork"] and r["name"] != USER
         and not r["name"].lower().endswith(".github.io")]

langs = {}
with_code = 0
for r in repos:
    try:
        data = api(f"/repos/{USER}/{r['name']}/languages")
    except Exception as e:
        print("langs", r["name"], e, file=sys.stderr)
        continue
    if data:
        with_code += 1
    for k, v in data.items():
        langs[k] = langs.get(k, 0) + v

last = max(datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00")) for r in repos)
last_txt = f"{last.day} {MESES[last.month - 1]} {last.year}"

# ---------------------------------------------------------------- summary.svg
W, H = 760, 84
s = [head(W, H, 12)]
items = [(with_code, "PROYECTOS CON CÓDIGO"), (len(langs), "LENGUAJES"), (last_txt, "ÚLTIMO PUSH")]
cw = W / 3
for i, (val, lab) in enumerate(items):
    cx = cw * i + cw / 2
    if i:
        s.append(f'<line x1="{cw*i}" y1="20" x2="{cw*i}" y2="{H-20}" stroke="{LINE}"/>')
    s.append(text(cx, 44, val, 24, TXT, "700", "middle"))
    s.append(text(cx, 66, lab, 10, MUT, anchor="middle", extra='letter-spacing="1.2"'))
s.append("</svg>")
save("summary.svg", "".join(s))

# ---------------------------------------------------------------- proyectos
for name, desc, techs in PROJECTS:
    W, H = 372, 92
    s = [head(W, H, 10, "#0a0e14")]
    s.append(f'<rect x="16" y="20" width="3" height="16" rx="1.5" fill="{GRN}"/>')
    s.append(text(28, 33, name, 14, GRN, "700"))
    for i, ln in enumerate(textwrap.wrap(desc, 62)[:1]):
        s.append(text(16, 58, ln, 12, "#c9d1d9"))
    s.append(text(16, 78, techs, 11, MUT))
    s.append("</svg>")
    save(f"proj-{name.lower()}.svg", "".join(s))
print("ok", with_code, "proyectos;", len(langs), "lenguajes;", last_txt)
