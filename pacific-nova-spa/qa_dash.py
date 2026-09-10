#!/usr/bin/env python3
# ══════════════════════════════════════════════════════════════════════════
#  qa_dash.py  ·  QA fungsional dashboard admin (Playwright, chromium)
#
#  [QA-00] Prinsip suite: JANGAN percaya teks UI. Angka yang diuji adalah
#          hasil hitung ulang dari basis data di localStorage (pn.admin.db.v2),
#          lalu dibandingkan dengan yang tampil. Ini yang menangkap bug tipe
#          "NAS tersimpan dua kali" atau "pending ikut dihitung".
#          Blok: S0 boot · S1 login+guard · S2 overview · S3 influencer ·
#          S4 report · S5 create+review (2 langkah) · S6 leaderboard ·
#          S7 manage content · S8 responsif+a11y · S9 ketahanan · S10 file://
#
#  [QA-01] Cara pakai:
#            python3 build.py --src src/dashboard.src.html --out dashboard.html
#            python3 qa_dash.py          # lewat http://localhost:8001 + smoke file://
#          Keluaran: daftar centang + "HASIL QA DASHBOARD: n/n LULUS". Exit 1 bila gagal.
#
#  [QA-02] Data seed yang diasumsikan suite ini (lihat [JS-06] di template):
#            9 influencer · Joshua/0983 total 100 NAS · 3 tier (Blue 0, Gold 600,
#            Platinum 1500) · 4 aktivitas · 10 FAQ · 3 entry pending · 4 status.
#          Kalau seed diganti, ubas asumsi di sini, jangan longgarkan pemeriksaannya.
# ══════════════════════════════════════════════════════════════════════════
import json
import pathlib
import re
import subprocess
import sys
import datetime as dt

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).parent
FILE_URL = (ROOT / 'dashboard.html').as_uri()
HTTP_URL = 'http://localhost:8001/dashboard.html'
DBKEY = 'pn.admin.db.v2'
AUTHKEY = 'pn.admin.auth.v2'
TODAY = dt.date.today()

RESULTS, FAILED = [], []


def check(name, ok, note=''):
    RESULTS.append(name)
    if not ok:
        FAILED.append(f'{name}  {str(note)[:150]}')
        print(f'  ✗ {name}  {str(note)[:150]}')
    return 1 if ok else 0


def iso(d):
    return d.isoformat()


def back(n):
    return iso(TODAY - dt.timedelta(days=n))


def db_of(pg):
    return json.loads(pg.evaluate(f"() => localStorage.getItem('{DBKEY}') || 'null'"))


def nas_of(db, name, verified_only=True, since=None):
    ids = [p['id'] for p in db['people'] if p['name'] == name]
    out = 0
    for r in db['nas']:
        if r['personId'] not in ids or (verified_only and r['status'] != 'verified'):
            continue
        if since and r['date'] < since:
            continue
        out += r['amount']
    return out


def num(s):
    # [QA-03] UI memakai format id-ID (3.245) -> ambil digitnya saja
    d = re.sub(r'\D', '', str(s))
    return int(d) if d else -1


def dnice(iso_str):
    # sama seperti dNice() di app: 8 Sep 2026 (tanpa nol di depan)
    d = dt.date.fromisoformat(iso_str)
    b = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
    return '%d %s %d' % (d.day, b[d.month - 1], d.year)


def cell(pg, sel):
    return (pg.inner_text(sel) or '').strip()


def alls(pg, sel):
    return pg.query_selector_all(sel)


def login(pg, user='admin', pw='pacificnova'):
    pg.fill('#user', user)
    pg.fill('#pass', pw)
    pg.click('#loginForm button[type=submit]')
    pg.wait_for_selector('#view-app:visible', timeout=4000)


def go(pg, route):
    pg.evaluate(f"() => {{ location.hash = '#/{route}'; }}")
    pg.wait_for_timeout(230)


