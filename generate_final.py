"""Generate the GitHub profile SVG.

Two themes share one layout:
  metis   - warm amber interference dot field on near-black (default)
  claude  - parchment-warm dots on Claude's dark warm neutral

The interference pattern is a static bake of the wave-interference field used by
Metis's chat-aurora backdrop (5 drifting sources, 17px grid), approximated with
nested radial gradients plus a slow CSS drift. Canvas/Perlin is unavailable in a
repo-hosted SVG - GitHub strips <script> - so this is the closest static form.

Every dynamic string goes through esc(). A bare "&" makes the document
unparseable and GitHub renders a blank profile with no hint as to why.
"""
import base64
import io
import json
import math
import os
import random
import re
import ssl
import urllib.request
import xml.etree.ElementTree as ET

from PIL import Image

random.seed(2024)
W = 850
CM = 24
CRX = 10
GAP = 16

# ============================================================
# THEMES
# ============================================================
THEMES = {
    "metis": {
        "bg": "#0a0a0e",
        "bg_alt": "#101017",
        "card": "#14141a",
        "card_hi": "#1a1a22",
        "border": "#2a2a33",
        "text": "#e8e6ec",
        "muted": "#9a9a94",
        "faint": "#5c5c60",
        "accent": "#e8b96a",
        "accent2": "#4a6b5a",
        "dot": "#e8b96a",
        "ghost": "#4a6b5a",
        "theme_btn": "#14141a",
    },
    "claude": {
        "bg": "#1f1e1d",
        "bg_alt": "#262624",
        "card": "#262624",
        "card_hi": "#30302e",
        "border": "#3d3d3a",
        "text": "#faf9f5",
        "muted": "#c2c0b6",
        "faint": "#87867f",
        "accent": "#d97757",
        "accent2": "#c96442",
        "dot": "#c2c0b6",
        "ghost": "#87867f",
        "theme_btn": "#30302e",
    },
}

# ============================================================
# NETWORK
# ============================================================
def fetch(url, timeout=20):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, context=ctx, timeout=timeout).read()


