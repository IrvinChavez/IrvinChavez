#!/usr/bin/env python3
"""Genera los SVG del dashboard del perfil con datos reales de GitHub.

Sin dependencias externas (solo biblioteca estandar). Se ejecuta a diario
desde .github/workflows/update-dashboard.yml y escribe en ./assets.
"""
import base64, json, math, os, re, sys, textwrap
import urllib.request
from datetime import datetime, timezone
from html import escape

USER = os.environ.get("GH_USER", "IrvinChavez")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
os.makedirs(OUT, exist_ok=True)

FONT = 'font-family="-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif"'
BG, CARD, LINE, TXT, MUT, GRN = "#0b0e14", "#0d1117", "#21262d", "#e6edf3", "#8b949e", "#3fb950"
LANG_COLORS = {"TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572a5",
               "CSS": "#8b5cf6", "HTML": "#e34c26", "Otros": "#6e7681"}
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]

# Descripciones basadas en el contenido real de cada repositorio.
PROJECTS = [
    ("SYSTEM", "App multiplataforma con Expo Router, React Native y Firebase.",
     "Expo · React Native · Firebase"),
    ("PAGEMY", "Sitio web hecho con React y Vite, publicado en Netlify.",
     "React · Vite · Tailwind CSS"),
    ("POPSTAR", "Tienda en línea con catálogo, carrito de compras y contacto.",
     "HTML · CSS · JavaScript"),
    ("POKEAPI", "App móvil con Expo Router y React Native.",
     "Expo · React Native · TypeScript"),
    ("ProyectoCalculo", "Proyecto de cálculo desarrollado en Python.", "Python"),
]


def get(url, binary=False):
    h = {"User-Agent": "profile-dashboard", "Accept": "application/vnd.github+json"}
    if TOKEN and "api.github.com" in url:
        h["Authorization"] = "Bearer " + TOKEN
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30) as r:
        data = r.read()
    return data if binary else data.decode("utf-8")


def api(path):
    return json.loads(get("https://api.github.com" + path))


def save(name, svg):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)


def svg_open(w, h):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">')


def card(x, y, w, h, r=12, fill=CARD):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{LINE}"/>'


def text(x, y, s, size=13, fill=TXT, weight="400", anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" fill="{fill}" {FONT} font-size="{size}" '
            f'font-weight="{weight}" text-anchor="{anchor}" {extra}>{escape(str(s))}</text>')


# ---------------------------------------------------------------- datos
user = api(f"/users/{USER}")
repos_all = api(f"/users/{USER}/repos?per_page=100&sort=pushed")
repos = [r for r in repos_all if not r["fork"] and r["name"] != USER
         and not r["name"].lower().endswith(".github.io")]
stars = sum(r["stargazers_count"] for r in repos_all)
created = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
years = max(1, datetime.now(timezone.utc).year - created.year)

lang_bytes = {}
for r in repos:
    try:
        for k, v in api(f"/repos/{USER}/{r['name']}/languages").items():
            lang_bytes[k] = lang_bytes.get(k, 0) + v
    except Exception as e:  # repo vacio o error puntual
        print("langs", r["name"], e, file=sys.stderr)

html = get(f"https://github.com/users/{USER}/contributions")
cells = []
for tag in re.findall(r"<td[^>]*ContributionCalendar-day[^>]*>", html):
    d = re.search(r'data-date="([\d-]+)"', tag)
    l = re.search(r'data-level="(\d)"', tag)
    if d and l:
        cells.append((d.group(1), int(l.group(1))))
cells.sort()
m = re.search(r"([\d,\.]+)\s+contributions?\s+in\s+the\s+last\s+year", html)
total_contrib = m.group(1) if m else str(sum(1 for _, l in cells if l))

avatar_b64 = base64.b64encode(get(user["avatar_url"] + "&s=240", binary=True)).decode()

try:
    events = [e for e in api(f"/users/{USER}/events/public?per_page=50") if e["type"] == "PushEvent"]
except Exception:
    events = []

# ---------------------------------------------------------------- profile.svg
W, H = 260, 372
s = [svg_open(W, H), f'<defs><clipPath id="c"><circle cx="130" cy="112" r="96"/></clipPath></defs>',
     card(0.5, 0.5, W - 1, H - 1)]
s.append(f'<circle cx="130" cy="112" r="98" fill="none" stroke="{LINE}" stroke-width="2"/>')
s.append(f'<image x="34" y="16" width="192" height="192" clip-path="url(#c)" preserveAspectRatio="xMidYMid slice" '
         f'href="data:image/jpeg;base64,{avatar_b64}" xlink:href="data:image/jpeg;base64,{avatar_b64}"/>')