# ══════════════════════════════════════════════════════════════════════════
def run_suite(pg, ctx, base, L, errs, reqs):
    """Semua pemeriksaan berat dijalankan di halaman `pg` yang sudah login."""
    db = db_of(pg)

    # ── S2 · overview ───────────────────────────────────────────────────
    tot = sum(r['amount'] for r in db['nas'] if r['status'] == 'verified')
    pend = [r for r in db['nas'] if r['status'] == 'pending']
    kpi = [num(cell(pg, f'#ovKpi .kpi:nth-child({i}) b')) for i in (1, 2, 3, 4)]
    n = 0
    n += check(f'{L} S2.1 empat KPI terisi angka', all(k > 0 for k in kpi), str(kpi))
    n += check(f'{L} S2.2 KPI total NAS = jumlah verified',
               kpi[1] == tot, f'UI {kpi[1]} vs DB {tot}')
    n += check(f'{L} S2.3 bagan NAS per bulan = 6 kolom', len(alls(pg, '#ovChart .col')) == 6)
    n += check(f'{L} S2.3b keterangan bagan menyebut 6 bulan', '6 bulan' in cell(pg, '#ovChartNote'))
    n += check(f'{L} S2.3c batang bagan benar-benar punya tinggi (bukan nol)',
               pg.evaluate("() => [...document.querySelectorAll('#ovChart .col i')].filter(i => i.getBoundingClientRect().height > 6).length >= 4"))
    n += check(f'{L} S2.3d label bulan terbaca di atas latar terang (bukan putih)',
               pg.evaluate("() => { const s = getComputedStyle(document.querySelector('#ovChart .col span')); return s.color !== 'rgb(255, 255, 255)'; }"))

    n += check(f'{L} S2.4 tinggi batang 0-100%',
               pg.evaluate("""() => [...document.querySelectorAll('#ovChart .col i')]
                     .every(i => { const v = parseFloat(i.style.height); return v >= 0 && v <= 100; })"""))
    n += check(f'{L} S2.5 top 5 orang', len(alls(pg, '#ovTop > .row')) == 5)
    n += check(f'{L} S2.6 daftar pending = pending di DB', len(alls(pg, '#ovPending > .row')) == min(4, len(pend)))
    n += check(f'{L} S2.7 chip sidebar cocok dengan DB',
               cell(pg, '#cntPeople') == str(len(db['people'])) and cell(pg, '#cntPending') == str(len(pend)))
    n += check(f'{L} S2.8 aktivitas terbaru 5 baris', len(alls(pg, '#ovRecent > .row')) == 5)
    n += check(f'{L} S2.9 chip status "Sinkron"', cell(pg, '#syncTxt') == 'tersimpan')
    n += check(f'{L} S2.9b teks keterangan KPI navy kontras (bukan hitam di atas navy)',
               pg.evaluate("() => { const el = document.querySelector('#ovKpi .kpi.navy .muted') || document.querySelector('#ovKpi .kpi.navy .t'); return !!el && /255,\\s*255,\\s*255/.test(getComputedStyle(el).color); }"))
    n += check(f'{L} S2.10 tanpa NaN/undefined',
               'NaN' not in pg.inner_text('#page-overview') and 'undefined' not in pg.inner_text('#page-overview'))

    # ── S3 · data influencer ────────────────────────────────────────────
    go(pg, 'influencers')
    n += check(f'{L} S3.1 baris = jumlah orang', len(alls(pg, '#pRows tr')) == len(db['people']))
    bad = pg.evaluate("""() => { const rows = [...document.querySelectorAll('#pRows tr')];
          return rows.map(r => r.innerText); }""")
    per_person = {}
    for txt in bad:
        nm = txt.split('\n')[1] if False else None
    # bandingkan tiap baris: angka NAS di UI vs jumlah manual verified rows orang itu
    mism = []
    for i in range(1, len(db['people']) + 1):
        nm = cell(pg, f'#pRows tr:nth-child({i}) .who2 b')
        ui = num(cell(pg, f'#pRows tr:nth-child({i}) .nasbig'))
        want = nas_of(db, nm)
        if ui != want:
            mism.append(f'{nm}: UI {ui} vs DB {want}')
    n += check(f'{L} S3.2 kolom NAS = penjumlahan entry terverifikasi (9 orang)', not mism, '; '.join(mism[:2]))
    jrow = pg.evaluate("""() => [...document.querySelectorAll('#pRows tr')]
          .find(t => t.innerText.includes('Joshua'))?.innerText || ''""")
    n += check(f'{L} S3.3 kontrak landing: Joshua · 0983 · 100 NAS · Blue Nova',
               '0983' in jrow and '100' in jrow and 'Blue Nova' in jrow, jrow.replace('\n', ' | ')[:130])
    n += check(f'{L} S3.4 jumlah entry per orang tertulis',
               'entry' in jrow, jrow.replace('\n', ' | ')[:80])
    pg.fill('#pSearch', '0983')
    pg.wait_for_timeout(160)
    n += check(f'{L} S3.5 cari lewat member number', len(alls(pg, '#pRows tr')) == 1)
    pg.fill('#pSearch', 'tidak-ada-yang-ini')
    pg.wait_for_timeout(160)
    n += check(f'{L} S3.6 tanpa hasil → pesan kosong yang jelas', pg.is_visible('#pRows .empty'))
    pg.fill('#pSearch', '')
    pg.select_option('#pTier', value='Gold Nova')
    pg.wait_for_timeout(160)
    g = alls(pg, '#pRows tr')
    n += check(f'{L} S3.7 filter tier menyisakan hanya tier itu', 0 < len(g) < 9 and all('Gold Nova' in r.inner_text() for r in g), str(len(g)))
    pg.select_option('#pStatus', label='Active')
    pg.wait_for_timeout(160)
    n += check(f'{L} S3.8 dua filter digabung (AND)',
               all('Active' in r.inner_text() and 'Gold Nova' in r.inner_text() for r in alls(pg, '#pRows tr')))
    pg.select_option('#pTier', index=0)
    pg.select_option('#pStatus', index=0)
    pg.wait_for_timeout(160)
    n += check(f'{L} S3.9 reset filter → penuh lagi', len(alls(pg, '#pRows tr')) == len(db['people']))
    foot = cell(pg, '#pFoot .nasbig')
    want = sum(nas_of(db, cell(pg, f'#pRows tr:nth-child({i}) .who2 b')) for i in range(1, len(db['people']) + 1))
    n += check(f'{L} S3.10 total di footer = jumlah kolom NAS',
               num(foot) == want, f'{foot} vs {want}')

    # tambah orang
    pg.click('#pAdd')
    pg.wait_for_selector('#fName', timeout=2000)
    pg.fill('#fName', 'Rani Puspita')
    pg.fill('#fNo', 'NV-2026-009099')
    pg.fill('#fHandle', '@ranipsp')
    pg.select_option('#fStatus', label='New member')
    pg.click('#fSave')
    pg.wait_for_timeout(300)
    db2 = db_of(pg)
    n += check(f'{L} S3.11 tambah orang → DB + tabel',
               any(p['name'] == 'Rani Puspita' for p in db2['people'])
               and len(alls(pg, '#pRows tr')) == len(db['people']) + 1)
    last = pg.evaluate("() => [...document.querySelectorAll('#pRows tr')].pop().innerText")
    n += check(f'{L} S3.12 orang baru: 0 NAS, tier dasar', '0' in last and 'Blue Nova' in last, last.replace('\n', ' | ')[:110])
    n += check(f'{L} S3.13 modal tertutup, toast muncul',
               not pg.is_visible('#fName') and pg.is_visible('#toast'))
    pg.click('#pAdd')
    pg.wait_for_selector('#fName', timeout=2000)
    pg.fill('#fName', 'X')
    pg.fill('#fNo', 'NV-2026-009099')
    pg.click('#fSave')
    pg.wait_for_timeout(150)
    n += check(f'{L} S3.14 validasi nama terlalu pendek', 'minimal 2' in cell(pg, '#fMsg'))
    pg.fill('#fName', 'Duplikat Ya')
    pg.click('#fSave')
    pg.wait_for_timeout(150)
    n += check(f'{L} S3.15 validasi member number kembar', 'sudah dipakai' in cell(pg, '#fMsg'))
    n += check(f'{L} S3.16 ditolak → tidak masuk DB', not any(p['name'] == 'Duplikat Ya' for p in db_of(pg)['people']))
    pg.click('.mask [data-close]')
    pg.wait_for_timeout(150)
    pg.evaluate("""() => [...document.querySelectorAll('#pRows tr')]
          .find(t => t.innerText.includes('Rani')).querySelector('[data-act=edit]').click()""")
    pg.wait_for_selector('#fName', timeout=2000)
    pg.fill('#fName', 'Rani Puspitawati')
    pg.click('#fSave')
    pg.wait_for_timeout(300)
    n += check(f'{L} S3.17 edit nama tersimpan',
               'Rani Puspitawati' in pg.inner_text('#pRows')
               and any(p['name'] == 'Rani Puspitawati' for p in db_of(pg)['people']))
    n += check(f'{L} S3.18 edit orang tidak menyentuh ledger',
               len(db_of(pg)['nas']) == len(db['nas']))
    n += check(f'{L} S3.19 hint menyebut cara hitung NAS', 'dihitung otomatis' in cell(pg, '#pHint'))
    pg.evaluate("""() => [...document.querySelectorAll('#pRows tr')]
          .find(t => t.innerText.includes('Joshua')).querySelector('[data-act=hist]').click()""")
    pg.wait_for_selector('.mask .rep', timeout=2000)
    hist_n = pg.evaluate("() => document.querySelectorAll('#modalBody .rep, .mask .rep').length")
    want_n = len([r for r in db_of(pg)['nas'] if r['personId'] in
                  [p['id'] for p in db_of(pg)['people'] if p['name'] == 'Joshua']])
    n += check(f'{L} S3.20 modal riwayat menampilkan seluruh entry orang itu', hist_n == want_n, f'{hist_n} vs {want_n}')
    pg.keyboard.press('Escape')
    pg.wait_for_timeout(180)
    n += check(f'{L} S3.21 Esc menutup modal', not pg.is_visible('.mask .rep'))
    rows_before = len(db_of(pg)['nas'])
    pg.evaluate("""() => [...document.querySelectorAll('#pRows tr')]
          .find(t => t.innerText.includes('Rani')).querySelector('[data-act=del]').click()""")
    pg.wait_for_selector('#doDel', timeout=2000)
    n += check(f'{L} S3.22 hapus butuh konfirmasi dulu', pg.inner_text('#modalBody').count('dihapus') >= 1)
    pg.click('#doDel')
    pg.wait_for_timeout(300)
    db3 = db_of(pg)
    n += check(f'{L} S3.23 hapus → orang hilang, ledger bersih',
               'Rani' not in pg.inner_text('#pRows') and len(db3['people']) == len(db['people'])
               and len(db3['nas']) == rows_before)
    n += check(f'{L} S3.24 caption tabel ada (a11y)',
               pg.evaluate("() => /Daftar influencer/.test(document.querySelector('#page-influencers caption').textContent)"))

    # ── S4 · NAS report ─────────────────────────────────────────────────
    go(pg, 'report')
    db = db_of(pg)
    n += check(f'{L} S4.1 semua entry tampil', len(alls(pg, '#rRows tr')) == len(db['nas']))
    want_seq = [dnice(r['date']) for r in sorted(db['nas'], key=lambda r: r['date'], reverse=True)][:12]
    got_seq = [cell(pg, f'#rRows tr:nth-child({i}) td:nth-child(1)').splitlines()[0] for i in range(1, 13)]
    n += check(f'{L} S4.2 urut tanggal terbaru lebih dulu (12 baris pertama)', got_seq == want_seq, str(got_seq[:3]) + ' vs ' + str(want_seq[:3]))
    ver = sum(r['amount'] for r in db['nas'] if r['status'] == 'verified')
    n += check(f'{L} S4.3 KPI verified = jumlah manual',
               num(cell(pg, '#rpKpi .kpi:nth-child(2) b')) == ver)
    n += check(f'{L} S4.4 KPI menunggu = pending DB',
               cell(pg, '#rpKpi .kpi:nth-child(3) b') == str(len([r for r in db['nas'] if r['status'] == 'pending'])))
    n += check(f'{L} S4.5 KPI lampiran = entry dengan attachment',
               cell(pg, '#rpKpi .kpi:nth-child(4) b') == str(len([r for r in db['nas'] if r.get('attachment')])))
    pg.select_option('#rStatus', index=1)
    pg.wait_for_timeout(180)
    pr = alls(pg, '#rRows tr')
    n += check(f'{L} S4.6 filter status hanya menampilkan status itu',
               len(pr) == len([r for r in db['nas'] if r['status'] == 'pending'])
               and all('menunggu' in r.inner_text().lower() for r in pr), str(len(pr)))
    pg.select_option('#rStatus', index=0)
    pg.wait_for_timeout(180)
    pg.select_option('#rPerson', label='Joshua')
    pg.wait_for_timeout(180)
    jr = alls(pg, '#rRows tr')
    want_j = len([r for r in db['nas'] if r['personId'] in [p['id'] for p in db['people'] if p['name'] == 'Joshua']])
    n += check(f'{L} S4.7 filter per influencer', len(jr) == want_j and all('Joshua' in r.inner_text() for r in jr), str(len(jr)))
    pg.select_option('#rPerson', index=0)
    pg.fill('#rSearch', 'campaign')
    pg.wait_for_timeout(180)
    want_c = len([r for r in db['nas'] if 'campaign' in r['activity'].lower()])
    n += check(f'{L} S4.8 pencarian teks cocok dengan isi ledger', len(alls(pg, '#rRows tr')) == want_c, str(want_c))
    pg.fill('#rSearch', '')
    pg.wait_for_timeout(150)
    # tandai satu baris dengan catatan unik supaya bisa dilacak di DB
    pg.evaluate("""() => { const tr = [...document.querySelectorAll('#rRows tr')]
          .find(t => /menunggu/i.test(t.innerText)); tr.querySelector('[data-act=note]').click(); }""")
    pg.wait_for_selector('#ntIn', timeout=2000)
    pg.fill('#ntIn', 'QA-MARK')
    pg.click('#ntSave')
    pg.wait_for_timeout(300)
    mark = [r for r in db_of(pg)['nas'] if r['note'] == 'QA-MARK']
    if not check(f'{L} S4.9 catatan tersimpan ke baris yang benar', len(mark) == 1, str(len(mark))):
        mark = [{'id': None}]
    mid = mark[0]['id']
    kpi_before = num(cell(pg, '#rpKpi .kpi:nth-child(2) b'))
    amt = mark[0]['amount']
    pg.evaluate(f"""() => {{ const tr = [...document.querySelectorAll('#rRows tr')]
          .find(t => t.innerText.includes('QA-MARK')); tr.querySelector('[data-act=ok]').click(); }}""")
    pg.wait_for_timeout(350)
    now = [r for r in db_of(pg)['nas'] if r['id'] == mid][0]
    n += check(f'{L} S4.10 verifikasi mengubah status di basis data', now['status'] == 'verified')
    n += check(f'{L} S4.11 verifikasi menaikkan total verified tepat +nominal',
               num(cell(pg, '#rpKpi .kpi:nth-child(2) b')) == kpi_before + amt,
               f'{amt}')
    n += check(f'{L} S4.12 baris tidak lagi punya tombol "verifikasi"',
               pg.evaluate("""() => { const tr = [...document.querySelectorAll('#rRows tr')]
                     .find(t => t.innerText.includes('QA-MARK')); return !tr.querySelector('[data-act=ok]'); }"""))
    pg.evaluate("""() => { const tr = [...document.querySelectorAll('#rRows tr')]
          .find(t => t.innerText.includes('QA-MARK')); tr.querySelector('[data-act=undo]').click(); }""")
    pg.wait_for_timeout(350)
    now = [r for r in db_of(pg)['nas'] if r['id'] == mid][0]
    n += check(f'{L} S4.13 undo verifikasi mengembalikan status & angka',
               now['status'] == 'pending'
               and num(cell(pg, '#rpKpi .kpi:nth-child(2) b')) == kpi_before)
    n += check(f'{L} S4.14 orang yang relevan: NAS-nya ikut turun lagi',
               nas_of(db_of(pg), [p for p in db_of(pg)['people'] if p['id'] == now['personId']][0]['name']) ==
               nas_of(db, [p for p in db_of(pg)['people'] if p['id'] == now['personId']][0]['name']))
    pg.evaluate("""() => { const tr = [...document.querySelectorAll('#rRows tr')]
          .find(t => t.innerText.includes('QA-MARK')); tr.querySelector('[data-act=del]').click(); }""")
    pg.wait_for_selector('#doDel', timeout=2000)
    pg.click('#doDel')
    pg.wait_for_timeout(300)
    n += check(f'{L} S4.15 hapus entry mengurangi DB tepat 1', len(db_of(pg)['nas']) == len(db['nas']) - 1)
    n += check(f'{L} S4.16 lampiran bisa dibuka dari tabel',
               pg.evaluate("""() => { const b = document.querySelector('#rRows [data-act=file]');
                     if (!b) return false; b.click(); return true; }"""))
    pg.wait_for_timeout(250)
    n += check(f'{L} S4.17 modal bukti menyebut nama berkas', pg.is_visible('.mask') and ('.jpg' in pg.inner_text('.mask') or '.pdf' in pg.inner_text('.mask')))
    pg.keyboard.press('Escape')
    pg.wait_for_timeout(200)
    try:
        with pg.expect_download(timeout=5000) as dl:
            pg.click('#rCsv')
        fn = dl.value.suggested_filename
        n += check(f'{L} S4.18 ekspor CSV menghasilkan berkas .csv', fn.startswith('nas-report-') and fn.endswith('.csv'), fn)
    except Exception as e:
        n += check(f'{L} S4.18 ekspor CSV menghasilkan berkas .csv', False, str(e)[:90])

    # ── S5 · create NAS + verifikasi ulang ──────────────────────────────
    go(pg, 'create')
    db = db_of(pg)
    josh_before = nas_of(db, 'Joshua')
    n += check(f'{L} S5.1 form tampil + tanggal default hari ini',
               pg.is_visible('#nasForm') and pg.input_value('#nDate') == iso(TODAY))
    n += check(f'{L} S5.2 pilihan nama = daftar influencer (satu sumber data)',
               len(alls(pg, '#nPerson option')) - 1 == len(db['people']))
    n += check(f'{L} S5.3 kartu referensi activity type', len(alls(pg, '#actList .rep')) == len(db['activities']))
    n += check(f'{L} S5.4 nominal terisi otomatis + ada keterangannya',
               pg.input_value('#nAmount').isdigit() and 'default' in cell(pg, '#amountNote').lower())
    pg.select_option('#nPerson', index=0)   # opsi kosong
    pg.click('#nSubmit')
    pg.wait_for_timeout(200)
    n += check(f'{L} S5.5 tanpa nama → ditolak sebelum review',
               pg.is_visible('#nasErr') and pg.evaluate("() => document.getElementById('nasPreview').hidden"))
    pg.select_option('#nPerson', index=1)   # orang ke-1 = Joshua
    pg.fill('#nAmount', '0')
    pg.click('#nSubmit')
    pg.wait_for_timeout(200)
    n += check(f'{L} S5.6 NAS 0 ditolak', '9999' in cell(pg, '#nasErr'))
    pg.fill('#nAmount', '25000')
    pg.click('#nSubmit')
    pg.wait_for_timeout(200)
    n += check(f'{L} S5.7 NAS di atas plafon ditolak', '9999' in cell(pg, '#nasErr'))
    pg.fill('#nAmount', '45')
    pg.fill('#nDate', back(-4))
    pg.click('#nSubmit')
    pg.wait_for_timeout(200)
    n += check(f'{L} S5.8 tanggal masa depan ditolak', 'belum terjadi' in cell(pg, '#nasErr'))
    pg.fill('#nDate', back(2))
    pg.select_option('#nAct', value='campaign')
    pg.wait_for_timeout(150)
    n += check(f'{L} S5.9 ganti activity type → nominal ikut default barunya',
               pg.input_value('#nAmount') == '25', pg.input_value('#nAmount'))
    pg.fill('#nAmount', '30')
    pg.fill('#nNote', 'tiket dua panggung')
    png = ROOT / 'assets' / 'qa-attach.png'
    pg.set_input_files('#nFile', str(png))
    pg.wait_for_timeout(250)
    n += check(f'{L} S5.10 lampiran tercatat namanya di form', png.name in cell(pg, '#nFileNote'))
    pg.click('#nSubmit')
    pg.wait_for_timeout(300)
    n += check(f'{L} S5.11 submit → panel re-verification, form disembunyikan',
               pg.is_visible('#nasPreview') and pg.evaluate("() => document.getElementById('nasForm').hidden"))
    rv = pg.inner_text('#nasPreview')
    n += check(f'{L} S5.12 review menyebut orang + member number',
               'Joshua' in rv and '0983' in rv)
    n += check(f'{L} S5.13 review menyebut activity type + tanggal input',
               'Campaign Bonus' in rv and dnice(back(2)) in rv, rv[:170])
    n += check(f'{L} S5.14 review menyebut NAS yang AKAN dicatat', '+30 NAS' in rv, rv[:120])
    n += check(f'{L} S5.15 review menampilkan NAS tercatat saat ini', str(josh_before) in cell(pg, '#rvDelta'))
    n += check(f'{L} S5.16 review menampilkan hasil sesudah diverifikasi',
               str(josh_before + 30) in cell(pg, '#rvDelta'), cell(pg, '#rvDelta'))
    n += check(f'{L} S5.17 review menampilkan riwayat entry orang itu',
               'sudah tercatat' in cell(pg, '#rvHistory').lower())
    n += check(f'{L} S5.18 review menampilkan lampiran + status awal',
               png.name in cell(pg, '#rvData') and 'menunggu verifikasi' in cell(pg, '#rvData'))
    n += check(f'{L} S5.18b pratinjau gambar lampiran ikut tampil di review',
               pg.evaluate("() => { const i = document.querySelector('#rvData img'); return !!i && i.naturalWidth > 0; }"))
    n += check(f'{L} S5.19 tombol lanjut berbunyi "Lanjutkan prosesnya"',
               cell(pg, '#rvOk') == 'Lanjutkan prosesnya')
    n += check(f'{L} S5.20 tombol batal tersedia (koreksi masih mungkin)', pg.is_visible('#rvBack'))
    n += check(f'{L} S5.21 commit BELUM terjadi saat review tampil',
               len(db_of(pg)['nas']) == len(db['nas']))
    pg.click('#rvBack')
    pg.wait_for_timeout(250)
    n += check(f'{L} S5.22 "Kembali" → form tampil lagi, DB tetap',
               pg.evaluate("() => !document.getElementById('nasForm').hidden") and len(db_of(pg)['nas']) == len(db['nas']))
    n += check(f'{L} S5.23 isian form tidak hilang saat kembali',
               pg.input_value('#nNote') == 'tiket dua panggung')
    pg.click('#nSubmit')
    pg.wait_for_timeout(250)
    n += check(f'{L} S5.24 masuk review lagi dengan data sama', pg.is_visible('#rvOk') and '+30 NAS' in pg.inner_text('#nasPreview'))
    pg.click('#rvOk')
    pg.wait_for_timeout(450)
    db5 = db_of(pg)
    added = [r for r in db5['nas'] if r['note'] == 'tiket dua panggung']
    n += check(f'{L} S5.25 lanjut → tepat 1 entry masuk DB', len(added) == 1, str(len(added)))
    n += check(f'{L} S5.26 entry hasil create berstatus pending',
               added and added[0]['status'] == 'pending')
    n += check(f'{L} S5.27 nominal + tanggal + orang tercatat persis seperti direview',
               added and added[0]['amount'] == 30 and added[0]['date'] == back(2)
               and added[0]['personId'] in [p['id'] for p in db5['people'] if p['name'] == 'Joshua'])
    n += check(f'{L} S5.28 attachment tersimpan sebagai metadata (bukan path lokal)',
               added and added[0]['attachment'] and added[0]['attachment']['name'] == png.name
               and 'KB' in str(added[0]['attachment'].get('size', '')))
    n += check(f'{L} S5.29 form direset untuk entry berikutnya',
               pg.evaluate("() => !document.getElementById('nasForm').hidden") and pg.input_value('#nNote') == '')
    n += check(f'{L} S5.30 admin diarahkan ke report + baris baru disorot',
               pg.is_visible('#page-report')
               and pg.evaluate("() => !!document.querySelector('#rRows tr.flash')"))
    n += check(f'{L} S5.31 toast menyebut nilai dan statusnya', pg.is_visible('#toast') and 'menunggu verifikasi' in pg.inner_text('#toast'))
    go(pg, 'influencers')
    jrow2 = num(pg.evaluate("() => [...document.querySelectorAll('#pRows tr')].find(t => t.innerText.includes('Joshua')).querySelector('.nasbig').innerText"))
    n += check(f'{L} S5.32 pending TIDAK dihitung ke NAS (kolom masih lama)', jrow2 == josh_before, jrow2)
    go(pg, 'report')
    pg.evaluate("""() => { const tr = [...document.querySelectorAll('#rRows tr')]
          .find(t => t.innerText.includes('tiket dua panggung')); tr.querySelector('[data-act=ok]').click(); }""")
    pg.wait_for_timeout(400)
    go(pg, 'influencers')
    jrow3 = num(pg.evaluate("() => [...document.querySelectorAll('#pRows tr')].find(t => t.innerText.includes('Joshua')).querySelector('.nasbig').innerText"))
    n += check(f'{L} S5.33 setelah diverifikasi, NAS naik tepat +30', jrow3 == josh_before + 30, jrow3)
    tier_now = pg.evaluate("""() => [...document.querySelectorAll('#pRows tr')]
          .find(t => t.innerText.includes('Joshua')).querySelector('td:nth-child(3)').innerText""")
    n += check(f'{L} S5.34 tier ikut dihitung ulang dari total baru', 'Blue Nova' in tier_now, tier_now)
    n += check(f'{L} S5.35 nol request eksternal sepanjang alur create',
               all(u.startswith(('http://localhost:8001', 'data:', 'blob:', 'file:')) for u in reqs),
               str([u for u in reqs if not u.startswith(('http://localhost', 'data:', 'blob:', 'file:'))][:2]))

    # ── S6 · leaderboard ────────────────────────────────────────────────
    go(pg, 'leaderboard')
    db = db_of(pg)
    n += check(f'{L} S6.1 podium tiga besar', len(alls(pg, '#lbPodium .rank')) == 3)
    vals = [num(cell(pg, f'#lbRows .rank:nth-child({i}) .val'))
            for i in range(1, len(alls(pg, '#lbRows .rank')) + 1)]
    n += check(f'{L} S6.2 peringkat menurun', vals == sorted(vals, reverse=True), str(vals[:5]))
    top_name = cell(pg, '#lbRows .rank:nth-child(1) b')
    best = max(db['people'], key=lambda p: nas_of(db, p['name']))
    n += check(f'{L} S6.3 posisi 1 = peraih NAS terbesar', best['name'] in top_name, top_name)
    n += check(f'{L} S6.4 angka podium = angka daftar',
               num(cell(pg, '#lbPodium .rank:nth-child(1) .val')) == vals[0])
    cut = back(30)
    want30 = nas_of(db, 'Joshua', since=cut)
    pg.click('#page-leaderboard .tabs button[data-period="30"]')
    pg.wait_for_timeout(300)
    got30 = pg.evaluate("""() => { const r = [...document.querySelectorAll('#lbRows .rank')]
          .find(x => x.innerText.includes('Joshua'));
          return r ? parseInt(r.querySelector('.val').innerText.replace(/\\D/g, ''), 10) : -1; }""")
    n += check(f'{L} S6.5 periode 30 hari = jumlah manual dalam rentang', got30 == want30, f'{got30} vs {want30} ({cut})')
    n += check(f'{L} S6.6 tab aktif pindah',
               pg.get_attribute('#page-leaderboard .tabs button[data-period="30"]', 'aria-selected') == 'true'
               and pg.get_attribute('#page-leaderboard .tabs button[data-period="all"]', 'aria-selected') == 'false')
    n += check(f'{L} S6.7 judul periode ikut berubah', '30 hari' in cell(pg, '#lbCount'))
    pg.click('#page-leaderboard .tabs button[data-period="all"]')
    pg.wait_for_timeout(300)
    n += check(f'{L} S6.8 "semua waktu" >= angka 30 hari',
               num(cell(pg, '#lbRows .rank:nth-child(1) .val')) >= got30)
    n += check(f'{L} S6.9 bar progres terpotong di 100%',
               pg.evaluate("""() => [...document.querySelectorAll('#lbRows .bar i')]
                     .every(i => parseFloat(i.style.width) <= 100)"""))
    n += check(f'{L} S6.10 petunjuk menuju tier berikutnya hadir',
               'NAS lagi' in pg.inner_text('#lbPodium') or 'tertinggi' in pg.inner_text('#lbPodium'))

    # ── S7 · manage content ─────────────────────────────────────────────
    go(pg, 'content')
    db = db_of(pg)
    n += check(f'{L} S7.1 empat tab + FAQ aktif',
               len(alls(pg, '#page-content .tabs button')) == 4 and pg.is_visible('#tab-faq'))
    n += check(f'{L} S7.2 baris FAQ = DB', len(alls(pg, '#tab-faq .panel[data-i]')) == len(db['content']['faq']))
    pg.fill('#tab-faq .panel[data-i="0"] [data-k="q"]', 'Berapa harga tiket pesawat?')
    pg.wait_for_timeout(200)
    n += check(f'{L} S7.3 editan HANYA di draft sampai disimpan',
               'Berapa harga tiket pesawat' not in json.dumps(db_of(pg)['content'])
               and 'belum disimpan' in cell(pg, '#syncChip'))
    pg.click('#page-content .tabs button[data-tab="about"]')
    pg.wait_for_timeout(180)
    pg.click('#page-content .tabs button[data-tab="faq"]')
    pg.wait_for_timeout(180)
    n += check(f'{L} S7.4 berpindah tab tidak menghapus draf',
               pg.input_value('#tab-faq .panel[data-i="0"] [data-k="q"]') == 'Berapa harga tiket pesawat?')
    before = len(db['content']['faq'])
    pg.click('#faqAdd')
    pg.wait_for_timeout(200)
    n += check(f'{L} S7.5 tambah FAQ: +1 di layar, DB tetap',
               len(alls(pg, '#tab-faq .panel[data-i]')) == before + 1 and len(db_of(pg)['content']['faq']) == before)
    last = len(alls(pg, '#tab-faq .panel[data-i]')) - 1
    pg.evaluate(f"() => document.querySelectorAll('#tab-faq .panel[data-i]')[{last}].querySelector('[data-mv=up]').click()")
    pg.wait_for_timeout(250)
    n += check(f'{L} S7.6 tombol naik memindahkan urutan (FAQ baru naik satu)',
               'Pertanyaan baru' in pg.input_value(f'#tab-faq .panel[data-i="{last - 1}"] [data-k="q"]'))
    pg.evaluate("() => document.querySelectorAll('#tab-faq .panel[data-i]')[1].querySelector('[data-rm]').click()")
    pg.wait_for_timeout(200)
    n += check(f'{L} S7.7 hapus FAQ di draft', len(alls(pg, '#tab-faq .panel[data-i]')) == before)
    pg.fill('#tab-faq .panel[data-i="0"] [data-k="q"]', 'abc')
    pg.click('#cSave')
    pg.wait_for_timeout(250)
    n += check(f'{L} S7.8 simpan ditolak bila ada pertanyaan terlalu pendek', 'pendek' in pg.inner_text('#toast'))
    pg.fill('#tab-faq .panel[data-i="0"] [data-k="q"]', 'Berapa harga tiket pesawat?')
    pg.select_option('#tab-faq .panel[data-i="0"] [data-k="cat"]', index=2)
    pg.click('#cSave')
    pg.wait_for_timeout(350)
    db = db_of(pg)
    n += check(f'{L} S7.9 simpan → FAQ baru masuk DB', db['content']['faq'][0]['q'] == 'Berapa harga tiket pesawat?')
    n += check(f'{L} S7.10 kategori FAQ ikut tersimpan', db['content']['faq'][0]['cat'] != 'nas')
    n += check(f'{L} S7.11 chip kembali "Sinkron"', cell(pg, '#syncTxt') == 'tersimpan')
    pg.reload()
    pg.wait_for_timeout(600)
    if pg.is_visible('#loginForm'):
        login(pg)
    go(pg, 'content')
    n += check(f'{L} S7.12 reload: konten tetap (localStorage)',
               pg.input_value('#tab-faq .panel[data-i="0"] [data-k="q"]') == 'Berapa harga tiket pesawat?')
    pg.click('#page-content .tabs button[data-tab="about"]')
    pg.wait_for_timeout(200)
    db = db_of(pg)
    n += check(f'{L} S7.13 About: lede = DB, statistik & langkah lengkap',
               pg.input_value('#aLede') == db['content']['about']['lede']
               and len(alls(pg, '#aStats .grid2')) == len(db['content']['about']['stats'])
               and len(alls(pg, '#aSteps .rep')) == len(db['content']['about']['steps']))
    pg.fill('#aStats .grid2[data-i="0"] [data-k="v"]', '12 mitra')
    pg.fill('#aSteps .rep[data-i="0"] [data-k="t"]', 'Daftar jadi anggota')
    pg.click('#cSave')
    pg.wait_for_timeout(350)
    db = db_of(pg)
    n += check(f'{L} S7.14 statistik + langkah About tersimpan',
               db['content']['about']['stats'][0]['v'] == '12 mitra'
               and db['content']['about']['steps'][0]['t'] == 'Daftar jadi anggota')
    n += check(f'{L} S7.15 ambang tier tampil dan bisa diubah',
               pg.input_value('#aTiers .rep[data-i="1"] [data-k="min"]') == '600',
               pg.input_value('#aTiers .rep[data-i="1"] [data-k="min"]'))
    pg.fill('#aTiers .rep[data-i="1"] [data-k="min"]', '20')
    pg.fill('#aTiers .rep[data-i="1"] [data-k="note"]', 'Ambang uji QA')
    pg.click('#cSave')
    pg.wait_for_timeout(350)
    db = db_of(pg)
    n += check(f'{L} S7.16 ambang tier tersimpan', db['tiers'][1]['min'] == 20)
    go(pg, 'influencers')
    jrow = pg.evaluate("""() => [...document.querySelectorAll('#pRows tr')]
          .find(t => t.innerText.includes('Joshua')).innerText""")
    n += check(f'{L} S7.17 tier di tabel mengikuti ambang baru (sumber kebenaran tunggal)',
               'Gold Nova' in jrow and '130' in jrow, jrow.replace('\n', ' | ')[:120])
    go(pg, 'content')
    pg.click('#page-content .tabs button[data-tab="about"]')
    pg.wait_for_timeout(200)
    pg.fill('#aTiers .rep[data-i="1"] [data-k="min"]', '600')
    pg.fill('#aTiers .rep[data-i="1"] [data-k="note"]', 'Kursi tamu & jendela booking lebih panjang.')
    pg.click('#cSave')
    pg.wait_for_timeout(350)
    go(pg, 'influencers')
    n += check(f'{L} S7.18 kembalikan ambang → Joshua Blue Nova lagi',
               'Blue Nova' in pg.evaluate("""() => [...document.querySelectorAll('#pRows tr')]
                     .find(t => t.innerText.includes('Joshua')).innerText"""))
    go(pg, 'content')
    pg.click('#page-content .tabs button[data-tab="contact"]')
    pg.wait_for_timeout(200)
    db = db_of(pg)
    c = db['content']['contact']
    n += check(f'{L} S7.19 contact: 6 field terisi dari DB',
               pg.input_value('#cEmail') == c['email'] and pg.input_value('#cPhone') == c['phone']
               and pg.input_value('#cLounge') == c['lounge'] and pg.input_value('#cEmailNote') == c['emailNote']
               and pg.input_value('#cPhoneNote') == c['phoneNote'] and pg.input_value('#cLoungeNote') == c['loungeNote'])
    pg.fill('#cEmail', 'halo@pacificnova.example')
    pg.fill('#cPhone', 'bukan nomor')
    pg.wait_for_timeout(150)
    n += check(f'{L} S7.20 telepon tidak valid ditandai aria-invalid',
               pg.get_attribute('#cPhone', 'aria-invalid') == 'true')
    pg.fill('#cPhone', '+62 21 3000 8888')
    pg.wait_for_timeout(150)
    n += check(f'{L} S7.21 telepon valid → aria-invalid false',
               pg.get_attribute('#cPhone', 'aria-invalid') == 'false')
    pg.click('#cSave')
    pg.wait_for_timeout(350)
    db = db_of(pg)
    n += check(f'{L} S7.22 contact tersimpan', db['content']['contact']['email'] == 'halo@pacificnova.example'
               and db['content']['contact']['phone'] == '+62 21 3000 8888')
    pg.click('#page-content .tabs button[data-tab="benefit"]')
    pg.wait_for_timeout(250)
    tiers = [t['name'] for t in db['tiers']]
    n += check(f'{L} S7.23 benefit: satu panel per tier',
               len(alls(pg, '#bByTier .panel[data-tier]')) == len(tiers))
    for i, tn in enumerate(tiers):
        want = len(db['content']['benefits'].get(tn, []))
        got = pg.evaluate(f"() => document.querySelectorAll('#bByTier .panel[data-tier]')[{i}].querySelectorAll('.rep').length")
        check(f'{L} S7.24.{i} panel {tn}: {want} benefit', got == want, f'{got}')
    bn = tiers[0]
    sel = f"#bByTier .panel[data-tier='{bn}'] .rep"
    pg.evaluate(f"""() => {{ const el = document.querySelector("{sel} [data-k=label]");
          el.value = 'Prioritas kursi'; el.dispatchEvent(new Event('input', {{ bubbles: true }}));
          const m = document.querySelector("{sel} [data-k=meta]");
          m.value = 'gratis'; m.dispatchEvent(new Event('input', {{ bubbles: true }})); }}""")
    pg.wait_for_timeout(200)
    pg.evaluate(f"""() => document.querySelectorAll('#bByTier .panel[data-tier]')[0].querySelector('[data-add]').click()""")
    pg.wait_for_timeout(250)
    n += check(f'{L} S7.25 tambah benefit di draft',
               len(alls(pg, f'{sel}')) == len(db['content']['benefits'][bn]) + 1)
    pg.evaluate(f"""() => {{ const s = document.querySelector("{sel} [data-k=icon]");
          s.value = 'i-gem'; s.dispatchEvent(new Event('change', {{ bubbles: true }})); }}""")
    pg.wait_for_timeout(200)
    pg.click('#cSave')
    pg.wait_for_timeout(350)
    db = db_of(pg)
    b0 = db['content']['benefits'][bn]
    n += check(f'{L} S7.26 benefit tersimpan (label, meta, jumlah)',
               b0[0]['label'] == 'Prioritas kursi' and b0[0]['meta'] == 'gratis'
               and len(b0) == len([1 for _ in b0]) and len(b0) == len(db['content']['benefits'][bn]))
    n += check(f'{L} S7.27 ikon benefit berubah', b0[0]['icon'] == 'i-gem')
    n += check(f'{L} S7.28 semua opsi ikon ada di sprite',
               pg.evaluate("""() => { const have = new Set([...document.querySelectorAll('symbol')].map(s => s.id));
                     return [...document.querySelectorAll('#bByTier [data-k=icon] option')].every(o => have.has(o.value)); }"""))
    pg.evaluate("""() => document.querySelectorAll('#bByTier .panel[data-tier]')[0].querySelector('[data-rm]').click()""")
    pg.wait_for_timeout(250)
    pg.click('#cSave')
    pg.wait_for_timeout(350)
    n += check(f'{L} S7.29 hapus benefit tersimpan', len(db_of(pg)['content']['benefits'][bn]) == len(b0) - 1)
    pg.click('#cCopy')
    pg.wait_for_timeout(350)
    n += check(f'{L} S7.30 salin JSON memberi umpan balik', pg.is_visible('#toast'))

    # ── S8 · responsif & a11y ───────────────────────────────────────────
    pg.set_viewport_size({'width': 1280, 'height': 900})
    pg.wait_for_timeout(250)
    n += check(f'{L} S8.1 desktop: sidebar menempel, tombol menu tersembunyi',
               pg.evaluate("() => document.getElementById('side').getBoundingClientRect().width > 200")
               and not pg.is_visible('#drawerBtn'))
    pg.set_viewport_size({'width': 900, 'height': 800})
    pg.wait_for_timeout(300)
    n += check(f'{L} S8.2 tablet: tombol menu muncul', pg.is_visible('#drawerBtn'))
    n += check(f'{L} S8.2b kotak tombol seukuran tombol (tidak melebar menutupi baris)',
               pg.evaluate("""() => { const r = document.getElementById('drawerBtn').getBoundingClientRect();
                     return r.width < 200 && r.height < 70; }"""))
    pg.click('#drawerBtn')
    pg.wait_for_timeout(350)
    opened = pg.evaluate("() => document.body.classList.contains('nav-open')")
    try:
        pg.wait_for_function("() => document.getElementById('side').getBoundingClientRect().left >= 0", timeout=3000)
        landed = True
    except Exception:
        landed = False
    n += check(f'{L} S8.3 drawer terbuka: body.nav-open + aria-expanded + panel masuk layar',
               opened and pg.get_attribute('#drawerBtn', 'aria-expanded') == 'true' and landed)
    n += check(f'{L} S8.3b scrim ada dan menutupi layar',
               pg.evaluate("() => { const r = document.getElementById('scrim').getBoundingClientRect(); return r.width >= innerWidth - 1 && getComputedStyle(document.getElementById('scrim')).pointerEvents === 'auto'; }"))
    pg.mouse.click(700, 700)
    pg.wait_for_timeout(350)
    n += check(f'{L} S8.4 klik scrim menutup drawer', not pg.evaluate("() => document.body.classList.contains('nav-open')"))
    pg.click('#drawerBtn')
    pg.wait_for_timeout(300)
    pg.keyboard.press('Escape')
    pg.wait_for_timeout(300)
    n += check(f'{L} S8.5 Esc menutup drawer', not pg.evaluate("() => document.body.classList.contains('nav-open')"))
    pg.click('#drawerBtn')
    pg.wait_for_timeout(300)
    n += check(f'{L} S8.5b tombol menu tetap bisa dipakai saat drawer terbuka (toggle tertutup)',
               pg.evaluate("() => document.body.classList.contains('nav-open')"))
    pg.click('#drawerBtn')
    pg.wait_for_timeout(300)
    n += check(f'{L} S8.5c klik tombol lagi menutup drawer', not pg.evaluate("() => document.body.classList.contains('nav-open')"))
    pg.click('#drawerBtn')
    pg.wait_for_timeout(200)
    pg.click(".navlist a[data-route='report']")
    pg.wait_for_timeout(400)
    n += check(f'{L} S8.6 pilih rute dari drawer → pindah + drawer auto-tutup',
               pg.is_visible('#page-report') and not pg.evaluate("() => document.body.classList.contains('nav-open')"))
    pg.set_viewport_size({'width': 400, 'height': 860})
    pg.wait_for_timeout(350)
    n += check(f'{L} S8.7 400px: tabel bisa discroll, tidak luber',
               pg.evaluate("""() => { const t = document.querySelector('#page-report .tw');
                     return getComputedStyle(t).overflowX === 'auto' && t.getBoundingClientRect().right <= innerWidth + 1; }"""))
    n += check(f'{L} S8.8 400px: tanpa scroll horizontal dokumen',
               pg.evaluate("() => document.documentElement.scrollWidth <= window.innerWidth + 1"),
               pg.evaluate("() => document.documentElement.scrollWidth"))
    n += check(f'{L} S8.9 400px: konten tetap bisa dibaca (font tidak mengecil absurd)',
               pg.evaluate("() => parseFloat(getComputedStyle(document.querySelector('#rRows td')).fontSize) >= 11"))
    pg.set_viewport_size({'width': 1280, 'height': 900})
    pg.wait_for_timeout(300)
    a11y = pg.evaluate("""() => {
      const vis = el => el.offsetWidth > 0 && el.offsetHeight > 0 && !el.closest('[hidden]');
      const btn = [...document.querySelectorAll('#view-app button')].filter(b =>
        vis(b) && !(b.innerText || '').trim() && !b.getAttribute('aria-label') && !b.getAttribute('title'));
      const ctl = [...document.querySelectorAll('#view-app input, #view-app select, #view-app textarea')]
        .filter(el => vis(el) && !el.disabled
          && !(el.id && document.querySelector('label[for="' + el.id + '"]')) && !el.getAttribute('aria-label'));
      return { btn: btn.map(b => b.className).slice(0, 3), ctl: ctl.map(c => c.id || c.tagName).slice(0, 3) };
    }""")
    n += check(f'{L} S8.10 semua tombol punya nama aksesibel', not a11y['btn'], str(a11y['btn']))
    n += check(f'{L} S8.11 semua kontrol punya label', not a11y['ctl'], str(a11y['ctl']))
    pg.evaluate("() => document.querySelector('.skip').focus()")
    pg.wait_for_timeout(350)
    n += check(f'{L} S8.12 skip link ada dan muncul saat difokus',
               pg.evaluate("() => { const a = document.querySelector('.skip'); return !!a && a === document.activeElement; }")
               and pg.evaluate("() => parseFloat(getComputedStyle(document.querySelector('.skip')).top) > 0"))
    n += check(f'{L} S8.13 main bisa menerima fokus (target skip link)',
               pg.evaluate("() => document.getElementById('pages').tabIndex === -1"))
    n += check(f'{L} S8.14 toast = live region', pg.get_attribute('#toast', 'aria-live') == 'polite')
    n += check(f'{L} S8.15 nav pakai aria-current',
               pg.get_attribute(".navlist a[data-route='report']", 'aria-current') == 'page')
    go(pg, 'influencers')
    pg.click("#pRows tr:nth-child(1) [data-act=edit]")
    pg.wait_for_selector('#fName', timeout=2000)
    n += check(f'{L} S8.16 modal: role=dialog + aria-modal',
               pg.get_attribute('.mask [role=dialog]', 'aria-modal') == 'true')
    n += check(f'{L} S8.17 fokus dipindah ke dalam modal',
               pg.evaluate("() => document.querySelector('.mask').contains(document.activeElement)"))
    pg.keyboard.press('Escape')
    pg.wait_for_timeout(250)
    n += check(f'{L} S8.18 Esc menutup modal dan mengembalikan fokus',
               not pg.is_visible('#fName')
               and pg.evaluate("() => document.activeElement.classList.contains('ib')"))
    n += check(f'{L} S8.19 tabel: semua th punya scope=col',
               pg.evaluate("() => [...document.querySelectorAll('#page-influencers thead th')]").__len__() == 6
               and pg.evaluate("() => [...document.querySelectorAll('#page-influencers thead th')].every(t => t.getAttribute('scope') === 'col')"))
    n += check(f'{L} S8.20 gambar punya alt',
               pg.evaluate("() => [...document.images].every(i => i.hasAttribute('alt'))"))
    n += check(f'{L} S8.21 judul halaman bukan teks putih di atas latar terang',
               pg.evaluate("() => getComputedStyle(document.getElementById('pageTitle')).color !== 'rgb(255, 255, 255)'"))
    n += check(f'{L} S8.22 caption tabel tersembunyi secara visual tapi ada di DOM',
               pg.evaluate("() => { const c = document.querySelector('#page-influencers caption'); return c.getBoundingClientRect().height < 2 && c.textContent.includes('Daftar influencer'); }"))
    n += check(f'{L} S8.23 .sr-only berlaku di layar lebar juga (bukan cuma mobile)',
               pg.evaluate("() => getComputedStyle(document.querySelector('.sr-only')).clipPath !== 'none'"))

    # ── S9 · ketahanan data ─────────────────────────────────────────────
    pg.evaluate(f"() => localStorage.setItem('{DBKEY}', '{{rusak')")
    pg.reload()
    pg.wait_for_timeout(600)
    n += check(f'{L} S9.1 localStorage korup → sesi login tidak ikut hilang',
               pg.is_visible('#view-app') and not pg.is_visible('#loginForm'))
    if pg.is_visible('#loginForm'):
        login(pg)
    pg.wait_for_timeout(300)
    db = db_of(pg)
    n += check(f'{L} S9.1b DB di-seed ulang, tidak meledak',
               db is not None and db['v'] == 2 and len(db['people']) == 9)
    n += check(f'{L} S9.2 seed ulang lengkap (v2, 9 orang, ledger penuh)',
               db['v'] == 2 and len(db['people']) == 9 and len(db['nas']) > 100)
    n += check(f'{L} S9.3 Joshua kembali ke 100 NAS setelah reset', nas_of(db, 'Joshua') == 100, str(nas_of(db, 'Joshua')))
    pg.evaluate("""() => { const d = JSON.parse(localStorage.getItem('pn.admin.db.v2'));
          d.nas.push({ id: 'x-1', personId: 'tidak-ada', activity: 'event', amount: 5,
            date: '2026-09-01', status: 'verified', note: '<img src=x onerror=alert(1)>' });
          d.people[0].name = '<b>Html</b>';
          localStorage.setItem('pn.admin.db.v2', JSON.stringify(d)); }""")
    pg.reload()
    pg.wait_for_timeout(600)
    if pg.is_visible('#loginForm'):
        login(pg)
    go(pg, 'report')
    n += check(f'{L} S9.4 entry yatim (orang terhapus) tampil tanpa crash', '(terhapus)' in pg.inner_text('#rRows'))
    n += check(f'{L} S9.5 HTML di data di-escape, tidak dieksekusi',
               pg.evaluate("() => !document.querySelector('#rRows img[src=x]')"))
    go(pg, 'influencers')
    n += check(f'{L} S9.6 nama berisi markup jadi teks biasa',
               '<b>Html</b>' in pg.inner_text('#pRows')
               and not pg.evaluate("() => [...document.querySelectorAll('#pRows b')].some(e => e.textContent === 'Html')"))
    go(pg, 'create')
    n += check(f'{L} S9.7 orang rusak tidak membuat form create mati', pg.is_visible('#nPerson'))
    go(pg, 'leaderboard')
    n += check(f'{L} S9.8 leaderboard tetap terurut dengan data aneh',
               pg.evaluate("""() => { const v = [...document.querySelectorAll('#lbRows .val')]
                     .map(x => parseInt(x.innerText.replace(/\\D/g, ''), 10));
                     return v.every((x, i) => i === 0 || v[i - 1] >= x); }"""))
    n += check(f'{L} S9.9 nol error konsol sepanjang suite', not errs, str(errs[:2]))
    txt = pg.evaluate("() => document.getElementById('view-app').innerText")
    m = re.search(r'[^\n]{0,36}(NaN|undefined|\[object )[^\n]{0,36}', txt)
    n += check(f'{L} S9.10 nol teks cacat di app', m is None, m and m.group(0))
    return len(RESULTS)