def get_stars(repo):
    """Live stargazers_count. Uses GITHUB_TOKEN when present to dodge rate limits."""
    try:
        url = f"https://api.github.com/repos/linyeping/{repo}"
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/vnd.github+json"}
        token = os.environ.get("GITHUB_TOKEN", "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, headers=headers)
        return str(json.loads(urllib.request.urlopen(req, timeout=10).read()).get("stargazers_count", "?"))
    except Exception as e:
        print(f"  [warn] stars({repo}): {e}")
        return "?"


def png_data(path, sz):
    with Image.open(path) as im:
        im = im.convert("RGBA")
        im.thumbnail((sz, sz), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, format="PNG", optimize=True)
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"


def png_data_url(url, sz, cache_name=None):
    """Fetch an image and return a base64 data URI, caching to disk.

    The generated SVG is committed, but the generator still has to run on
    every Actions cycle for star counts. Network here is flaky (tunnel 502s),
    so a successful fetch is cached and reused rather than re-fetched.
    """
    cache = os.path.join(ASSETS, f"_{cache_name}.png") if cache_name else None
    if cache and os.path.exists(cache) and os.path.getsize(cache) > 0:
        with open(cache, "rb") as f:
            raw = f.read()
        print(f"    (cached)")
    else:
        raw = fetch(url)
        if cache:
            with open(cache, "wb") as f:
                f.write(raw)
    im = Image.open(io.BytesIO(raw)).convert("RGBA")
    im.thumbnail((sz, sz), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True)
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"


print("Fetching star counts...")
stars = {"Metis": get_stars("Metis"), "GemMate": get_stars("GemMate")}
print("  " + "  ".join(f"{k}: {v}" for k, v in stars.items()))

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
os.makedirs(ASSETS, exist_ok=True)

print("Loading local assets...")
assets = {}
for key, fname in [
    ("cert_bronze", "cert_bronze.png"),
    ("cert_silver", "cert_silver.png"),
]:
    p = os.path.join(ASSETS, fname)
    try:
        assets[key] = png_data(p, 512 if key.startswith("cert") else 128)
        print(f"  {key}: OK")
    except Exception as e:
        print(f"  [warn] {key}: {e}")
        assets[key] = None

print("Fetching remote logos...")
try:
    assets["logo_gemmate"] = png_data_url(
        "https://github.com/linyeping/GemMate/raw/main/assets/cover.png", 128, "cover_gemmate")
    print("  GemMate cover: OK")
except Exception as e:
    print(f"  [warn] GemMate cover: {e}")
try:
    assets["logo_metis"] = png_data_url(
        "https://raw.githubusercontent.com/linyeping/Metis/main/backend/assets/metis-M-128.png",
        128, "metis_mark")
    print("  Metis mark: OK")
except Exception as e:
    print(f"  [warn] Metis mark: {e}")


# ============================================================
# CONTRIBUTION SNAKE
# ============================================================
# snake.yml regenerates snake/*.svg daily. Inlined rather than hotlinked:
# GitHub's sanitiser strips external <image> refs inside repo-hosted SVGs.
SNAKE_URL = ("https://raw.githubusercontent.com/linyeping/linyeping/main/snake/"
             "github-contribution-grid-snake-dark.svg")


def get_snake(T):
    """Fetch the contribution grid snake and recolour it to the active theme.

    The upstream SVG defines its palette as CSS custom properties, so a
    palette swap is a matter of rewriting the :root block -- no need to touch
    the thousands of per-cell classes underneath it.
    """
    cache = os.path.join(ASSETS, "_snake_src.svg")
    if os.path.exists(cache) and os.path.getsize(cache) > 0:
        with open(cache, encoding="utf-8") as f:
            raw = f.read()
        print("    (cached)")
    else:
        try:
            raw = fetch(SNAKE_URL).decode("utf-8")
        except Exception as e:
            print(f"  [warn] snake: {e}")
            return None
        with open(cache, "w", encoding="utf-8") as f:
            f.write(raw)
        print("    (fetched + cached)")

    m = re.search(r'viewBox="([^"]+)"', raw)
    if not m:
        return None
    inner = re.sub(r"^.*?<svg[^>]*>", "", raw, flags=re.S)
    inner = re.sub(r"</svg>\s*$", "", inner, flags=re.S)

    # remap the five contribution levels onto a warm amber ramp
    ramp = [T["card_hi"], "#4a3a22", "#7a5c2c", "#b8862f", T["accent"]]
    snake_col = T["accent"]
    root = (
        ":root{"
        f"--cb:{T['card']};--cs:{snake_col};--ce:{T['card_hi']};"
        f"--c0:{ramp[0]};--c1:{ramp[1]};--c2:{ramp[2]};--c3:{ramp[3]};--c4:{ramp[4]}"
        "}"
    )
    inner = re.sub(r":root\{[^}]*\}", root, inner, count=1)
    if ":root{" not in inner:
        inner = root + inner
    return m.group(1), inner.strip()


print("Fetching contribution snake...")
snake = get_snake(THEMES[os.environ.get("PROFILE_THEME", "metis")])
print(f"  snake: {'OK' if snake else 'FAIL'}")


# ============================================================
# HELPERS
# ============================================================
def esc(t):
    """XML-escape text destined for an SVG node."""
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def wrap(text, limit):
    out, line = [], ""
    for w in text.split():
        if len(line + " " + w) > limit:
            out.append(line.strip())
            line = w
        else:
            line += " " + w
    if line.strip():
        out.append(line.strip())
    return out


# ============================================================
# WAVE INTERFERENCE FIELD  (baked from Metis chat-aurora.html)
# ============================================================
# 5 drifting sources, 17px lattice. Canvas runs this per frame with Perlin warp;
# in SVG we sample it once and let CSS drift the whole layer.
SOURCES = [
    {"bx": 0.22, "by": 0.30, "amp": 0.52, "freq": 7.2, "px": 0.0},
    {"bx": 0.78, "by": 0.25, "amp": 0.48, "freq": 6.5, "px": 2.1},
    {"bx": 0.50, "by": 0.72, "amp": 0.55, "freq": 7.8, "px": 1.0},
    {"bx": 0.18, "by": 0.70, "amp": 0.40, "freq": 6.0, "px": 3.3},
    {"bx": 0.82, "by": 0.68, "amp": 0.44, "freq": 7.5, "px": 0.7},
]
NOISE_SCALE = 0.0026 * 4.2


def dot_field(total_w, total_h, T, spacing=17, opacity_scale=1.0, t=0.0):
    """Sample the interference field on a lattice; return SVG <circle> markup."""
    parts = []
    # The canvas original runs maxAlpha 0.72 against a live backdrop. Cards sit
    # on top, so the field needs more punch than the raw values to stay legible.
    contrast, gain, max_a = 3.4, 2.6, 1.0
    cx0, cy0 = total_w / 2, total_h / 2
    y = -spacing * 2
    while y <= total_h + spacing * 2:
        x = -spacing * 2
        while x <= total_w + spacing * 2:
            px = (x - cx0) * NOISE_SCALE
            py = (y - cy0) * NOISE_SCALE
            warp_x = math.sin(py * 0.92 + t * 0.54) * 0.42 + math.cos(px * 0.58 - t * 0.38) * 0.26
            warp_y = math.cos(px * 0.84 - t * 0.46) * 0.34 - math.sin(py * 0.62 + t * 0.42) * 0.24
            wave = 0.0
            for s in SOURCES:
                dx = px + warp_x - (s["bx"] - 0.5) * (total_w * NOISE_SCALE)
                dy = py + warp_y - (s["by"] - 0.5) * (total_h * NOISE_SCALE)
                wave += math.cos(math.hypot(dx, dy) * s["freq"] - t * 2.6 + s["px"]) * s["amp"]
            wave /= 2.2
            radial = max(0.22, 1 - math.hypot((x - cx0) / total_w, (y - cy0) / total_h) * 1.06)
            bright = max(0.0, (wave + 1.0) * 0.5) * (0.42 + radial * 0.68)
            a = min(max_a, (bright ** contrast) * gain) * opacity_scale
            if a >= 0.03:
                col = T["dot"] if a > max_a * 0.5 * opacity_scale else T["ghost"]
                r = 1.7 + a * 0.9
                parts.append(f'<circle cx="{x + warp_x * 5.4:.0f}" cy="{y + warp_y * 5.0:.0f}" '
                             f'r="{r:.1f}" fill="{col}" opacity="{a:.2f}"/>')
            x += spacing
        y += spacing
    return parts


def dot_defs(T, prefix):
    """Soft glow filter + drift keyframes for the dot field."""
    return (
        f'<filter id="{prefix}glow" x="-30%" y="-30%" width="160%" height="160%">'
        f'<feGaussianBlur stdDeviation="1.6" result="b"/>'
        f'<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
    )


# ============================================================
# CARD SHELL
# ============================================================
PAD = 18   # card title left edge, relative to the card origin
IN = 16    # inner block left edge, relative to the card origin
COL = 108  # tech-stack category label column


def card(T, x, y, w, h):
    # Opaque. At 0.93 alpha the dot field showed through nicely, but the
    # Kaggle card's text bled into the Publications header above it.
    # The field still reads in the 24px gutters and the header band.
    return (
        f'<rect x="{x+2}" y="{y+2}" width="{w}" height="{h}" fill="black" opacity="0.3" rx="{CRX}"/>'
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{T["card"]}" rx="{CRX}" '
        f'stroke="{T["border"]}" stroke-width="1"/>'
    )


def card_title(T, x, y, text, prefix, ci=0):
    return (f'<text x="{x}" y="{y}" font-family="Google Sans,Segoe UI,sans-serif" font-size="15" '
            f'font-weight="600" fill="{T["accent"]}">{esc(text)}</text>')


# ============================================================
# BUILD
# ============================================================
TYPE_LINE = "Passionate about solving problems — for greatness is not something one is simply born with."


def build(theme_name):
    T = THEMES[theme_name]
    pre = theme_name[:3]
    A = T["accent"]
    cw = W - CM * 2

    hdr_h, about_h, type_h, res_h = 250, 178, 74, 190
    tech_h, proj_h, kag_h, pub_h, snake_h, ftr_h = 246, 212, 300, 286, 132, 66

    total = (hdr_h + GAP + about_h + GAP + type_h + GAP + res_h + GAP + tech_h + GAP
             + proj_h + GAP + kag_h + GAP + pub_h + GAP + snake_h + GAP + ftr_h)
    y_about = hdr_h + GAP
    y_type = y_about + about_h + GAP
    y_res = y_type + type_h + GAP
    y_tech = y_res + res_h + GAP
    y_proj = y_tech + tech_h + GAP
    y_kag = y_proj + proj_h + GAP
    y_pub = y_kag + kag_h + GAP
    y_snake = y_pub + pub_h + GAP
    y_ftr = y_snake + snake_h + GAP

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
         f'viewBox="0 0 {W} {total}" width="100%">']

    # ---- styles ----
    s.append("<style>")
    s.append(f"""@keyframes {pre}drift{{0%{{transform:translate(0,0)}}50%{{transform:translate(-9px,6px)}}100%{{transform:translate(0,0)}}}}
@keyframes {pre}drift2{{0%{{transform:translate(0,0)}}50%{{transform:translate(7px,-8px)}}100%{{transform:translate(0,0)}}}}
@keyframes {pre}blink{{0%,100%{{opacity:1}}50%{{opacity:0}}}}
@keyframes {pre}caret{{0%,100%{{opacity:1}}50%{{opacity:0}}}}
@keyframes {pre}tw{{0%{{clip-path:inset(0 100% 0 0)}}100%{{clip-path:inset(0 0 0 0)}}}}
@keyframes {pre}cardin{{0%{{opacity:0;transform:translateY(10px)}}100%{{opacity:1;transform:translateY(0)}}}}
@keyframes {pre}pulse{{0%,100%{{opacity:0.5}}50%{{opacity:0.95}}}}""")
    s.append(f'.{pre}card{{animation:{pre}cardin 0.5s ease-out both}}')
    s.append(f'.{pre}type{{font-family:JetBrains Mono,Fira Code,Consolas,monospace;'
             f'animation:{pre}tw 9s steps(88)1.1s forwards;}}')
    s.append(f'.{pre}caret{{animation:{pre}caret 1.05s step-end infinite}}')
    s.append(f'.{pre}halo{{animation:{pre}pulse 6s ease-in-out infinite}}')
    s.append("</style>")

    # ---- defs ----
    s.append("<defs>")
    s.append(f'<linearGradient id="{pre}bg" x1="0%" y1="0%" x2="100%" y2="100%">'
             f'<stop offset="0%" stop-color="{T["bg"]}"/>'
             f'<stop offset="55%" stop-color="{T["bg_alt"]}"/>'
             f'<stop offset="100%" stop-color="{T["bg"]}"/></linearGradient>')
    # three soft washes standing in for the canvas interference bloom
    for i, (fx, fy, fr, op) in enumerate([(0.24, 0.30, 0.46, 0.13),
                                          (0.78, 0.62, 0.42, 0.10),
                                          (0.50, 0.86, 0.38, 0.08)]):
        s.append(f'<radialGradient id="{pre}wash{i}" cx="{fx*100:.0f}%" cy="{fy*100:.0f}%" r="{fr*100:.0f}%">'
                 f'<stop offset="0%" stop-color="{T["dot"]}" stop-opacity="{op}"/>'
                 f'<stop offset="100%" stop-color="{T["dot"]}" stop-opacity="0"/></radialGradient>')
    for d in dot_defs(T, pre):
        s.append(d)
    s.append(f'<clipPath id="{pre}clip"><rect width="{W}" height="{total}"/></clipPath>')
    s.append("</defs>")

    # ---- background ----
    s.append(f'<rect width="{W}" height="{total}" fill="url(#{pre}bg)"/>')
    for i in range(3):
        s.append(f'<rect width="{W}" height="{total}" fill="url(#{pre}wash{i})"/>')

    # ---- interference dot field (the bake) ----
    # Cards cover most of the canvas, so the field is drawn on top at low
    # opacity as well - otherwise it only peeks through the 24px gutters.
    s.append(f'<g clip-path="url(#{pre}clip)" filter="url(#{pre}glow)">')
    s.append(f'<g style="animation:{pre}drift 26s ease-in-out infinite">')
    s.extend(dot_field(W, total, T, 18, 1.0, 0.0))
    s.append("</g>")
    s.append("</g>")

    # ============================================================
    # HEADER
    # ============================================================
    nx, ny = W / 2, 96
    NC = [A, T["accent2"], T["accent"], A, T["accent"], T["accent2"],
          T["accent"], T["accent2"], A]
    name = "LinYePing"
    fs = 42
    s.append(f'<text x="{nx}" y="{ny}" font-family="Google Sans,Segoe UI,sans-serif" font-size="{fs}" '
             f'font-weight="700" text-anchor="middle" class="{pre}card">')
    for ch, c in zip(name, NC):
        s.append(f'<tspan fill="{c}">{ch}</tspan>')
    s.append("</text>")

    # real name + handle
    s.append(f'<text x="{nx}" y="{ny+30}" font-family="Google Sans,Segoe UI,sans-serif" font-size="14" '
             f'text-anchor="middle" fill="{T["muted"]}">'
             f'<tspan fill="{A}">\u76db\u4f1f</tspan>'
             f'<tspan fill="{T["faint"]}">  /  </tspan>'
             f'<tspan fill="{T["muted"]}">Sheng Wei</tspan></text>')

    s.append(f'<text x="{nx}" y="{ny+52}" font-family="Google Sans,Segoe UI,sans-serif" font-size="13.5" '
             f'text-anchor="middle" fill="{T["text"]}" opacity="0.88">'
             f'AI Agent Engineer&#160;&#160;&#183;&#160;&#160;'
             f'LLM Application Development&#160;&#160;&#183;&#160;&#160;On-Device AI</text>')

    roles = [("AI Agents", A), ("Tool Use / MCP", T["accent2"]),
             ("RAG", T["accent"]), ("On-Device", T["ghost"])]
    widths = [len(r) * 8 + 28 for r, _ in roles]
    total_rw = sum(widths) + 10 * (len(roles) - 1)
    rx = nx - total_rw / 2
    ry = ny + 70
    for (text, color), rw in zip(roles, widths):
        s.append(f'<rect x="{rx:.0f}" y="{ry}" width="{rw}" height="24" fill="{color}" opacity="0.12" rx="12"/>')
        s.append(f'<rect x="{rx:.0f}" y="{ry}" width="{rw}" height="24" fill="none" stroke="{color}" '
                 f'stroke-width="0.8" opacity="0.4" rx="12"/>')
        s.append(f'<text x="{rx+rw/2:.0f}" y="{ry+16}" font-family="Google Sans,Segoe UI,sans-serif" '
                 f'font-size="11" fill="{color}" text-anchor="middle">{esc(text)}</text>')
        rx += rw + 10

    s.append(f'<text x="{nx}" y="{ry+44}" font-family="JetBrains Mono,Consolas,monospace" font-size="10.5" '
             f'text-anchor="middle" fill="{T["faint"]}">201180946@qq.com&#160;&#160;&#183;&#160;&#160;'
             f'yepinglin20@gmail.com</text>')

    # hairline under the header
    s.append(f'<line x1="{CM}" y1="{hdr_h-1}" x2="{W-CM}" y2="{hdr_h-1}" stroke="{T["border"]}" stroke-width="1"/>')
    s.append(f'<rect x="{CM}" y="{hdr_h-1}" width="{(W-CM*2)*0.34:.0f}" height="2" fill="{A}" opacity="0.8"/>')

    # ============================================================
    # ABOUT
    # ============================================================
    ay = y_about
    s.append(f'<g class="{pre}card" style="animation-delay:0.05s">')
    s.append(card(T, CM, ay, cw, about_h))
    s.append(f'<line x1="{CM}" y1="{ay+28}" x2="{CM+cw}" y2="{ay+28}" stroke="{T["border"]}" stroke-width="0.5"/>')
    s.append(f'<text x="{CM+PAD}" y="{ay+19}" font-family="JetBrains Mono,Consolas,monospace" font-size="10" '
             f'fill="{T["faint"]}">linyeping@github</text>')

    lines = [
        ("$ whoami", T["accent2"], True),
        ("> Building desktop & mobile AI agents - Agent Loop, Tool Use, MCP, RAG", T["text"], False),
        ("> Shipped 3 open-source agent products: Metis, Metis Mobile, GemMate", T["text"], False),
        ("> 3 papers published - graph neural networks, multimodal fake news detection", T["text"], False),
        ("> Kaggle: CSIRO bronze, BirdCLEF+ 2026 silver", T["text"], False),
        ("> Also into CUDA kernel dev and GPU optimization", T["text"], False),
    ]
    ty = ay + 50
    for i, (ln, col, bold) in enumerate(lines):
        s.append(f'<text x="{CM+PAD}" y="{ty}" font-family="JetBrains Mono,Consolas,monospace" '
                 f'font-size="12" font-weight="{"600" if bold else "400"}" fill="{col}">{esc(ln)}</text>')
        ty += 20
    s.append("</g>")

    # ============================================================
    # TYPEWRITER  (below About, over a calm slice of the field)
    # ============================================================
    py_ = y_type
    # measured in-browser: this 91-char line renders 728px wide at 13px,
    # so the average advance is 8.0px, not the 6.6 a naive estimate gives
    type_w = len(TYPE_LINE) * 8.0
    s.append(f'<g class="{pre}card" style="animation-delay:0.1s">')
    s.append(card(T, CM, py_, cw, type_h))
    s.append(card_title(T, CM + 18, py_ + 24, "Statement", pre))
    s.append(f'<text x="{W-CM-PAD}" y="{py_+24}" font-family="monospace" font-size="9" '
             f'fill="{T["faint"]}" text-anchor="end">typewriter</text>')
    s.append(f'<rect x="{CM+PAD}" y="{py_+36}" width="3" height="{type_h-52}" rx="1.5" fill="{A}" opacity="0.7"/>')
    s.append(f'<text class="{pre}type" x="{CM+PAD+14}" y="{py_+60}" font-size="13" fill="{T["text"]}" '
             f'xml:space="preserve">{esc(TYPE_LINE)}</text>')
    # caret rides the end of the text. The line is 87 chars at 13px in a
    # proportional face, so the width has to be measured, not estimated.
    s.append(f'<rect class="{pre}caret" x="{CM+PAD+14+type_w:.0f}" y="{py_+48}" width="2" height="15" '
             f'fill="{A}" rx="1"/>')
    s.append("</g>")

    # ============================================================
    # RESEARCH INTERESTS
    # ============================================================
    ry = y_res
    s.append(f'<g class="{pre}card" style="animation-delay:0.15s">')
    s.append(card(T, CM, ry, cw, res_h))
    s.append(card_title(T, CM + 18, ry + 24, "Research Interests", pre))
    sub_gap = 10
    sub_w = (cw - 32 - sub_gap * 3) / 4
    cards = [
        ("AI Agents", A, ["Agent Loop", "Tool Use", "MCP / RAG"]),
        ("LLM Apps", T["accent2"], ["LangChain", "LlamaIndex", "Prompt Eng."]),
        ("On-Device AI", T["accent"], ["Edge LLM", "LiteRT-LM", "llama.cpp"]),
        ("ML / DL", T["ghost"], ["NLP", "Multimodal", "Optimization"]),
    ]
    for ci, (title, color, tags) in enumerate(cards):
        cx = CM + 16 + ci * (sub_w + sub_gap)
        cy = ry + 40
        ch = res_h - 54
        s.append(f'<rect x="{cx:.0f}" y="{cy}" width="{sub_w:.0f}" height="{ch}" fill="{T["bg_alt"]}" rx="7" '
                 f'stroke="{T["border"]}" stroke-width="0.5"/>')
        s.append(f'<rect x="{cx:.0f}" y="{cy}" width="{sub_w:.0f}" height="3" fill="{color}" rx="1.5"/>')
        # left-aligned inside the sub-card: title and tags share one edge
        s.append(f'<text x="{cx+14:.0f}" y="{cy+24}" font-family="Google Sans,Segoe UI,sans-serif" '
                 f'font-size="12.5" font-weight="600" fill="{T["text"]}">{esc(title)}</text>')
        tagy = cy + 44
        for tag in tags:
            tw = len(tag) * 6.4 + 16
            tx = cx + 14
            s.append(f'<rect x="{tx:.0f}" y="{tagy}" width="{tw:.0f}" height="18" fill="{color}" opacity="0.12" rx="9"/>')
            s.append(f'<text x="{tx+tw/2:.0f}" y="{tagy+13}" font-family="monospace" font-size="10" '
                     f'fill="{color}" text-anchor="middle" opacity="0.92">{esc(tag)}</text>')
            tagy += 23
    s.append("</g>")

    # ============================================================
    # TECH STACK
    # ============================================================
    tb = y_tech
    s.append(f'<g class="{pre}card" style="animation-delay:0.2s">')
    s.append(card(T, CM, tb, cw, tech_h))
    s.append(card_title(T, CM + 18, tb + 24, "Tech Stack", pre))
    cats = [
        ("Agent / LLM", [("Agent Loop", A), ("Tool Use", T["accent2"]), ("MCP", T["accent"]),
                          ("RAG", T["ghost"]), ("LangChain", A), ("LlamaIndex", T["accent2"]),
                          ("Multi-Agent", T["ghost"])]),
        ("AI / ML", [("Python", T["accent2"]), ("PyTorch", T["accent"]), ("TensorFlow", T["ghost"]),
                     ("Transformers", A), ("Fine-tune", T["accent2"]), ("OpenCV", T["accent"])]),
        ("Backend", [("Flask", T["accent"]), ("SSE", T["ghost"]), ("REST API", A),
                     ("MySQL", T["accent2"]), ("Electron", T["accent"]), ("React", T["ghost"])]),
        ("Systems", [("C / C++", A), ("TypeScript", T["accent2"]), ("Git", T["accent"]),
                     ("WSL", T["ghost"]), ("Worktree", A)]),
        ("On-Device", [("LiteRT-LM", T["ghost"]), ("llama.cpp", A), ("Flutter", T["accent2"]),
                        ("Android", T["accent"])]),
    ]
    rowy = tb + 44
    avail = CM + cw - 24 - (CM + 108)   # right edge the chip row may reach
    for cat, chips in cats:
        s.append(f'<text x="{CM+IN}" y="{rowy+16}" font-family="Google Sans,Segoe UI,sans-serif" '
                 f'font-size="11" fill="{T["muted"]}">{esc(cat)}</text>')
        xc = CM + COL
        for name_, color in chips:
            chipw = len(name_) * 7.6 + 28
            if xc + chipw > avail:          # drop chips that would run past the card
                break
            s.append(f'<rect x="{xc:.0f}" y="{rowy}" width="{chipw:.0f}" height="26" fill="{color}" '
                     f'opacity="0.11" rx="13"/>')
            s.append(f'<rect x="{xc:.0f}" y="{rowy}" width="{chipw:.0f}" height="26" fill="none" '
                     f'stroke="{color}" stroke-width="0.8" opacity="0.34" rx="13"/>')
            s.append(f'<circle cx="{xc+12:.0f}" cy="{rowy+13}" r="3.2" fill="{color}" opacity="0.65"/>')
            s.append(f'<text x="{xc+22:.0f}" y="{rowy+17}" font-family="Google Sans,Segoe UI,sans-serif" '
                     f'font-size="12" fill="{T["text"]}">{esc(name_)}</text>')
            xc += chipw + 9
        rowy += 40
    s.append("</g>")

    # ============================================================
    # FEATURED PROJECTS  (cards link out to the repos)
    # ============================================================
    pj = y_proj
    s.append(f'<g class="{pre}card" style="animation-delay:0.25s">')
    s.append(card(T, CM, pj, cw, proj_h))
    s.append(card_title(T, CM + 18, pj + 24, "Featured Projects", pre))
    pgap = 12
    pw = (cw - 32 - pgap) / 2
    projects = [
        ("Metis", "Desktop AI agent (Electron + Python). Agent Loop, Skills, Checkpoint, MCP connectors, "
                  "four work surfaces, Git Worktree execution. Android companion via accessibility API.",
         A, stars["Metis"], assets.get("logo_metis"), "Electron \u00b7 TypeScript \u00b7 Python \u00b7 MCP",
         "https://github.com/linyeping/Metis"),
        ("GemMate", "On-device study companion. Runs Gemma 4 E2B fully local via LiteRT-LM, falls back to "
                    "LAN Ollama. Smart Router + SM-2, OCR/STT, six languages.",
         T["accent2"], stars["GemMate"], assets.get("logo_gemmate"),
         "Flutter \u00b7 Dart \u00b7 LiteRT-LM \u00b7 Gemma 4",
         "https://github.com/linyeping/GemMate"),
    ]
    for pi, (nm, desc, color, st, logo, stack, url) in enumerate(projects):
        px = CM + 16 + pi * (pw + pgap)
        pcy = pj + 38
        pch = proj_h - 52
        s.append(f'<a href="{url}" target="_blank">'
                 f'<rect x="{px:.0f}" y="{pcy}" width="{pw:.0f}" height="{pch}" fill="{T["bg_alt"]}" rx="7" '
                 f'stroke="{T["border"]}" stroke-width="0.5"/></a>')
        s.append(f'<rect x="{px:.0f}" y="{pcy}" width="3" height="{pch}" fill="{color}" rx="1.5"/>')
        lx, ly, lsz = px + IN, pcy + 10, 40
        if logo:
            s.append(f'<image href="{logo}" x="{lx}" y="{ly}" width="{lsz}" height="{lsz}" '
                     f'preserveAspectRatio="xMidYMid meet"/>')
        # name and star sit to the right of the logo, on the logo's own
        # vertical centre so the block reads as one unit
        tx = lx + lsz + 12
        s.append(f'<text x="{tx:.0f}" y="{ly+17}" font-family="Google Sans,Segoe UI,sans-serif" '
                 f'font-size="15" font-weight="600" fill="{T["text"]}">{esc(nm)}</text>')
        s.append(f'<text x="{tx:.0f}" y="{ly+33}" font-family="monospace" font-size="10" '
                 f'fill="{color}">&#9733; {st}</text>')
        s.append(f'<text x="{px+pw-IN:.0f}" y="{ly+17}" font-family="monospace" font-size="10" '
                 f'fill="{T["faint"]}" text-anchor="end">view \u2192</text>')
        dy = pcy + 66
        for ln in wrap(desc, 46)[:4]:
            s.append(f'<text x="{px+IN:.0f}" y="{dy}" font-family="Google Sans,Segoe UI,sans-serif" '
                     f'font-size="11" fill="{T["muted"]}">{esc(ln)}</text>')
            dy += 15
        if stack:
            s.append(f'<text x="{px+IN:.0f}" y="{pcy+pch-12}" font-family="monospace" font-size="9" '
                     f'fill="{color}" opacity="0.72">{esc(stack)}</text>')
    s.append("</g>")

    # ============================================================
    # KAGGLE  (certificate thumbnails, side by side)
    # ============================================================
    ky = y_kag
    s.append(f'<g class="{pre}card" style="animation-delay:0.3s">')
    s.append(card(T, CM, ky, cw, kag_h))
    s.append(card_title(T, CM + 18, ky + 24, "Kaggle", pre))
    badges = [
        ("CSIRO - Image2Biomass Prediction", "Bronze", "296 / 3,805", "#c2703e",
         assets.get("cert_bronze")),
        ("BirdCLEF+ 2026", "Silver", "194 / 4,094", "#c9d1d9", assets.get("cert_silver")),
    ]
    kgap = 14
    kw = (cw - 32 - kgap) / 2
    for bi, (comp, medal, rank, mc, cert) in enumerate(badges):
        kx = CM + 16 + bi * (kw + kgap)
        kcy = ky + 38
        kch = kag_h - 52
        s.append(f'<rect x="{kx:.0f}" y="{kcy}" width="{kw:.0f}" height="{kch}" fill="{T["bg_alt"]}" rx="7" '
                 f'stroke="{T["border"]}" stroke-width="0.5"/>')
        s.append(f'<rect x="{kx:.0f}" y="{kcy}" width="3" height="{kch}" fill="{mc}" rx="1.5"/>')
        if cert:
            # fit the certificate to the height actually available rather than
            # to the card width - at full width a 560x345 cert is taller than
            # the caption block allows and spills past the card edge
            cap_h = 48
            iw_max, ih_max = kw - 28, kch - 24 - cap_h
            ih = ih_max
            iw = ih * 560 / 345
            if iw > iw_max:
                iw = iw_max
                ih = iw * 345 / 560
            ix = kx + (kw - iw) / 2
            s.append(f'<image href="{cert}" x="{ix:.0f}" y="{kcy+12}" width="{iw:.0f}" height="{ih:.0f}" '
                     f'preserveAspectRatio="xMidYMid meet" opacity="0.96"/>')
            ty2 = kcy + 12 + ih + 22
        else:
            ty2 = kcy + 30
        s.append(f'<circle cx="{kx+IN+2:.0f}" cy="{ty2-4}" r="4" fill="{mc}"/>')
        s.append(f'<text x="{kx+IN+12:.0f}" y="{ty2}" font-family="monospace" font-size="10.5" font-weight="600" '
                 f'fill="{mc}">{esc(medal.upper())}</text>')
        s.append(f'<text x="{kx+kw-IN:.0f}" y="{ty2}" font-family="monospace" font-size="9.5" '
                 f'fill="{T["faint"]}" text-anchor="end">{esc(rank)}</text>')
        nm_lines = wrap(comp, 40)
        ny2 = ty2 + 15
        for ln in nm_lines[:2]:
            s.append(f'<text x="{kx+IN:.0f}" y="{ny2}" font-family="Google Sans,Segoe UI,sans-serif" '
                     f'font-size="11" fill="{T["text"]}">{esc(ln)}</text>')
            ny2 += 14
    s.append("</g>")

    # ============================================================
    # PUBLICATIONS
    # ============================================================
    py2 = y_pub
    s.append(f'<g class="{pre}card" style="animation-delay:0.35s">')
    s.append(card(T, CM, py2, cw, pub_h))
    s.append(card_title(T, CM + 18, py2 + 24, "Publications", pre))
    cols = [CM + 22, CM + 58, CM + 452, CM + 664]
    thy = py2 + 52
    s.append(f'<rect x="{CM+12}" y="{thy-12}" width="{cw-24}" height="20" fill="{T["bg"]}" opacity="0.6" rx="3"/>')
    for cx, h in zip(cols, ["#", "Title", "Venue", "Status"]):
        s.append(f'<text x="{cx}" y="{thy}" font-family="monospace" font-size="10" font-weight="600" '
                 f'fill="{T["faint"]}">{h}</text>')
    papers = [
        ("Social media rumor detection using multi-relational temporal-semantic augmented dynamic "
         "graph neural networks", "Complex & Intelligent Systems", "2026.08",
         "https://doi.org/10.1007/s40747-026-02463-5"),
        ("A dataset of Tang poetry sentence pairs for metrical imitation", "China Scientific Data",
         "2026.09", "https://doi.org/10.11922/11-6035.csd.2025.0219.zh"),
        ("A decoupled approach for multimodal fake news detection incorporating entity knowledge "
         "enhancement and multi-scale adaptive fusion", "Data Intelligence", "2026.09",
         "https://doi.org/10.3724/2096-7004.di.2025.1349"),
    ]
    # Every cell in a row shares one baseline. The title may wrap to three
    # lines, so the row is laid out from the title block: the number, venue
    # and pill all align to the title's FIRST line, and the row height is
    # driven by the title block.
    # Every row is the same height regardless of how the title wraps, so the
    # zebra banding lines up. The title is truncated to two lines: a third
    # line made the last row taller than the others and pushed the card
    # out of shape.
    # Row pitch is fixed at 54px and every title is fitted to exactly two
    # lines, so the number, title, venue and pill all sit on one baseline
    # and the zebra bands line up. Titles that need a third line are
    # truncated with an ellipsis rather than spilling past the band.
    # Every row gets the same height, sized for the longest title. Titles
    # wrap naturally; the number, venue and pill all sit on the row's first
    # baseline. Truncating a title to fit was not an option - the paper
    # name is the point of the row.
    MAXL = max(len(wrap(t, 60)) for t, _, _, _ in papers)
    ROW_H = 22 + MAXL * 15
    for row, (title, venue, year, doi) in enumerate(papers):
        lines = wrap(title, 60)
        ryr = thy + 32 + row * ROW_H       # shared baseline for the row
        band_top = ryr - 16
        band_h = ROW_H - 6
        if row % 2 == 0:
            s.append(f'<rect x="{CM+12}" y="{band_top}" width="{cw-24}" height="{band_h}" '
                     f'fill="{T["bg"]}" opacity="0.45" rx="3"/>')
        s.append(f'<a href="{doi}" target="_blank">'
                 f'<rect x="{CM+12}" y="{band_top}" width="{cw-24}" height="{band_h}" '
                 f'fill="transparent"/></a>')
        # number, title, venue and pill all share ryr as their baseline
        s.append(f'<text x="{cols[0]}" y="{ryr}" font-family="monospace" font-size="11" '
                 f'fill="{T["faint"]}" dominant-baseline="alphabetic">{row+1}</text>')
        for li, ln in enumerate(lines):
            s.append(f'<text x="{cols[1]}" y="{ryr+li*15}" font-family="Google Sans,Segoe UI,sans-serif" '
                     f'font-size="10" font-style="italic" fill="{T["text"]}" '
                     f'dominant-baseline="alphabetic">{esc(ln)}</text>')
        s.append(f'<text x="{cols[2]}" y="{ryr}" font-family="monospace" font-size="10" '
                 f'fill="{T["muted"]}" dominant-baseline="alphabetic">{esc(venue)}</text>')
        # The pill sits on the SAME baseline as the row number, the title's
        # first line and the venue. Centring it on the wrapped title block
        # put it at a different height in every row, which read as a
        # misaligned table.
        pw_ = 116
        px_ = cols[3]
        pill_y = ryr - 9
        s.append(f'<rect x="{px_}" y="{pill_y}" width="{pw_}" height="18" fill="{T["accent2"]}" '
                 f'opacity="0.18" rx="9"/>')
        # 9px text on an 11px row baseline: nudge up so the pill's text
        # shares the row's baseline with the number and the venue
        s.append(f'<text x="{px_+10}" y="{ryr}" font-family="monospace" font-size="9" '
                 f'font-weight="600" fill="{T["accent"]}" dominant-baseline="alphabetic">PUBLISHED</text>')
        s.append(f'<rect x="{px_+73}" y="{ryr-7}" width="0.5" height="9" fill="{T["border"]}"/>')
        s.append(f'<text x="{px_+82}" y="{ryr}" font-family="monospace" font-size="9" '
                 f'fill="{T["muted"]}" dominant-baseline="alphabetic">{year}</text>')
    s.append("</g>")

    # ============================================================
    # CONTRIBUTION GRAPH
    # ============================================================
    shy = y_snake
    s.append(f'<g class="{pre}card" style="animation-delay:0.4s">')
    s.append(card(T, CM, shy, cw, snake_h))
    s.append(card_title(T, CM + 18, shy + 24, "Contribution Graph", pre))
    if snake:
        vb, markup = snake
        parts = [float(v) for v in vb.replace(",", " ").split()]
        sw, sh = parts[2], parts[3]
        avail_w, avail_h = cw - 36, snake_h - 46
        sc = min(avail_w / sw, avail_h / sh)
        dx = CM + 18 + (avail_w - sw * sc) / 2
        dy = shy + 36 + (avail_h - sh * sc) / 2
        s.append(f'<g transform="translate({dx:.1f},{dy:.1f}) scale({sc:.4f})" opacity="0.92">{markup}</g>')
    s.append("</g>")

    # ============================================================
    # FOOTER
    # ============================================================
    s.append(f'<line x1="{CM}" y1="{y_ftr-14}" x2="{W-CM}" y2="{y_ftr-14}" stroke="{T["border"]}" stroke-width="1"/>')
    s.append(f'<rect x="{CM}" y="{y_ftr-13}" width="{(W-CM*2)*0.34:.0f}" height="2" fill="{A}" opacity="0.8"/>')
    s.append(f'<text x="{W/2}" y="{y_ftr+20}" font-family="Google Sans,Segoe UI,sans-serif" font-size="12" '
             f'fill="{T["muted"]}" text-anchor="middle" opacity="0.75">'
             f'Let&apos;s build something that actually ships.</text>')
    s.append(f'<text x="{W/2}" y="{y_ftr+42}" font-family="monospace" font-size="9" '
             f'fill="{T["faint"]}" text-anchor="middle">github.com/linyeping</text>')

    s.append("</svg>")
    return "\n".join(s)


# ============================================================
out_dir = os.path.dirname(os.path.abspath(__file__))
theme = os.environ.get("PROFILE_THEME", "metis")
svg = build(theme)

try:
    ET.fromstring(svg)
except ET.ParseError as e:
    line, col = e.position
    ctx = svg.split("\n")[line - 1][max(0, col - 60):col + 60]
    print(f"[fail] malformed SVG at line {line}, col {col}: {e}")
    print(f"       ...{ctx}...")
    raise SystemExit(1)

with open(os.path.join(out_dir, "profile.svg"), "w", encoding="utf-8") as f:
    f.write(svg)
print(f"[ok] profile.svg ({len(svg)} bytes, theme={theme})")