s.append(text(20, 244, user.get("name") or USER, 20, weight="700"))
s.append(text(20, 264, "@" + USER, 13, MUT))
s.append(f'<rect x="20" y="276" width="220" height="30" rx="6" fill="#161b22" stroke="{LINE}"/>')
s.append(text(130, 296, "Seguir en GitHub", 12.5, weight="600", anchor="middle"))
desc = ["Estudiante de Ingeniería en", "Desarrollo de Software. Me interesan",
        "la programación y la tecnología."]
for i, ln in enumerate(desc):
    s.append(text(20, 326 + i * 16, ln, 11.5, "#c9d1d9"))
s.append("</svg>")
save("profile.svg", "".join(s))

# ---------------------------------------------------------------- hero.svg
W, H = 760, 196
s = [svg_open(W, H), card(0.5, 0.5, W - 1, 72)]
s.append(text(20, 32, f"Bienvenido al Hub de {user.get('name') or USER}", 18, weight="700"))
s.append(text(20, 54, "Explora mis proyectos y contribuciones de código abierto.", 12, MUT))
s.append(text(W - 20, 32, "Actualizado " + datetime.now(timezone.utc).strftime("%d/%m/%Y"),
              10, MUT, anchor="end"))
stats = [("REPOS TOTALES", user["public_repos"]), ("ESTRELLAS", stars),
         ("SEGUIDORES", user["followers"]), ("AÑOS ACTIVO" if years > 1 else "AÑO ACTIVO", years)]
cw = (W - 3 * 12) / 4
for i, (lab, val) in enumerate(stats):
    x = i * (cw + 12)
    s.append(card(x + 0.5, 84.5, cw - 1, 110))
    cx = x + cw / 2
    ic = f'stroke="{MUT}" stroke-width="1.6" fill="none" stroke-linejoin="round"'
    if i == 0:
        s.append(f'<rect x="{cx-7}" y="100" width="14" height="14" rx="2" {ic}/>')
    elif i == 1:
        pts = " ".join(f"{cx+8*math.sin(a*0.628):.1f},{107-8*math.cos(a*0.628):.1f}"
                       if a % 2 == 0 else
                       f"{cx+3.5*math.sin(a*0.628):.1f},{107-3.5*math.cos(a*0.628):.1f}"
                       for a in range(10))
        s.append(f'<polygon points="{pts}" {ic}/>')
    elif i == 2:
        s.append(f'<circle cx="{cx-3}" cy="103" r="3.5" {ic}/><path d="M{cx-9} 114 q6 -8 12 0" {ic}/>'
                 f'<circle cx="{cx+6}" cy="104" r="2.6" {ic}/>')
    else:
        s.append(f'<circle cx="{cx}" cy="107" r="8" {ic}/><path d="M{cx} 102 v5 l3 2" {ic}/>')
    s.append(text(cx, 152, val, 30, weight="700", anchor="middle"))
    s.append(text(cx, 176, lab, 10, MUT, anchor="middle", extra='letter-spacing="1.2"'))
s.append("</svg>")
save("hero.svg", "".join(s))

