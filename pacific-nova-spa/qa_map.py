#!/usr/bin/env python3
"""
Menghasilkan CODEMAP.md — indeks semua penanda [CSS-nn] / [MK-nn] / [JS-nn]
beserta barisnya, untuk DUA template: src/index.src.html (landing) dan
src/dashboard.src.html (dashboard admin). Dijalankan ulang setelah mengedit:

    python3 qa_map.py

Peta ini DIHASILKAN dari kode, jadi nomornya tidak bisa basi seperti komentar
manual. build.py tidak menyentuhnya.
"""
import re
import pathlib
import datetime

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / 'src/index.src.html'
# [MAP-01] · dua berkas source dipetakan: landing dan dashboard. Tambah berkas
# baru cukup di daftar ini; isinya dibaca dari kode, bukan dari komentar manual.
SOURCES = [('Landing page (publik)', 'src/index.src.html'),
           ('Dashboard admin', 'src/dashboard.src.html')]
OUT = ROOT / 'CODEMAP.md'

# Definisi = tag yang DISEGARA disusul penanda tingkat. Rujukan silang
# ("lihat [JS-07]") tidak punya penanda tingkat, jadi tidak ikut terindeks.
TAG = re.compile(r'\[(?P<tag>CSS-\d+[a-z]?|MK-\d+|JS-\d+|BUILD-\d+)\]\s*(?P<sev>★KRITIS|◆PENTING|·)')
BUILD_TAG = re.compile(r'\[(?P<tag>BUILD-\d+)\](?P<sev>)')

def scan(lines, source, pat=TAG):
    """Ambil setiap penanda yang sengaja disusul penanda tingkat."""
    found = []
    for i, line in enumerate(lines, start=1):
        m = pat.search(line)
        if not m:
            continue
        tag = m.group('tag')
        sev = m.group('sev') or '★KRITIS'
        title = line.split(']', 1)[1].lstrip(' *·-—/\t').rstrip(' */\t')
        title = title.replace('★KRITIS ·', '').replace('◆PENTING ·', '').replace('·', '·', 1).strip()
        if len(title) < 5:                      # banner polos: judul di baris berikut
            for nxt in lines[i:i + 2]:
                cand = nxt.strip(' *·-—/')
                if len(cand) > 6 and not TAG.search(cand):
                    title = cand
                    break
        found.append((tag, sev, i, title[:94], source))
    return found


def block_for(label, rel):
    """Satu berkas source -> daftar baris tabel (sudah didedup, diurut per tag)."""
    path = ROOT / rel
    if not path.exists():
        return None, 0, []
    ls = path.read_text(encoding='utf-8').split('\n')
    rows = scan(ls, rel)
    seen, dedup = set(), []
    for r in sorted(rows, key=lambda r: r[0]):
        if (r[4], r[0]) in seen:
            continue
        seen.add((r[4], r[0]))
        dedup.append(r)
    return path, len(ls), dedup


out = [
    '# Peta kode — Pacific Nova (landing + dashboard admin)',
    '',
    f'Dihasilkan otomatis oleh `qa_map.py` dari kode sumber pada {datetime.date.today():%d %b %Y}.  ',
    'Kolom "Baris" menunjuk nomor baris di file source — jangan di-update manual, jalankan ulang skripnya.',
    '',
    '**Cara pakai:** `grep -n "\\[JS-08\\]" src/dashboard.src.html`  ·  '
    '★KRITIS = jangan dipindah tanpa alasan (halaman rusak / file unduhan tidak mandiri)  ·  '
    '◆PENTING = interaksi atau aksesibilitas yang hilang kalau dilepas.',
    '',
]
build_rows = scan((ROOT / 'build.py').read_text(encoding='utf-8').split('\n'), 'build.py', BUILD_TAG)
total = 0
for label, rel in SOURCES:
    path, nlines, rows = block_for(label, rel)
    if path is None:
        out += [f'## {label} — `{rel}` tidak ada', '']
        continue
    total += len(rows)
    out += [f'## {label}', '', f'`{rel}` · {nlines} baris · {len(rows)} penanda', '',
            '| Penanda | Tingkat | Baris | Isi |', '|---|---|---:|---|']
    for tag, sev, no, title, source in rows:
        out.append(f'| `{tag}` | {sev} | {no} | {title} |')
    out.append('')
if build_rows:
    total += 1
    out += ['## Build', '', '| Penanda | Tingkat | Baris | Isi |', '|---|---|---:|---|']
    tag, sev, no, title, source = build_rows[0]
    out.append(f'| `{tag}` | ★KRITIS | {no} | {title} |')
    out.append('')

out += ['## Rantai yang harus jalan berurutan', '', '```',
        'src/index.src.html      ← diedit untuk halaman publik',
        'src/dashboard.src.html  ← diedit untuk papan kerja admin',
        '      │  python3 build.py                                   (landing   → index.html)',
        '      │  python3 build.py --src src/dashboard.src.html --out dashboard.html',
        '      │        (inlining + guard [BUILD-01]: token harus tepat 1x)',
        '      ▼',
        'index.html · dashboard.html   ← file mandiri yang di-download user',
        '      │  python3 qa_audit.py     (A–H, kedua pasangan file)',
        '      │  python3 qa_spec.py      (122 asersi fungsional landing)',
        '      │  python3 qa_dash.py      (200 asersi fungsional dashboard)',
        '      ▼',
        'LOLOS / TEMUAN', '```', '']
OUT.write_text('\n'.join(out), encoding='utf-8')
print(f'CODEMAP.md: {total} penanda terindeks (landing + dashboard + build)')
for label, rel in SOURCES:
    _, _, rows = block_for(label, rel)
    print(f'  {label:24s} {len(rows):3d} penanda')
