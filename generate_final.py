"""Generate ONE comprehensive SVG for GitHub profile - full dark theme, floating cards, embedded logos, tech vibes."""
import random, math, urllib.request, base64, io, os, ssl, json
from PIL import Image

random.seed(2024)
G = ['#4285F4', '#EA4335', '#FBBC05', '#34A853']
BG = '#0d1117'
BG2 = '#161b22'
BORDER = '#21262d'
T1 = '#e6edf3'
T2 = '#8b949e'
W = 850
CM = 24  # card margin
CRX = 10
GAP = 16

# ============================================================
# DOWNLOAD LOGOS
# ============================================================
def dl_encode(url, sz=72):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = urllib.request.urlopen(req, context=ctx, timeout=15).read()
        img = Image.open(io.BytesIO(data))
        img.thumbnail((sz, sz), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
    except Exception as e:
        print(f"  [warn] {e}")
        return None

# ============================================================
# LIVE STAR COUNTS from GitHub API
# ============================================================
def get_stars(repo):
    """Fetch live stargazers_count for linyeping/<repo>."""
    try:
        url = f"https://api.github.com/repos/linyeping/{repo}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        return str(data.get("stargazers_count", "?"))
    except Exception as e:
        print(f"  [warn] stars({repo}): {e}")
        return "?"

print("Fetching star counts...")
stars_gem = get_stars("GemMate")
stars_inv = get_stars("InSeeVision")
print(f"  GemMate: {stars_gem} stars")
print(f"  InSeeVision: {stars_inv} stars")

print("Downloading logos...")
logo_gem = dl_encode("https://github.com/linyeping/GemMate/raw/main/assets/cover.png", 72)
logo_inv = dl_encode("https://raw.githubusercontent.com/linyeping/InSeeVision/master/assets/7.png", 72)
print(f"  GemMate: {'OK' if logo_gem else 'FAIL'}")
print(f"  InSeeVision: {'OK' if logo_inv else 'FAIL'}")

# ============================================================
# HELPERS
# ============================================================
cw = W - CM * 2

def card(x, y, w, h, accent=None):
    s = []
    s.append(f'<rect x="{x+2}" y="{y+2}" width="{w}" height="{h}" fill="black" opacity="0.25" rx="{CRX}" filter="url(#shadow)"/>')
    s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{BG2}" rx="{CRX}" stroke="{BORDER}" stroke-width="1"/>')
    if accent:
        s.append(f'<rect x="{x}" y="{y}" width="{w}" height="3" fill="{accent}" rx="1.5"/>')
    return '\n'.join(s)

def gdots(cx, cy, sz=2.5, gap=10):
    s = []
    for i, c in enumerate(G):
        x = cx - gap*1.5 + i*gap
        s.append(f'<circle cx="{x:.0f}" cy="{cy}" r="{sz}" fill="{c}" class="gd{i}"/>')
    return '\n'.join(s)

def stitle(x, y, text, ci):
    return f'<text x="{x}" y="{y}" font-family="Google Sans,Segoe UI,sans-serif" font-size="15" font-weight="600" fill="{G[ci%4]}">{text}</text>'

# ============================================================
# BUILD
# ============================================================
def build():
    hdr_h = 240
    about_h = 145
    res_h = 195
    tech_h = 175
    proj_h = 170
    pub_h = 160
    net_h = 100  # flowing network section
    ftr_h = 70

    total = hdr_h + GAP + about_h + GAP + res_h + GAP + tech_h + GAP + proj_h + GAP + pub_h + GAP + net_h + ftr_h
    y_about = hdr_h + GAP
    y_res = y_about + about_h + GAP
    y_tech = y_res + res_h + GAP
    y_proj = y_tech + tech_h + GAP
    y_pub = y_proj + proj_h + GAP
    y_net = y_pub + pub_h + GAP
    y_ftr = y_net + net_h

    # Particles
    random.seed(2024)
    parts = []
    for i in range(50):
        parts.append({'x': random.uniform(15, W-15), 'y': random.uniform(15, total-15),
                       'r': random.uniform(1, 3.5), 'c': random.choice(G),
                       'op': random.uniform(0.1, 0.4), 'p': i % 12,
                       'dur': random.uniform(14, 28), 'dl': random.uniform(0, 12)})

    conns = []
    for i in range(len(parts)):
        for j in range(i+1, len(parts)):
            d = math.hypot(parts[i]['x']-parts[j]['x'], parts[i]['y']-parts[j]['y'])
            if d < 110:
                conns.append((i, j, max(0.015, 0.1*(1-d/110))))

    # Flowing network nodes (bottom section)
    random.seed(7777)
    net_nodes = []
    for i in range(22):
        net_nodes.append({'x': random.uniform(30, W-30), 'y': y_net + random.uniform(10, net_h-10),
                          'r': random.uniform(1.5, 4), 'c': random.choice(G),
                          'p': i % 8, 'dur': random.uniform(10, 22), 'dl': random.uniform(0, 8)})
    net_lines = []
    for i in range(len(net_nodes)):
        for j in range(i+1, len(net_nodes)):
            d = math.hypot(net_nodes[i]['x']-net_nodes[j]['x'], net_nodes[i]['y']-net_nodes[j]['y'])
            if d < 130:
                net_lines.append((i, j, max(0.05, 0.2*(1-d/130))))

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {total}" width="100%">']

    # ---- STYLES ----
    s.append('<style>')
    # Float patterns for particles
    for i in range(12):
        random.seed(2024 + i)
        d = [random.uniform(-25,25), random.uniform(-15,15), random.uniform(-20,20),
             random.uniform(-12,12), random.uniform(-22,22), random.uniform(-14,14)]
        s.append(f'@keyframes fl{i}{{0%,100%{{transform:translate(0,0)}}25%{{transform:translate({d[0]:.0f}px,{d[1]:.0f}px)}}50%{{transform:translate({d[2]:.0f}px,{d[3]:.0f}px)}}75%{{transform:translate({d[4]:.0f}px,{d[5]:.0f}px)}}}}')

    # Network node drift patterns
    for i in range(8):
        random.seed(7777 + i)
        d = [random.uniform(-35,35), random.uniform(-18,18), random.uniform(-30,30),
             random.uniform(-15,15), random.uniform(-28,28), random.uniform(-16,16)]
        s.append(f'@keyframes nd{i}{{0%,100%{{transform:translate(0,0)}}33%{{transform:translate({d[0]:.0f}px,{d[1]:.0f}px)}}66%{{transform:translate({d[2]:.0f}px,{d[3]:.0f}px)}}}}')

    s.append('''@keyframes lnPulse{0%,100%{opacity:1}50%{opacity:0.3}}
@keyframes glow{0%,100%{filter:drop-shadow(0 0 4px rgba(66,133,244,0.3))}50%{filter:drop-shadow(0 0 12px rgba(66,133,244,0.6))}}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}
@keyframes fadeUp{0%{opacity:0;transform:translateY(10px)}100%{opacity:1;transform:translateY(0)}}
@keyframes typeIn{0%{opacity:0;transform:translateX(-6px)}100%{opacity:1;transform:translateX(0)}}
@keyframes chipPop{0%{opacity:0;transform:scale(0.85)}100%{opacity:1;transform:scale(1)}}
@keyframes cardIn{0%{opacity:0;transform:translateY(12px)}100%{opacity:1;transform:translateY(0)}}
@keyframes dataFlow{0%{stroke-dashoffset:30}100%{stroke-dashoffset:0}}
@keyframes flowGlow{0%,100%{opacity:0.15;filter:drop-shadow(0 0 2px currentColor)}50%{opacity:0.5;filter:drop-shadow(0 0 6px currentColor)}}
@keyframes nodeGlow{0%,100%{r:2;opacity:0.5}50%{r:3.5;opacity:1}}
@keyframes scanLine{0%{transform:translateX(-100%)}100%{transform:translateX(850px)}}
@keyframes wave{0%,100%{transform:translate(0,0)}15%{transform:translate(5px,-14px)}35%{transform:translate(0,-2px)}55%{transform:translate(5px,-14px)}75%{transform:translate(0,0)}}
@keyframes peekBob{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}
@keyframes bubPop{0%{opacity:0;transform:scale(0.5)}60%{opacity:1;transform:scale(1.1)}100%{opacity:1;transform:scale(1)}}''')

    # Sequential Google dots — smooth "water flowing" wave with overlapping brightness
    # Each dot uses a wide gaussian-like curve that overlaps with neighbors
    # Dot i peaks at i*25% of the cycle, with smooth ramp-up/down
    s.append('@keyframes gd0{0%{opacity:1}8%{opacity:0.7}17%{opacity:0.3}25%{opacity:0.15}75%{opacity:0.15}83%{opacity:0.3}92%{opacity:0.7}100%{opacity:1}}')
    s.append('@keyframes gd1{0%{opacity:0.3}8%{opacity:0.15}17%{opacity:0.3}20%{opacity:0.7}25%{opacity:1}30%{opacity:0.7}33%{opacity:0.3}42%{opacity:0.15}100%{opacity:0.15}}')
    s.append('@keyframes gd2{0%{opacity:0.15}25%{opacity:0.15}33%{opacity:0.15}42%{opacity:0.3}45%{opacity:0.7}50%{opacity:1}55%{opacity:0.7}58%{opacity:0.3}67%{opacity:0.15}100%{opacity:0.15}}')
    s.append('@keyframes gd3{0%{opacity:0.15}50%{opacity:0.15}58%{opacity:0.15}67%{opacity:0.3}70%{opacity:0.7}75%{opacity:1}80%{opacity:0.7}83%{opacity:0.3}92%{opacity:0.15}100%{opacity:0.15}}')
    for i in range(4):
        s.append(f'.gd{i}{{animation:gd{i} 3s ease-in-out infinite}}')

    s.append('</style>')

    # ---- DEFS ----
    s.append('<defs>')
    s.append(f'<linearGradient id="mainBg" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="{BG}"/><stop offset="50%" stop-color="#10151c"/><stop offset="100%" stop-color="{BG}"/></linearGradient>')
    s.append('<filter id="shadow"><feDropShadow dx="0" dy="2" stdDeviation="4" flood-opacity="0.3"/></filter>')
    s.append('<filter id="glow2"><feGaussianBlur stdDeviation="2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    # Scan line gradient
    s.append('<linearGradient id="scanGrad" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="transparent"/><stop offset="40%" stop-color="#4285F4" stop-opacity="0.06"/><stop offset="50%" stop-color="#4285F4" stop-opacity="0.12"/><stop offset="60%" stop-color="#4285F4" stop-opacity="0.06"/><stop offset="100%" stop-color="transparent"/></linearGradient>')
    s.append(f'<clipPath id="edgeClip"><rect x="0" y="0" width="{W}" height="{total}"/></clipPath>')
    s.append('</defs>')

    # ---- BACKGROUND ----
    s.append(f'<rect width="{W}" height="{total}" fill="url(#mainBg)"/>')

    # Tech grid (subtle cross pattern instead of dots)
    for gx in range(0, W, 50):
        s.append(f'<line x1="{gx}" y1="0" x2="{gx}" y2="{total}" stroke="{BORDER}" stroke-width="0.3" opacity="0.15"/>')
    for gy in range(0, total, 50):
        s.append(f'<line x1="0" y1="{gy}" x2="{W}" y2="{gy}" stroke="{BORDER}" stroke-width="0.3" opacity="0.15"/>')
    # Intersection glow dots
    for gx in range(0, W, 50):
        for gy in range(0, total, 50):
            s.append(f'<circle cx="{gx}" cy="{gy}" r="0.6" fill="{BORDER}" opacity="0.3"/>')

    # Scanning line (sweeps horizontally, sci-fi feel)
    s.append(f'<rect x="0" y="0" width="200" height="{total}" fill="url(#scanGrad)" style="animation:scanLine 12s linear infinite"/>')

    # Background particles
    s.append('<g style="animation:lnPulse 8s ease-in-out infinite">')
    for i, j, op in conns:
        pi, pj = parts[i], parts[j]
        s.append(f'<line x1="{pi["x"]:.0f}" y1="{pi["y"]:.0f}" x2="{pj["x"]:.0f}" y2="{pj["y"]:.0f}" stroke="{pi["c"]}" stroke-width="0.4" opacity="{op:.3f}" stroke-dasharray="4 8" style="animation:dataFlow 3s linear infinite"/>')
    s.append('</g>')
    for i, p in enumerate(parts):
        s.append(f'<circle cx="{p["x"]:.0f}" cy="{p["y"]:.0f}" r="{p["r"]:.1f}" fill="{p["c"]}" opacity="{p["op"]:.2f}" style="animation:fl{p["p"]} {p["dur"]:.0f}s ease-in-out {p["dl"]:.0f}s infinite"/>')

    # ================================================================
    # HEADER
    # ================================================================
    NAME = "LinYePing"
    NC = ['#4285F4','#EA4335','#FBBC05','#4285F4','#34A853','#EA4335','#FBBC05','#4285F4','#34A853']
    nx, ny = W/2, 85
    fs = 42

    # Name
    s.append('<g style="animation:glow 5s ease-in-out infinite">')
    s.append(f'<text x="{nx}" y="{ny}" font-family="Google Sans,Segoe UI,sans-serif" font-size="{fs}" font-weight="700" text-anchor="middle" style="animation:fadeUp 0.6s ease-out both">')
    for ch, c in zip(NAME, NC):
        s.append(f'<tspan fill="{c}">{ch}</tspan>')
    s.append('</text></g>')

    # Cursor
    cur_x = nx + len(NAME)*fs*0.28 + 4
    s.append(f'<rect x="{cur_x:.0f}" y="{ny-30}" width="2.5" height="36" rx="1" fill="#4285F4" style="animation:blink 1.2s step-end infinite"/>')

    # FIXED: Brackets - properly aligned, more visible
    name_half = len(NAME) * fs * 0.28
    bracket_y = ny + 3  # align with text baseline
    bracket_fs = 46
    lbx = nx - name_half - 38
    rbx = nx + name_half + 12
    s.append(f'<text x="{lbx:.0f}" y="{bracket_y}" font-family="JetBrains Mono,Fira Code,monospace" font-size="{bracket_fs}" font-weight="300" fill="{G[0]}" opacity="0.3" filter="url(#glow2)">&lt;</text>')
    s.append(f'<text x="{rbx:.0f}" y="{bracket_y}" font-family="JetBrains Mono,Fira Code,monospace" font-size="{bracket_fs}" font-weight="300" fill="{G[3]}" opacity="0.3" filter="url(#glow2)">/&gt;</text>')

    # Real name line
    s.append(f'<text x="{nx}" y="{ny+28}" font-family="Google Sans,Segoe UI,sans-serif" font-size="14" fill="{T2}" text-anchor="middle" opacity="0.5" style="animation:fadeUp 0.6s ease-out 0.3s both">')
    s.append(f'<tspan fill="{G[0]}">盛</tspan><tspan fill="{G[1]}"> 伟</tspan>')
    s.append(f'<tspan fill="{T2}" opacity="0.4">  /  </tspan>')
    s.append(f'<tspan fill="{T2}">Sheng Wei</tspan>')
    s.append(f'</text>')

    # Subtitle
    s.append(f'<text x="{nx}" y="{ny+46}" font-family="Google Sans,Segoe UI,sans-serif" font-size="12" fill="{T2}" text-anchor="middle" opacity="0.5">build something interesting, Why not?</text>')

    # Role chips
    roles = [("AI Undergraduate", G[0]), ("ML / DL", G[1]), ("Flutter Dev", G[2]), ("On-Device AI", G[3])]
    role_y = ny + 68
    total_rw = sum(len(r)*8+28 for r,_ in roles) + 10*(len(roles)-1)
    rx = nx - total_rw/2
    for text, color in roles:
        rw = len(text)*8 + 28
        s.append(f'<rect x="{rx:.0f}" y="{role_y}" width="{rw}" height="24" fill="{color}" opacity="0.1" rx="12"/>')
        s.append(f'<rect x="{rx:.0f}" y="{role_y}" width="{rw}" height="24" fill="none" stroke="{color}" stroke-width="0.8" opacity="0.35" rx="12"/>')
        s.append(f'<text x="{rx+rw/2:.0f}" y="{role_y+16}" font-family="Google Sans,Segoe UI,sans-serif" font-size="11" fill="{color}" text-anchor="middle">{text}</text>')
        rx += rw + 10

    # Google dots
    s.append(gdots(nx, hdr_h - 15, 3.5, 14))

    # Divider
    for i, c in enumerate(G):
        s.append(f'<rect x="{i*W/4:.0f}" y="{hdr_h}" width="{W/4:.0f}" height="3" fill="{c}" opacity="0.7"/>')

    # ================================================================
    # ABOUT CARD
    # ================================================================
    ay = y_about
    s.append(f'<g style="animation:cardIn 0.5s ease-out both">')
    s.append(card(CM, ay, cw, about_h))
    # Title bar — no separate bg rect, just divider line + traffic lights (clean look)
    s.append(f'<line x1="{CM}" y1="{ay+28}" x2="{CM+cw}" y2="{ay+28}" stroke="{BORDER}" stroke-width="0.5"/>')
    for i, c in enumerate(['#FF5F57','#FEBC2E','#28C840']):
        s.append(f'<circle cx="{CM+18+i*16}" cy="{ay+14}" r="4.5" fill="{c}"/>')
    s.append(f'<text x="{W/2}" y="{ay+18}" font-family="monospace" font-size="10" fill="{T2}" text-anchor="middle" opacity="0.6">linyeping@github ~ </text>')

    lines_data = [
        ("$ whoami", "#34A853", True),
        ("> AI Undergraduate | ML and DL Focus", T1, False),
        ("> NLP, Computer Vision, Flutter Android Developer", T1, False),
        ("> Exploring on-device LLM and AI Agents on mobile", T1, False),
        ("> Interested in CUDA kernel dev and GPU optimization", T1, False),
    ]
    ty = ay + 50
    for idx, (line, color, bold) in enumerate(lines_data):
        wt = "700" if bold else "400"
        dl = 0.12 * idx
        s.append(f'<text x="{CM+20}" y="{ty}" font-family="JetBrains Mono,Fira Code,monospace" font-size="12" font-weight="{wt}" fill="{color}" style="animation:typeIn 0.4s ease-out {dl:.2f}s both">{line}</text>')
        ty += 20
    # (cursor removed — cleaner look)
    s.append('</g>')

    # ================================================================
    # ANDROID ROBOT - uses ABSOLUTE coordinates (no <g transform>)
    # GitHub SVG sanitizer may strip transform attr on <g> elements,
    # so we compute every x/y position directly.
    # ================================================================
    ax = W - CM - 12   # 814 — right side of about card
    acy = ay + int(about_h * 0.50)  # vertically centered on about card
    # Bobbing wrapper (CSS animation only, no transform attribute)
    s.append(f'<g style="animation:peekBob 3s ease-in-out infinite">')
    # Soft glow
    s.append(f'<circle cx="{ax}" cy="{acy+10}" r="35" fill="#3DDC84" opacity="0.06"/>')
    # Right arm
    s.append(f'<rect x="{ax+20}" y="{acy+2}" width="8" height="22" rx="4" fill="#3DDC84"/>')
    # Left arm (waving)
    s.append(f'<g style="animation:wave 2s ease-in-out infinite">')
    s.append(f'<rect x="{ax-28}" y="{acy+2}" width="8" height="22" rx="4" fill="#3DDC84"/>')
    s.append(f'</g>')
    # Body
    s.append(f'<rect x="{ax-18}" y="{acy}" width="36" height="30" rx="6" fill="#3DDC84"/>')
    # Head dome (circle + rect junction)
    s.append(f'<circle cx="{ax}" cy="{acy-1}" r="20" fill="#3DDC84"/>')
    s.append(f'<rect x="{ax-18}" y="{acy-1}" width="36" height="5" fill="#3DDC84"/>')
    # Eyes
    s.append(f'<circle cx="{ax-7}" cy="{acy-10}" r="2.2" fill="white"/>')
    s.append(f'<circle cx="{ax+7}" cy="{acy-10}" r="2.2" fill="white"/>')
    # Antennae
    s.append(f'<line x1="{ax-9}" y1="{acy-18}" x2="{ax-14}" y2="{acy-28}" stroke="#3DDC84" stroke-width="2" stroke-linecap="round"/>')
    s.append(f'<line x1="{ax+9}" y1="{acy-18}" x2="{ax+14}" y2="{acy-28}" stroke="#3DDC84" stroke-width="2" stroke-linecap="round"/>')
    # Legs
    s.append(f'<rect x="{ax-12}" y="{acy+32}" width="10" height="14" rx="5" fill="#3DDC84"/>')
    s.append(f'<rect x="{ax+2}" y="{acy+32}" width="10" height="14" rx="5" fill="#3DDC84"/>')
    # Kaggle "K" gold badge on body
    s.append(f'<circle cx="{ax}" cy="{acy+13}" r="6.5" fill="{G[2]}" opacity="0.95"/>')
    s.append(f'<circle cx="{ax}" cy="{acy+13}" r="5" fill="#F4B400"/>')
    s.append(f'<text x="{ax}" y="{acy+16}" font-family="Google Sans,sans-serif" font-size="8" font-weight="700" fill="white" text-anchor="middle">K</text>')
    # Speech bubble "Hi!"
    bx, by = ax - 32, acy - 34
    s.append(f'<g style="animation:bubPop 0.5s ease-out 1.2s both">')
    s.append(f'<rect x="{bx-15}" y="{by-9}" width="30" height="18" fill="white" rx="9" opacity="0.92" stroke="#3DDC84" stroke-width="0.6"/>')
    s.append(f'<polygon points="{bx+8},{by+9} {bx+13},{by+9} {bx+16},{by+16}" fill="white" opacity="0.92"/>')
    s.append(f'<text x="{bx}" y="{by+4}" font-family="Google Sans,Segoe UI,sans-serif" font-size="10" font-weight="700" fill="#3DDC84" text-anchor="middle">Hi!</text>')
    s.append(f'</g>')
    s.append(f'</g>')

    # ================================================================
    # RESEARCH CARD
    # ================================================================
    ry = y_res
    s.append(f'<g style="animation:cardIn 0.5s ease-out 0.1s both">')
    s.append(card(CM, ry, cw, res_h))
    s.append(stitle(CM+16, ry+24, "Research Interests", 1))
    s.append(gdots(W-CM-30, ry+20, 2.5, 10))

    sub_gap = 10
    sub_w = (cw - 32 - sub_gap*3) / 4
    cards_d = [
        ("ML / DL", G[0], ["NLP", "CV", "Transformers", "Optimization"]),
        ("On-Device AI", G[1], ["Edge LLM", "Quantization", "Mobile Infer."]),
        ("AI Agents", G[2], ["Autonomous", "Tool Use", "Agentic Flow"]),
        ("CUDA / HPC", G[3], ["Kernel Dev", "GPU Opt", "Parallel"]),
    ]
    for ci, (title, color, tags) in enumerate(cards_d):
        cx = CM + 16 + ci*(sub_w+sub_gap)
        cy = ry + 40
        ch = res_h - 52
        s.append(f'<rect x="{cx:.0f}" y="{cy}" width="{sub_w:.0f}" height="{ch}" fill="{BG}" rx="6" stroke="{BORDER}" stroke-width="0.5"/>')
        s.append(f'<rect x="{cx:.0f}" y="{cy}" width="{sub_w:.0f}" height="3" fill="{color}" rx="1.5"/>')
        s.append(f'<text x="{cx+sub_w/2:.0f}" y="{cy+22}" font-family="Google Sans,Segoe UI,sans-serif" font-size="12" font-weight="600" fill="{T1}" text-anchor="middle">{title}</text>')
        tag_y = cy + 40
        for tag in tags:
            tw = len(tag)*6.5 + 14
            tx = cx + sub_w/2 - tw/2
            s.append(f'<rect x="{tx:.0f}" y="{tag_y}" width="{tw:.0f}" height="18" fill="{color}" opacity="0.1" rx="9"/>')
            s.append(f'<text x="{cx+sub_w/2:.0f}" y="{tag_y+13}" font-family="monospace" font-size="10" fill="{color}" text-anchor="middle" opacity="0.85">{tag}</text>')
            tag_y += 24
    s.append('</g>')

    # ================================================================
    # TECH STACK CARD
    # ================================================================
    tb = y_tech
    s.append(f'<g style="animation:cardIn 0.5s ease-out 0.2s both">')
    s.append(card(CM, tb, cw, tech_h))
    s.append(stitle(CM+16, tb+24, "Tech Stack", 2))
    s.append(gdots(W-CM-30, tb+20, 2.5, 10))

    categories = [
        ("AI / ML", [("Python",G[0]),("PyTorch",G[1]),("TensorFlow",G[2]),("HuggingFace",G[3]),("OpenCV",G[0]),("Kaggle",G[0])]),
        ("Systems", [("C++",G[1]),("CUDA",G[3]),("Linux",G[2])]),
        ("Mobile", [("Flutter",G[0]),("Dart",G[3]),("Android",G[1])]),
    ]
    row_y = tb + 42
    ci2 = 0
    for cat, chips in categories:
        s.append(f'<text x="{CM+24}" y="{row_y+16}" font-family="Google Sans,Segoe UI,sans-serif" font-size="11" fill="{T2}">{cat}</text>')
        xc = CM + 105
        for name, color in chips:
            chipw = len(name)*7.8 + 30
            chiph = 26
            dl = ci2 * 0.05
            s.append(f'<g style="animation:chipPop 0.35s ease-out {dl:.2f}s both">')
            s.append(f'<rect x="{xc:.0f}" y="{row_y}" width="{chipw:.0f}" height="{chiph}" fill="{color}" opacity="0.1" rx="13"/>')
            s.append(f'<rect x="{xc:.0f}" y="{row_y}" width="{chipw:.0f}" height="{chiph}" fill="none" stroke="{color}" stroke-width="0.8" opacity="0.3" rx="13"/>')
            s.append(f'<circle cx="{xc+12:.0f}" cy="{row_y+chiph/2:.0f}" r="3.5" fill="{color}" opacity="0.6"/>')
            s.append(f'<text x="{xc+22:.0f}" y="{row_y+chiph/2+4:.0f}" font-family="Google Sans,Segoe UI,sans-serif" font-size="12" fill="{T1}">{name}</text>')
            s.append('</g>')
            xc += chipw + 10
            ci2 += 1
        row_y += 42
    s.append('</g>')

    # ================================================================
    # PROJECTS CARD
    # ================================================================
    py = y_proj
    s.append(f'<g style="animation:cardIn 0.5s ease-out 0.3s both">')
    s.append(card(CM, py, cw, proj_h))
    s.append(stitle(CM+16, py+24, "Featured Projects", 3))
    s.append(gdots(W-CM-30, py+20, 2.5, 10))

    pg = 12
    pw = (cw - 32 - pg) / 2
    projects = [
        ("GemMate", "Your sovereign, zero-cost AI study companion - running Gemma 4 on your own hardware.", G[0], stars_gem, logo_gem),
        ("InSeeVision", "Edge-AI powered vision assistance for the visually impaired.", G[1], stars_inv, logo_inv),
    ]
    for pi, (name, desc, color, stars, logo) in enumerate(projects):
        px = CM + 16 + pi*(pw+pg)
        pcy = py + 38
        pch = proj_h - 50
        s.append(f'<rect x="{px:.0f}" y="{pcy}" width="{pw:.0f}" height="{pch}" fill="{BG}" rx="6" stroke="{BORDER}" stroke-width="0.5"/>')
        s.append(f'<rect x="{px:.0f}" y="{pcy}" width="3" height="{pch}" fill="{color}" rx="1.5"/>')
        lx, ly, lsz = px+16, pcy+10, 40
        if logo:
            s.append(f'<image href="{logo}" x="{lx}" y="{ly}" width="{lsz}" height="{lsz}" preserveAspectRatio="xMidYMid meet"/>')
        else:
            s.append(f'<circle cx="{lx+lsz/2}" cy="{ly+lsz/2}" r="{lsz/2}" fill="{color}" opacity="0.15"/>')
            s.append(f'<text x="{lx+lsz/2}" y="{ly+lsz/2+5}" font-size="16" fill="{color}" text-anchor="middle">{name[0]}</text>')
        s.append(f'<text x="{lx+lsz+10}" y="{ly+16}" font-family="Google Sans,Segoe UI,sans-serif" font-size="15" font-weight="600" fill="{T1}">{name}</text>')
        s.append(f'<text x="{lx+lsz+10}" y="{ly+32}" font-family="monospace" font-size="10" fill="{color}">&#9733; {stars}</text>')
        words = desc.split()
        line = ""
        dy = pcy + 65
        for w_t in words:
            if len(line + " " + w_t) > 48:
                s.append(f'<text x="{px+14:.0f}" y="{dy}" font-family="Google Sans,Segoe UI,sans-serif" font-size="11" fill="{T2}">{line.strip()}</text>')
                dy += 16
                line = w_t
            else:
                line += " " + w_t
        if line.strip():
            s.append(f'<text x="{px+14:.0f}" y="{dy}" font-family="Google Sans,Segoe UI,sans-serif" font-size="11" fill="{T2}">{line.strip()}</text>')
    s.append('</g>')

    # ================================================================
    # PUBLICATIONS CARD
    # ================================================================
    puy = y_pub
    s.append(f'<g style="animation:cardIn 0.5s ease-out 0.4s both">')
    s.append(card(CM, puy, cw, pub_h))
    s.append(stitle(CM+16, puy+24, "Publications", 0))
    s.append(gdots(W-CM-30, puy+20, 2.5, 10))
    s.append(f'<text x="{CM+16}" y="{puy+42}" font-family="Google Sans,Segoe UI,sans-serif" font-size="11" fill="{T2}" font-style="italic">Papers under review - links will be added upon acceptance.</text>')

    cols = [CM+24, CM+60, CM+480, CM+600, CM+720]
    headers = ["#","Title","Venue","Status","Link"]
    thy = puy + 62
    s.append(f'<rect x="{CM+12}" y="{thy-12}" width="{cw-24}" height="20" fill="{BG}" rx="3"/>')
    for ci3, (cx, h) in enumerate(zip(cols, headers)):
        s.append(f'<text x="{cx}" y="{thy}" font-family="monospace" font-size="10" fill="{T2}" font-weight="600">{h}</text>')
    for row in range(3):
        ryr = thy + 24 + row*26
        if row % 2 == 0:
            s.append(f'<rect x="{CM+12}" y="{ryr-12}" width="{cw-24}" height="24" fill="{BG}" opacity="0.4" rx="2"/>')
        s.append(f'<text x="{cols[0]}" y="{ryr}" font-family="monospace" font-size="11" fill="{T2}">{row+1}</text>')
        s.append(f'<text x="{cols[1]}" y="{ryr}" font-family="Google Sans,Segoe UI,sans-serif" font-size="11" fill="{T1}" font-style="italic">Paper Title Placeholder</text>')
        s.append(f'<text x="{cols[2]}" y="{ryr}" font-family="monospace" font-size="10" fill="{T2}">--</text>')
        bw, bx = 72, cols[3]-2
        s.append(f'<rect x="{bx}" y="{ryr-10}" width="{bw}" height="16" fill="{G[2]}" opacity="0.15" rx="8"/>')
        s.append(f'<text x="{bx+bw/2}" y="{ryr}" font-family="monospace" font-size="9" fill="{G[2]}" text-anchor="middle">Under Review</text>')
        s.append(f'<text x="{cols[4]}" y="{ryr}" font-family="monospace" font-size="10" fill="{T2}">TBD</text>')
    s.append('</g>')

    # ================================================================
    # FLOWING NETWORK (bottom tech decoration)
    # ================================================================
    # Connection lines with flowing dashes
    for i, j, op in net_lines:
        ni, nj = net_nodes[i], net_nodes[j]
        dur_l = random.uniform(2, 5)
        dl_l = random.uniform(0, 3)
        s.append(f'<line x1="{ni["x"]:.0f}" y1="{ni["y"]:.0f}" x2="{nj["x"]:.0f}" y2="{nj["y"]:.0f}" '
                 f'stroke="{ni["c"]}" stroke-width="0.8" opacity="{op:.2f}" '
                 f'stroke-dasharray="3 9" style="animation:dataFlow {dur_l:.1f}s linear {dl_l:.1f}s infinite"/>')

    # Glowing nodes
    for i, n in enumerate(net_nodes):
        glow_dur = random.uniform(2, 5)
        glow_dl = random.uniform(0, 4)
        s.append(f'<circle cx="{n["x"]:.0f}" cy="{n["y"]:.0f}" r="{n["r"]:.1f}" fill="{n["c"]}" opacity="0.6" '
                 f'filter="url(#glow2)" '
                 f'style="animation:nd{n["p"]} {n["dur"]:.0f}s ease-in-out {n["dl"]:.0f}s infinite"/>')
        # Inner glow dot
        s.append(f'<circle cx="{n["x"]:.0f}" cy="{n["y"]:.0f}" r="1" fill="white" opacity="0.5" '
                 f'style="animation:nd{n["p"]} {n["dur"]:.0f}s ease-in-out {n["dl"]:.0f}s infinite"/>')

    # ================================================================
    # FOOTER
    # ================================================================
    # Divider
    for i, c in enumerate(G):
        s.append(f'<rect x="{i*W/4:.0f}" y="{y_ftr-3}" width="{W/4:.0f}" height="3" fill="{c}" opacity="0.6"/>')

    s.append(f'<text x="{W/2}" y="{y_ftr+25}" font-family="Google Sans,Segoe UI,sans-serif" font-size="12" fill="{T2}" text-anchor="middle" opacity="0.6">build something interesting, Why not?</text>')
    s.append(gdots(W/2, y_ftr+45, 3, 14))
    s.append(f'<text x="{W/2}" y="{y_ftr+62}" font-family="monospace" font-size="9" fill="#484f58" text-anchor="middle">Made with curiosity</text>')

    s.append('</svg>')
    return '\n'.join(s)

# ============================================================
out_dir = os.path.dirname(os.path.abspath(__file__))
svg = build()
with open(os.path.join(out_dir, 'profile.svg'), 'w', encoding='utf-8') as f:
    f.write(svg)
print(f"[ok] profile.svg ({len(svg)} bytes)")