# ══════════════════════════════════════════════════════════════════════════
def main():
    srv = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', HTTP_URL],
                         capture_output=True, text=True).stdout.strip()
    base = HTTP_URL if srv == '200' else FILE_URL
    L = 'HTTP' if srv == '200' else 'FILE'
    if srv != '200':
        print('   (server :8001 tidak aktif → suite jalan dari file://)')
    print(f'\n══ QA dashboard admin · {base}')
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        ctx = br.new_context(viewport={'width': 1280, 'height': 900}, accept_downloads=True)
        pg = ctx.new_page()
        errs, reqs = [], []
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('request', lambda r: reqs.append(r.url))
        pg.goto(base)
        pg.wait_for_timeout(500)

        n = 0
        n += check(f'{L} S0.1 login tampil, app tersembunyi', pg.is_visible('#loginForm') and not pg.is_visible('#view-app'))
        n += check(f'{L} S0.2 judul dokumen menyebut Admin', 'Admin' in pg.title(), pg.title())
        n += check(f'{L} S0.3 logo termuat (data URI, bukan berkas)',
               pg.evaluate("() => { const i = document.querySelector('#loginForm .brand-logo'); return !!i && i.naturalWidth > 100; }"))
        n += check(f'{L} S0.4 ilustrasi login = data URI',
                   pg.evaluate("() => getComputedStyle(document.querySelector('.art')).backgroundImage.includes('data:image')"))
        ext = [u for u in reqs if not u.startswith(('http://localhost:8001', 'data:', 'file:', 'blob:'))]
        n += check(f'{L} S0.5 nol request eksternal', not ext, str(ext[:2]))
        n += check(f'{L} S0.6 nol error konsol saat boot', not errs, str(errs[:2]))
        n += check(f'{L} S0.7 6 menu rute dengan data-route yang sah',
                   len(alls(pg, '.navlist a[data-route]')) == 6 and all(a.get_attribute('data-route') in ('overview', 'influencers', 'report', 'leaderboard', 'create', 'content') for a in alls(pg, '.navlist a[data-route]')))
        n += check(f'{L} S0.8 seed dipersistenkan saat boot (id stabil)', db_of(pg) is not None)
        orphan = pg.evaluate("""() => {
          const have = new Set([...document.querySelectorAll('symbol')].map(s => s.id));
          const bad = [];
          [...document.querySelectorAll('use')].forEach(u => { const id = (u.getAttribute('href') || '').slice(1);
            if (id && !have.has(id)) bad.push('markup:' + id); });
          const d = JSON.parse(localStorage.getItem('pn.admin.db.v2') || '{}');
          const dataIcons = [...(d.activities || []).map(a => a.icon),
            ...(((d.content || {}).about || {}).steps || []).map(s => s.icon),
            ...Object.values(((d.content || {}).benefits) || {}).flat().map(b => b.icon)];
          dataIcons.forEach(i => { if (i && !have.has(i)) bad.push('data:' + i); });
          return [...new Set(bad)]; }""")
        n += check(f'{L} S0.9 setiap ikon yang dipakai data punya <symbol>', not orphan, str(orphan[:3]))
        db = db_of(pg)
        n += check(f'{L} S0.10 bentuk basis data (9 orang · 4 aktivitas · 7 FAQ · 4 status)',
                   len(db['people']) == 9 and len(db['activities']) == 4 and len(db['tiers']) == 3
                   and len(db['content']['faq']) == 7 and len(db['statuses']) == 4)
        n += check(f'{L} S0.11 3 entry menunggu verifikasi di seed',
                   len([r for r in db['nas'] if r['status'] == 'pending']) == 3)

        # guard sebelum login
        pgg = ctx.new_page()
        pgg.goto(base)
        pgg.wait_for_timeout(300)
        pgg.evaluate("() => { location.hash = '#/report'; }")
        pgg.wait_for_timeout(300)
        n += check(f'{L} S1.1 guest tidak bisa membuka #/report', pgg.is_visible('#loginForm') and not pgg.is_visible('#view-app'))
        pgg.fill('#user', 'admin')
        pgg.fill('#pass', 'salah123')
        pgg.click('#loginForm button[type=submit]')
        pgg.wait_for_timeout(250)
        n += check(f'{L} S1.2 password salah → pesan error, tetap di login',
                   pgg.is_visible('#loginErr') and not pgg.is_visible('#view-app') and 'salah' in cell(pgg, '#loginErr'))
        pgg.fill('#user', '')
        pgg.fill('#pass', 'pacificnova')
        pgg.click('#loginForm button[type=submit]')
        pgg.wait_for_timeout(250)
        n += check(f'{L} S1.3 field kosong → pesan khusus, tidak masuk app', 'Isi username dan password' in cell(pgg, '#loginErr') and not pgg.is_visible('#view-app'))
        n += check(f'{L} S1.4 error = live region (aria-live + role)', pgg.get_attribute('#loginErr', 'aria-live') == 'polite' and pgg.get_attribute('#loginErr', 'role') == 'alert')
        pgg.fill('#user', 'admin')
        pgg.click('#loginForm button[type=submit]')
        pgg.wait_for_timeout(400)
        n += check(f'{L} S1.5 login benar → langsung ke rute yang dituju (deep link)',
                   pgg.is_visible('#view-app') and pgg.evaluate("() => location.hash") == '#/report'
                   and pgg.is_visible('#page-report'))
        n += check(f'{L} S1.6 sesi disimpan (remember me default aktif)',
                   bool(pgg.evaluate(f"() => localStorage.getItem('{AUTHKEY}')")))
        n += check(f'{L} S1.7 nama user tampil di footer sidebar', cell(pgg, '#whoName').lower() == 'admin')
        n += check(f'{L} S1.8 ticker login menampilkan 3 entry terbaru', len(pgg.query_selector_all('#loginTicker .tk')) == 3)
        pgg.click('#logoutBtn')
        pgg.wait_for_timeout(350)
        n += check(f'{L} S1.9 logout → login lagi + sesi hilang',
                   pgg.is_visible('#loginForm') and not pgg.evaluate(f"() => localStorage.getItem('{AUTHKEY}')"))
        # remember me dimatikan → sessionStorage
        pgg.evaluate("() => { document.getElementById('remember').checked = false; }")
        pgg.fill('#user', 'admin')
        pgg.fill('#pass', 'pacificnova')
        pgg.click('#loginForm button[type=submit]')
        pgg.wait_for_timeout(350)
        n += check(f'{L} S1.10 tanpa remember me → sesi di sessionStorage saja',
                   not pgg.evaluate(f"() => localStorage.getItem('{AUTHKEY}')")
                   and bool(pgg.evaluate(f"() => sessionStorage.getItem('{AUTHKEY}')")))
        pgg.close()

        login(pg)
        pg.wait_for_timeout(300)
        try:
            run_suite(pg, ctx, base, L, errs, reqs)
        except Exception as e:                                      # [QA-04] satu selector mati tidak boleh menyembunyikan 100 pemeriksaan lain
            check(f'{L} S-FATAL suite berhenti karena exception', False, repr(e)[:160])

        # ── S10 · file:// (berkas yang di-download user) ────────────────
        if L == 'HTTP':
            c2 = br.new_context(viewport={'width': 1280, 'height': 900})
            f = c2.new_page()
            ferrs = []
            f.on('console', lambda m: ferrs.append(m.text) if m.type == 'error' else None)
            f.on('pageerror', lambda e: ferrs.append(str(e)))
            fre = []
            f.on('request', lambda r: fre.append(r.url))
            f.goto(FILE_URL)
            f.wait_for_timeout(600)
            check('FILE S10.1 login tampil tanpa server', f.is_visible('#loginForm'))
            login(f)
            f.wait_for_timeout(300)
            check('FILE S10.2 data seed terbaca dari file://', len(alls(f, '#ovKpi .kpi')) == 4)
            go(f, 'influencers')
            check('FILE S10.3 tabel terisi (9 orang)', len(alls(f, '#pRows tr')) == 9)
            jrow = f.evaluate("""() => [...document.querySelectorAll('#pRows tr')]
                  .find(t => t.innerText.includes('Joshua')).innerText""")
            check('FILE S10.4 kontrak Joshua 100 NAS utuh', '100' in jrow and '0983' in jrow, jrow.replace('\n', ' | ')[:110])
            go(f, 'report')
            check('FILE S10.5 report terisi', len(alls(f, '#rRows tr')) > 100)
            check('FILE S10.6 nol request eksternal dari file://',
                  all(u.startswith(('file:', 'data:', 'blob:')) for u in fre), str(fre[:2]))
            check('FILE S10.7 nol error konsol dari file://', not ferrs, str(ferrs[:2]))
            f.close()
            c2.close()

        ctx.close()
        br.close()

    total, fails = len(RESULTS), len(FAILED)
    # [QA-05] ringkasan per blok, dihitung dari hasil run (bukan dari jumlah baris
    # sumber) supaya dokumen tidak bisa basi saat ada pemeriksaan yang ditambah.
    import collections
    grp = collections.Counter()
    for nm in RESULTS:
        m = re.search(r'(S\d+)', nm)
        grp[m.group(1) if m else 'lain'] += 1
    nama = {'S0': 'boot & file mandiri', 'S1': 'login, guard, sesi', 'S2': 'overview',
            'S3': 'data influencer', 'S4': 'NAS report', 'S5': 'create NAS + re-verification',
            'S6': 'leaderboard', 'S7': 'manage content', 'S8': 'responsif & a11y',
            'S9': 'ketahanan data', 'S10': 'dibuka dari file://'}
    print('Per blok:')
    for k in sorted(grp, key=lambda s: int(re.sub(r'\D', '', s) or 0)):
        print(f'  {k:4s} {grp[k]:3d}  {nama.get(k, "")}')
    print(f'\nHASIL QA DASHBOARD: {total - fails}/{total} LULUS')
    if fails:
        print('\nGAGAL:')
        for x in FAILED:
            print(' ·', x)
        sys.exit(1)
    print('Lolos semua: login & guard, CRUD influencer, ledger + verifikasi, create NAS dua\n'
          'langkah (review dulu, "Lanjutkan prosesnya" kemudian), leaderboard, manage content\n'
          '(FAQ · About · Contact · benefit per tier), persistensi, responsif, a11y, file mandiri.')


if __name__ == '__main__':
    main()
