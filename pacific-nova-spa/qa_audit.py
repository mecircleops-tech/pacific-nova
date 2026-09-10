#!/usr/bin/env python3
"""
QA STATIC AUDIT — Pacific Nova SPA
Membaca src/index.src.html (template) dan index.html (hasil build), lalu memeriksa
kontrak yang bikin file ini aman: single-file, id unik, sprite utuh, a11y dasar,
sinkronisasi breakpoint, dan keamanan innerHTML.

Jalankan: python3 qa_audit.py            (audit kedua file)
         python3 qa_audit.py --built     (audit index.html saja)
"""
import re, sys, pathlib, collections

ROOT = pathlib.Path(__file__).parent
TOKENS = ('__HERO_BG__', '__LOGO_URI__')


def strip_comments(src: str) -> str:
    """Komentar HTML bisa menyebut <style>/<body> sebagai teks; buang dulu."""
    return re.sub(r'<!--.*?-->', '', src, flags=re.S)


def slices(src: str):
    src = strip_comments(src)
    raw = src
    css = raw[raw.index('<style>') + 7:raw.index('</style>')] if '<style>' in raw else ''
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)   # komentar CSS bukan selector
    body = src[src.index('<body'):] if '<body' in src else src
    return css, body


def audit(path: pathlib.Path, label: str, built: bool):
    src = path.read_text(encoding='utf-8')
    css, body = slices(src)
    html_only = body[:body.index('<script>')] if '<script>' in body else body
    problems = []

    def bad(tag, msg):
        problems.append(f'{tag}  {msg}')

    # ---- A. dead / orphan CSS -------------------------------------------------
    css_bare = re.sub(r'url\([^)]*\)', 'url()', css)   # isi data-URI bukan selector
    defined = set(re.findall(r'\.([A-Za-z][\w-]*)', css_bare))
    used = set()          # hanya dari markup  → untuk A2 (styling yatim)
    broad = set()         # markup + setiap kata di string JS → untuk A1 (CSS mati)
    for m in re.findall(r'class="([^"]*)"', src):   # src penuh: kelas di string JS juga dihitung untuk A1
        used |= set(m.split())
    for m in re.findall(r'class=\\"([^\\"]*)', src):
        used |= set(x for x in m.split() if x)
    for m in re.findall(r"className = '([^']*)'", src):
        used |= set(m.split())
    used |= set(x for m in re.findall(r"classList\.(?:add|remove|toggle)\('([^']+)'", src) for x in m.split())
    broad |= used
    # kelas yang dirakit runtime dari string ('chip ' + kind, 'rank p' + n): nama apa pun
    # yang muncul di literal JS dianggap dipakai, supaya A1 tidak berisik. Akibatnya
    # A1 = peringatan "kemungkinan mati", bukan vonis.
    for m in re.findall("'([^']{1,80})'", src):
        broad |= set(re.findall(r"[A-Za-z][A-Za-z0-9_-]*", m))
    if (dead := sorted(defined - broad)):
        bad('A1', 'CSS tidak terpakai: ' + ', '.join('.' + d for d in dead))
    state_prefix = ('view-', 'is-', 'no-', 'desk')
    orphans = sorted(x for x in used - defined if not x.startswith(state_prefix)
                     and re.fullmatch(r'[a-z][a-z0-9_-]*', x))
    if orphans:
        bad('A2', 'class dipakai di markup tapi tidak ada aturan CSS-nya: ' + ', '.join('.' + o for o in orphans))

    # ---- B. ids ---------------------------------------------------------------
    ids = re.findall(r'\bid="([^"]+)"', html_only)
    if (dup := [k for k, v in collections.Counter(ids).items() if v > 1]):
        bad('B1', 'ID duplikat: ' + ', '.join(dup))
    js_ids = set(re.findall(r"getElementById\('([^']+)'\)", src))
    if (missing := sorted(js_ids - set(ids))):
        bad('B2', 'getElementById() ke id yang tidak ada: ' + ', '.join(missing))

    # ---- C. svg sprite contract ----------------------------------------------
    syms = set(re.findall(r'<symbol id="([^"]+)"', html_only))
    uses = {u for u in re.findall(r'<use href="#([^"]+)"', html_only) if not u.startswith((' ', "'"))}
    uses |= set(re.findall(r"icon: '(i-[a-z]+)'", src))
    if (gone := sorted(uses - syms)):
        bad('C1', '<use> menunjuk symbol yang tidak ada: ' + ', '.join(gone))

    # ---- D. a11y basics -------------------------------------------------------
    for m in re.finditer(r'<img\s[^>]*>', html_only):
        if 'alt=' not in m.group(0):
            bad('D1', '<img> tanpa alt: ' + m.group(0)[:70])
    for m in re.finditer(r'<button[^>]*>(.*?)</button>', html_only, re.S):
        inner = re.sub(r'<[^>]+>|&\w+;|\s', '', m.group(1))
        tag = m.group(0)
        if not inner and 'aria-label' not in tag:
            bad('D2', '<button> tanpa label: ' + tag[:90])
    for m in re.finditer(r'<input[^>]*>', html_only):
        t = m.group(0)
        named = 'aria-label=' in t or 'id=' in t
        if not named:
            bad('D3', '<input> tanpa aria-label/id: ' + t[:90])
    if 'lang=' not in src[:400]:
        bad('D4', '<html> tanpa atribut lang')
    if 'role="status"' not in src and 'aria-live' not in src:
        bad('D5', 'tidak ada live region untuk pesan error/proses')

    # ---- D6/D7/D8 · komentar HTML ------------------------------------------------
    # "--" di dalam komentar HTML membuat browser MENUTUP komentar lebih awal, dan
    # sisa teks legenda ikut dirender sebagai konten. Kejadian nyata: hero bergeser
    # 532px ke bawah dan halaman home jadi bisa di-scroll. Diperiksa selamanya.
    for m in re.finditer(r'<!--(.*?)-->', src, re.S):
        if '--' in m.group(1):
            ln = src[:m.start()].count('\n') + 1
            bad('D6', f'komentar HTML memuat "--" (baris {ln}) → browser menutup komentar di situ')
    if src.count('<!--') != src.count('-->'):
        bad('D7', f'komentar tidak seimbang: {src.count("<!--")} <!-- vs {src.count("-->")} -->')
    # periksa region antara <body> SUNGGUH dan .page, pada sumber yang komentarnya
    # sudah dilepas (kata "<body>" di dalam komentar CSS bukan tag body)
    naked = strip_comments(src)
    mb = re.search(r'^<body\b[^>]*>', naked, re.M)
    page = re.search(r'^<div class="page">', naked, re.M)
    if mb and page:
        stray = re.sub(r'<[^>]+>|\s+', ' ', naked[mb.end():page.start()]).strip()
        if stray:
            bad('D8', 'teks lepas sebelum .page — biasanya komentar yang menutup dini: ' + stray[:70])

    # ---- E. security / injection ---------------------------------------------
    if not built:
        sinks = re.findall(r"innerHTML\s*=\s*\n?\s*'([^']*)'\s*\+\s*([A-Za-z0-9_.\[\]()| ']+)", src)
        esc = re.findall(r'esc\(', src)
        if sinks and not esc:
            bad('E1', f'innerHTML concat tanpa escaping ({len(sinks)} titik) — berisiko saat data pindah ke API')

    # ---- F. single-file contract (built only) --------------------------------
    # scan atribut HANYA di markup (string JS memuat `src="` untuk template
    # HTML runtime  ·  itu bukan referensi berkas). url() hanya di <style>.
    region = html_only if built else ''
    ext = re.findall(r'(?:src|href)="(?!data:|#|about:)([^"]{1,80})"', region)
    urls = re.findall(r"url\(([^)]{1,80})\)", css)
    ext += [u.strip('\'\"') for u in urls
            if not u.strip('\'\"').startswith('data:')
            and re.search(r'\.(png|jpe?g|gif|webp|svg|css|js|woff2?)\\b', u)]
    ext = [e for e in ext if 'www.w3.org/2000/svg' not in e]
    if built:
        if any(t in src for t in TOKENS):
            bad('F1', 'TOKEN placeholder belum disubstitusi — file tidak standalone')
        if ext:
            bad('F2', 'referensi eksternal (akan rusak saat di-download): ' + ', '.join(ext[:5]))
        if re.search(r'\bsrc="\.\./|\bhref="\.\./', src):
            bad('F3', 'masih ada path relatif ../')
    else:
        for t in TOKENS:
            if src.count(t) < 1:
                bad('F4', f'template kehilangan token {t} — build.py tidak akan bisa inlining')

    # ---- G. breakpoint contract ---------------------------------------------
    # breakpoint yang menyembunyikan nav / memunculkan drawer HARUS dikenal JS
    blocks = re.split(r'@media([^{]*)[{]', css)   # blok tanpa kurung (@media print) ikut terpisahkan
    nav_bp = set()
    for i in range(1, len(blocks) - 1, 2):
        cond, body_ = blocks[i], blocks[i + 1]
        if re.search(r'[.](burger|drawer|navlinks)[^n]*[{][^}]*display', body_):
            m = re.search(r'max-width:\s*(\d+)px', cond)
            if m:
                nav_bp.add(int(m.group(1)))
    js_bp = {int(x) for x in re.findall(r"matchMedia\('\(max-width:\s*(\d+)px\)'\)", src)}
    for n in sorted(nav_bp):
        if n not in js_bp:
            bad('G1', f'breakpoint {n}px mengatur nav/drawer di CSS, tapi JS tidak '
                      f'menyebut matchMedia("(max-width: {n}px)")  ·  menu bisa menggantung')

    # ---- H. motion contract ----------------------------------------------------
    rm = css[css.index('prefers-reduced-motion'):] if 'prefers-reduced-motion' in css else ''
    if 'scroll-behavior' not in rm and 'scroll-behavior: smooth' in css:
        bad('H1', 'scroll-behavior smooth tidak dinonaktifkan saat prefers-reduced-motion')

    print(f'── {label}  ({path.name}, {len(src.encode())//1024} KB)')
    for p in problems:
        print('   ✗ ' + p)
    if not problems:
        print('   ✓ bersih (A–H lolos)')
    print(f'   info: id={len(ids)} · symbol={len(syms)} · class CSS={len(defined)} · innerHTML={src.count("innerHTML")}')
    return problems


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    pairs = [(args[0], args[1])] if len(args) >= 2 else [
        ('src/index.src.html', 'index.html'),          # landing page
        ('src/dashboard.src.html', 'dashboard.html'),  # dashboard admin
    ]
    all_problems = []
    for src, out in pairs:
        sp, op = ROOT / src, ROOT / out
        if not sp.exists() or not op.exists():
            print(f'── dilewati: {sp.name} / {op.name} tidak ada'); continue
        if '--built' not in sys.argv:
            all_problems += audit(sp, f'TEMPLATE {src}  (jangan di-download)', built=False)
        all_problems += audit(op, f'BUILD    {out}  (yang di-download user)', built=True)
    print('\nHASIL:', 'LOLOS' if not all_problems else f'{len(all_problems)} TEMUAN')
    sys.exit(1 if all_problems else 0)
