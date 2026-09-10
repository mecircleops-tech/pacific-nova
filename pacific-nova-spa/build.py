#!/usr/bin/env python3
"""Build the self-contained Pacific Nova SPA.

src/index.src.html holds the markup + CSS with two placeholders:
  __HERO_BG__   -> the landing hero artwork
  __LOGO_URI__  -> the Pacific Nova logo

Both are inlined as base64 data URIs so the output is ONE html file that works
from a double-click, a USB stick, or any static host — no sidecar assets needed.

    python3 build.py                     # assets/hero-bg.jpg + assets/pacific-nova-logo.png
    python3 build.py --bg assets/hero-bg.png   # lossless artwork, ~3.1 MB output
"""
import argparse, base64, pathlib, mimetypes, sys

ROOT = pathlib.Path(__file__).resolve().parent

def data_uri(path: pathlib.Path) -> str:
    if not path.exists():
        sys.exit(f'build.py: missing asset {path}')
    mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
    return f'data:{mime};base64,' + base64.b64encode(path.read_bytes()).decode()

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument('--src', default=str(ROOT / 'src/index.src.html'))
ap.add_argument('--bg', default=str(ROOT / 'assets/hero-bg.jpg'))
ap.add_argument('--logo', default=str(ROOT / 'assets/pacific-nova-logo.png'))
ap.add_argument('--out', default=str(ROOT / 'index.html'))
a = ap.parse_args()

html = pathlib.Path(a.src).read_text(encoding='utf-8')
for token, path in (('__HERO_BG__', a.bg), ('__LOGO_URI__', a.logo)):
    # [BUILD-01] satu token = satu titik sisip. replace() bersifat global, jadi
    # nama token yang tertulis di komentar/dokumentasi akan ikut diganti dan
    # menggemukkan file build beratus-ratus KB tanpa siapa pun curiga.
    if token not in html:
        sys.exit(f'build.py: {token} not found in {a.src}')
    if (n := html.count(token)) != 1:
        sys.exit(f'build.py: {token} muncul {n}x di {a.src} — harus tepat 1x (lihat [BUILD-01])')
    html = html.replace(token, data_uri(pathlib.Path(path)))

leftover = [t for t in ('__HERO_BG__', '__LOGO_URI__') if t in html]
if leftover:
    sys.exit(f'build.py: unsubstituted placeholders {leftover} — refusing to write a broken file')

out = pathlib.Path(a.out)
out.write_text(html, encoding='utf-8')
kb = out.stat().st_size / 1024
print(f'{out.name}: {kb:,.0f} KB  (1 file, {html.count("data:image/")} inlined images, 0 external requests)')