# ---------------------------------------------------------------- contrib.svg
cs, gap = 10, 3
first = datetime.fromisoformat(cells[0][0]).weekday()  # lunes=0
offset = (first + 1) % 7  # domingo=0
grid = [None] * offset + cells
weeks = -(-len(grid) // 7)
left, top = 16, 52
W = left * 2 + weeks * (cs + gap) - gap
H = top + 7 * (cs + gap) + 30
cols = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
s = [svg_open(W, H), card(0.5, 0.5, W - 1, H - 1)]
s.append(text(left, 28, "Contribuciones", 13, MUT))
s.append(text(W - left, 28, f"Total: {total_contrib} en el último año", 12, TXT, anchor="end"))
last_month = None
for i, c in enumerate(grid):
    if c is None:
        continue
    w, d = divmod(i, 7)
    x, y = left + w * (cs + gap), top + d * (cs + gap)
    s.append(f'<rect x="{x}" y="{y}" width="{cs}" height="{cs}" rx="2" fill="{cols[c[1]]}"/>')
    mo = c[0][:7]
    if d == 0 and mo != last_month and (last_month is not None or w < 3):
        s.append(text(x, 46, MESES[int(mo[5:]) - 1][:3].capitalize(), 9.5, MUT))
    if d == 0:
        last_month = mo
yb = top + 7 * (cs + gap) + 16
s.append(text(left, yb, "Último año de actividad", 10, MUT))
lx = W - left - 5 * (cs + 3) - 70
s.append(text(lx, yb, "Menos", 10, MUT, anchor="end"))
for k in range(5):
    s.append(f'<rect x="{lx+6+k*(cs+3)}" y="{yb-9}" width="{cs}" height="{cs}" rx="2" fill="{cols[k]}"/>')
s.append(text(lx + 12 + 5 * (cs + 3), yb, "Más", 10, MUT))
s.append("</svg>")
save("contrib.svg", "".join(s))

# ---------------------------------------------------------------- langs.svg
tot = sum(lang_bytes.values()) or 1
ordered = sorted(lang_bytes.items(), key=lambda kv: -kv[1])
top5, rest = ordered[:5], sum(v for _, v in ordered[5:])
if rest:
    top5.append(("Otros", rest))
W, H = 372, 200
s = [svg_open(W, H), card(0.5, 0.5, W - 1, H - 1)]
s.append(text(16, 26, "LENGUAJES MÁS USADOS", 10, MUT, extra='letter-spacing="1.2"'))
R, cx, cy, C = 46, 90, 112, 2 * math.pi * 46
s.append(f'<g transform="translate({cx},{cy}) rotate(-90)"><circle r="{R}" fill="none" stroke="#161b22" stroke-width="20"/>')
off = 0
for k, v in top5:
    ln = v / tot * C
    s.append(f'<circle r="{R}" fill="none" stroke="{LANG_COLORS.get(k, "#6e7681")}" stroke-width="20" '
             f'stroke-dasharray="{ln:.2f} {C-ln:.2f}" stroke-dashoffset="{-off:.2f}"/>')
    off += ln
s.append("</g>")
s.append(text(cx, cy + 4, f"{len(lang_bytes)} lenguajes", 10.5, MUT, anchor="middle"))
for i, (k, v) in enumerate(top5):
    y = 66 + i * 24
    s.append(f'<circle cx="190" cy="{y-4}" r="5" fill="{LANG_COLORS.get(k, "#6e7681")}"/>')
    s.append(text(204, y, k, 13))
    s.append(text(W - 18, y, f"{v / tot * 100:.0f}%", 13, MUT, anchor="end"))
s.append(text(16, H - 12, "Según el código de mis repositorios", 10, MUT))
s.append("</svg>")
save("langs.svg", "".join(s))

# ---------------------------------------------------------------- proyectos
by_name = {r["name"]: r for r in repos_all}
for name, desc, techs in PROJECTS:
    r = by_name.get(name, {})
    W, H = 372, 124
    s = [svg_open(W, H), card(0.5, 0.5, W - 1, H - 1, 10, "#0a0e14")]
    s.append(f'<path d="M16 22 h6 l2 3 h8 v11 h-16 z" fill="none" stroke="{MUT}" stroke-width="1.4" stroke-linejoin="round"/>')
    s.append(text(42, 34, name, 14, GRN, "700"))
    lang = r.get("language")
    if lang:
        s.append(f'<circle cx="{W-18-len(lang)*6.6-12}" cy="30" r="5" fill="{LANG_COLORS.get(lang, "#6e7681")}"/>')
        s.append(text(W - 18, 34, lang, 11.5, MUT, anchor="end"))
    for i, ln in enumerate(textwrap.wrap(desc, 56)[:2]):
        s.append(text(16, 62 + i * 16, ln, 12, "#c9d1d9"))
    s.append(text(16, 98, techs, 11, MUT))
    s.append(f'<text x="16" y="116" fill="{MUT}" {FONT} font-size="11">★ {r.get("stargazers_count", 0)}    ⑂ {r.get("forks_count", 0)}</text>')
    s.append("</svg>")
    save(f"proj-{name.lower()}.svg", "".join(s))

# ---------------------------------------------------------------- activity.svg
seen, rows = set(), []
for e in events:
    repo = e["repo"]["name"].split("/")[-1]
    day = e["created_at"][:10]
    if (repo, day) in seen:
        continue
    seen.add((repo, day))
    n = len(e["payload"].get("commits", [])) or 1
    rows.append((repo, day, n))
    if len(rows) == 5:
        break
W, H = 372, 40 + max(len(rows), 1) * 24 + 12
s = [svg_open(W, H), card(0.5, 0.5, W - 1, H - 1)]
s.append(text(16, 26, "ACTIVIDAD RECIENTE", 10, MUT, extra='letter-spacing="1.2"'))
if not rows:
    s.append(text(16, 56, "Sin actividad pública reciente.", 12, MUT))
for i, (repo, day, n) in enumerate(rows):
    y = 56 + i * 24
    s.append(f'<circle cx="22" cy="{y-4}" r="4" fill="{GRN}"/>')
    s.append(text(36, y, f"Push a {repo}", 12.5))
    s.append(text(W - 16, y, day, 11, MUT, anchor="end"))
s.append("</svg>")
save("activity.svg", "".join(s))
print("ok", len(cells), "celdas;", len(lang_bytes), "lenguajes")
