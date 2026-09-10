#!/usr/bin/env python3
"""
QA FUNCTIONAL SUITE — Pacific Nova SPA

Dijalankan terhadap HASIL BUILD (index.html) lewat file:// — yaitu kondisi
sesungguhnya saat user mendownload satu file itu lalu membuka dengan klik ganda.

    python3 qa_spec.py          # semua bagian
    python3 qa_spec.py --headed # lihat browsernya bekerja

Butuh: pip install playwright && playwright install chromium
"""
import sys
import re
import datetime
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent
FILE = (ROOT / 'index.html').as_uri()

# 759/760/761 dan 939/940/941 = persis di kedua sisi breakpoint:
# tempat layout paling sering patah dan tidak kelihatan kalau hanya dites di 1440.
VIEWPORTS = [(360, 740), (390, 844), (479, 900), (480, 900), (759, 900), (760, 900),
             (761, 900), (900, 700), (939, 900), (940, 900), (941, 900), (1280, 800),
             (1440, 900), (1920, 1080), (2560, 1300)]

results = []


def check(section, name, cond, detail=''):
    results.append((section, name, bool(cond), detail))
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"\n         → {detail}" if detail and not cond else ''))


def new_page(br, **kw):
    ctx = br.new_context(viewport=kw.pop('viewport', {'width': 1440, 'height': 900}),
                         device_scale_factor=2, **kw)
    pg = ctx.new_page()
    pg.state = {'errors': [], 'warnings': [], 'external': []}
    pg.on('pageerror', lambda e: pg.state['errors'].append(str(e)))
    pg.on('console', lambda m: pg.state['warnings'].append(m.text) if m.type in ('error', 'warning') else None)
    pg.on('request', lambda r: pg.state['external'].append(r.url) if not r.url.startswith(str(FILE)) else None)
    pg.js = lambda expr: pg.evaluate(expr)
    return pg


# ══ S0 ═════════════════════════════════════════════════════════════════════
def s0_single_file(br):
    print('\n[S0] ★ SATU FILE, MANDIRI  (kontrak download)')
    pg = new_page(br)
    pg.goto(FILE)
    pg.wait_for_timeout(700)
    check('S0', '0 request keluar file — tidak ada aset/path relatif yang bisa hilang',
          pg.state['external'] == [], pg.state['external'][:3])
    check('S0', '0 console error & 0 warning (self-check [JS-14] harus diam di produksi)',
          not pg.state['errors'] and not pg.state['warnings'],
          (pg.state['errors'] + pg.state['warnings'])[:3])
    check('S0', 'logo = data-URI dan benar-benar ter-load (naturalWidth 368)',
          pg.js("document.querySelector('.brand-logo').naturalWidth") == 368)
    check('S0', 'hero = data-URI (tidak mungkin ada <img> rusak di hero)',
          pg.js("getComputedStyle(document.querySelector('.hero')).backgroundImage").startswith('url("data:image'))
    check('S0', 'tidak ada token placeholder build yang tertinggal di output',
          '__HERO_BG__' not in pg.content() and '__LOGO_URI__' not in pg.content())
    check('S0', 'setiap src/href adalah data: atau # (nol path relatif)',
          pg.js("""[...document.querySelectorAll('[src],[href]')].every(e => {
             const s = e.getAttribute('src'), h = e.getAttribute('href');
             return (s === null || s.startsWith('data:')) && (h === null || h.startsWith('#'));
           })"""))
    # Pagar terhadap kejebolan yang BENAR-BENAR terjadi di proyek ini: komentar
    # HTML yang memuat "--" menutup komentar lebih awal, teks legendanya dirender
    # sebagai konten -> hero bergeser 532px ke bawah dan home jadi bisa di-scroll.
    geo = pg.js("() => {"
                "  const page = document.querySelector('.page');"
                "  const stray = [...document.body.childNodes].filter(n =>"
                "    n.nodeType === 3 && n.textContent.trim()).length;"
                "  return {pageTop: Math.round(page.getBoundingClientRect().top),"
                "          strayText: stray,"
                "          homeScrollable: document.documentElement.scrollHeight > innerHeight + 2};}")
    check('S0', 'tidak ada konten liar di atas .page (pageTop=0) dan home pas satu layar',
          geo['pageTop'] == 0 and geo['strayText'] == 0 and not geo['homeScrollable'], geo)
    ctx2 = br.new_context(viewport={'width': 1280, 'height': 800}, java_script_enabled=False)
    p2 = ctx2.new_page()
    p2.goto(FILE)
    p2.wait_for_timeout(400)
    check('S0', 'tanpa JavaScript sekalipun hero tetap tampil (konten tidak hilang, halaman tidak putih)',
          p2.is_visible('.view-home h1') and 'Collect moments' in p2.inner_text('.view-home h1'))
    ctx2.close()
    pg.close()


# ══ S1 ═════════════════════════════════════════════════════════════════════
def s1_router(br):
    print('\n[S1] ★ ROUTER [JS-03/JS-04]  · 4 view, title, state nav, anchor')
    pg = new_page(br)
    for h, view, title in [('#/', 'home', 'Pacific Nova — Collect Moments, Earn Nova'),
                           ('#/about', 'about', 'About Pacific Nova'),
                           ('#/faq', 'faq', 'FAQ — Pacific Nova'),
                           ('#/passport', 'passport', 'My Nova Passport — Pacific Nova')]:
        pg.goto(FILE + h)
        pg.wait_for_timeout(450)
        st = pg.js("""() => ({v: document.body.dataset.view,
            visible: [...document.querySelectorAll('.view')].filter(s => !s.hidden).map(s => s.id),
            t: document.title})""")
        check('S1', f'{h:11s} view={view:8s} · hanya 1 section tampil · document.title ikut',
              st['v'] == view and st['visible'] == ['view-' + view] and st['t'] == title, st)
    pg.goto(FILE + '#/about'); pg.wait_for_timeout(400)
    pg.evaluate("location.hash = '#/bukan-rute'"); pg.wait_for_timeout(300)
    check('S1', 'hash asing di tengah sesi tidak melempar user ke home (view bertahan)',
          pg.js("document.body.dataset.view") == 'about', pg.js("document.body.dataset.view"))
    pg.goto(FILE + '#/bukan-rute'); pg.reload(); pg.wait_for_timeout(500)
    check('S1', 'load langsung dengan rute tak dikenal → home (bukan halaman kosong)',
          pg.js("document.body.dataset.view") == 'home' and pg.is_visible('.view-home h1'))
    pg.goto(FILE + '#/about')
    pg.wait_for_timeout(400)
    ac = pg.js("[...document.querySelectorAll('.navlinks a')].map(a => a.getAttribute('aria-current'))")
    check('S1', 'aria-current hanya di link aktif (tidak ada nilai "false" nyasar)',
          ac == ['page', None], ac)
    pills = pg.js("() => ({contact: navContact.hidden, passport: navPassport.hidden, back: navBack.hidden})")
    check('S1', 'di About: Contact Us disembunyikan (sudah ada di halaman), Passport + Back tampil',
          pills == {'contact': True, 'passport': False, 'back': False}, pills)
    pg.goto(FILE)
    pg.wait_for_timeout(400)
    check('S1', 'di Home: pill Passport & Back disembunyikan (CTA hero sudah mewakili)',
          pg.js("navPassport.hidden") and pg.js("navBack.hidden") and not pg.js("navContact.hidden"))
    pg.goto(FILE + '#/about#contact')
    pg.reload()
    pg.wait_for_timeout(1200)
    a = pg.js("""() => {const c = document.getElementById('contact');
        return {top: Math.round(c.getBoundingClientRect().top),
                visible: c.getBoundingClientRect().top < innerHeight - 120,
                atMax: Math.round(scrollY) >=
                       Math.round(document.documentElement.scrollHeight - innerHeight) - 2};}""")
    # ★ clamp = perilaku sah. #contact blok terakhir sebelum band CTA, jadi sisa
    #   dokumen di bawahnya lebih pendek dari viewport dan browser tidak bisa
    #   memakainya di 92px. Yang dijamin: panel terlihat ATAU scroll maksimum.
    check('S1', 'deep-link #/about#contact → panel kontak terlihat (clamp di scroll maksimum diterima)',
          a['visible'] or a['atMax'], a)
    pg.close()


# ══ S2 ═════════════════════════════════════════════════════════════════════
def s2_passport(br):
    print('\n[S2] ★ MY NOVA PASSPORT  · search, 3 keadaan kartu, clock, deep link')
    pg = new_page(br)
    pg.goto(FILE + '#/passport')
    pg.wait_for_timeout(400)
    check('S2', 'keadaan awal: hanya hint — tidak ada kartu kosong, tidak ada pesan salah',
          pg.js("() => ({card: card.hidden, nf: notfound.hidden, note: note.hidden, hint: !hint.hidden})")
          == {'card': True, 'nf': True, 'note': True, 'hint': True})

    pg.fill('#memberInput', '')
    pg.keyboard.press('Enter')
    pg.wait_for_timeout(350)
    check('S2', 'submit kosong: pesan validasi + fokus kembali ke input + aria-invalid=true',
          pg.js("note.textContent") == 'Please enter your member number first.'
          and pg.js("document.activeElement.id") == 'memberInput'
          and pg.js("memberInput.getAttribute('aria-invalid')") == 'true')

    for q in ['0983', 'nv-2026-004821', ' NV 2026 004821 ']:
        pg.fill('#memberInput', q)
        pg.keyboard.press('Enter')
        pg.wait_for_timeout(1200)
        got = pg.js("""() => [mName, mTier, mTotal, document.querySelector('.chip')]
            .map(e => e.textContent.trim()).join('|')""")
        check('S2', f'lookup "{q.strip()}" → Joshua · Blue Nova · 100 · 7 activity',
              got == 'Joshua|Blue Nova|100|7 activity', got)

    check('S2', 'Total NAS = jumlah isi history (100) — bukan angka yang ditulis tangan',
          pg.js("""() => {
            const t = [...document.querySelectorAll('.amount')]
              .reduce((s, e) => s + parseInt(e.textContent.replace(/\\D/g, ''), 10), 0);
            return t === 100 && Number(mTotal.textContent) === t; }"""))
    dates = pg.js("[...document.querySelectorAll('.h-date')].map(e => e.textContent)")
    check('S2', f'7 baris history, tiap baris tanggal submit sendiri (unik {len(set(dates))}/7)',
          len(dates) == 7 and len(set(dates)) == 7, dates)
    check('S2', 'urutan history sama dengan urutan data (event +50 paling atas)',
          'NAS Event Attending' in pg.js("document.getElementById('history').firstElementChild.textContent"))
    check('S2', 'My Benefit: judul + 3 baris + meta per baris',
          pg.js("""() => document.querySelector('.b-head h3').textContent === 'My Benefit'
              && document.querySelectorAll('#benefitList li').length === 3
              && document.querySelectorAll('#benefitList .b-meta').length === 3"""))
    check('S2', 'avatar = inisial nama (dihitung, bukan hardcode)',
          pg.js("avatar.textContent") == 'J' and pg.js("mName.textContent") == 'Joshua')
    check('S2', 'tidak ada barcode & tidak ada cap bundar (permintaan R3)',
          pg.js("document.querySelectorAll('.barcode, .stamp, svg[viewBox*=stroke-dash]').length") == 0)

    stamp = pg.js("mUpdated.textContent")
    local_today = datetime.date.today().strftime('%d %b %Y')
    check('S2', f'[JS-08] tanggal stamp = ZONA LOKAL ({local_today}), bukan UTC (bug geser 1 hari)',
          stamp.startswith(local_today), stamp)
    hh, mm = int(pg.js("new Date().getHours()")), int(pg.js("new Date().getMinutes()"))
    m = re.search(r'(\d{2}):(\d{2}):(\d{2})', stamp)
    check('S2', 'jam stamp = jam lokal browser (menit boleh ±1 karena tick)',
          m is not None and abs(int(m.group(1)) - hh) == 0 and abs(int(m.group(2)) - mm) <= 1, stamp)
    t1 = pg.js("mUpdated.textContent")
    pg.wait_for_timeout(2300)
    t2 = pg.js("mUpdated.textContent")
    check('S2', 'clock benar-benar berdetak tiap detik', t1 != t2, f'{t1} → {t2}')
    pg.goto(FILE + '#/about')
    pg.wait_for_timeout(600)
    t3 = pg.js("mUpdated.textContent")
    pg.wait_for_timeout(1700)
    t4 = pg.js("mUpdated.textContent")
    check('S2', '★ clock DIHENTIKAN saat pindah view — tidak ada interval liar seumur tab',
          t3 == t4, f'{t3} → {t4}')
    pg.goto(FILE + '#/passport'); pg.wait_for_timeout(400)
    pg.fill('#memberInput', '0983'); pg.keyboard.press('Enter'); pg.wait_for_timeout(700)
    pg.fill('#memberInput', '0983'); pg.keyboard.press('Enter'); pg.wait_for_timeout(700)
    a = pg.js("mUpdated.textContent"); pg.wait_for_timeout(1200)
    b = pg.js("mUpdated.textContent")
    check('S2', 'search berkali-kali tidak menumpuk interval (jam tetap maju 1 langkah, bukan 2+)',
          int(b.split(':')[-1]) - int(a.split(':')[-1]) in (1, 0, -59), f'{a} → {b}')

    pg.goto(FILE + '#/passport?member=0983')
    pg.wait_for_timeout(1300)
    check('S2', 'deep link #/passport?member=0983 → kartu terisi tanpa satu klik pun',
          pg.js("mName.textContent") == 'Joshua' and not pg.js("card.hidden"))
    pg.evaluate("location.hash='#/passport?member=NV-2026-004821'")
    pg.wait_for_timeout(900)
    check('S2', 'perubahan ?member= setelah load ikut disinkronkan (tombol back/forward)',
          pg.js("mNo.textContent") == 'NV-2026-004821' and not pg.js("card.hidden"),
          pg.js("mNo.textContent"))
    pg.evaluate("location.hash='#/passport?member=TIDAKADA1'")
    pg.wait_for_timeout(500)
    check('S2', 'deep link ke member tak dikenal → keadaan not-found, bukan kartu kosong',
          not pg.js("notfound.hidden") and pg.js("card.hidden"))

    pg.goto(FILE + '#/passport')
    pg.wait_for_timeout(400)
    pg.fill('#memberInput', 'XXX999')
    pg.keyboard.press('Enter')
    pg.wait_for_timeout(400)
    check('S2', 'member tak dikenal → #notfound + #note, kartu disembunyikan',
          pg.js("notfound.hidden") is False and 'XXX999' in pg.js("note.textContent")
          and pg.js("card.hidden") is True)
    check('S2', 'nomor yang diketik tampil apa adanya (upper-case) di panel not-found',
          pg.js("nfQuery.textContent") == 'XXX999')
    pg.click('#clearBtn')
    pg.wait_for_timeout(300)
    check('S2', 'tombol × membersihkan input, mengembalikan hint, dan mengembalikan fokus',
          pg.js("memberInput.value") == '' and not pg.js("hint.hidden")
          and pg.js("document.activeElement.id") == 'memberInput')
    pg.fill('#memberInput', '0983')
    pg.keyboard.press('Enter')
    pg.wait_for_timeout(900)
    pg.keyboard.press('Escape')
    pg.wait_for_timeout(300)
    check('S2', 'Escape di input = reset penuh (kartu tidak tertinggal di bawah input kosong)',
          pg.js("card.hidden") and pg.js("memberInput.value") == '')

    n_img = pg.js("document.querySelectorAll('img').length")
    pg.fill('#memberInput', '<b>x</b><img src=1 onerror=window.__pwn=1>')
    pg.keyboard.press('Enter')
    pg.wait_for_timeout(700)
    check('S2', '★ payload markup di input tidak pernah jadi elemen (esc/textContent): <b>/<img> jadi teks',
          pg.js("typeof window.__pwn") == 'undefined'
          and pg.js("note.querySelector('b,img')") is None
          and pg.js("document.querySelectorAll('img').length") <= n_img,
          pg.js("note.textContent"))
    pg.fill('#memberInput', '<s')
    pg.keyboard.press('Enter')
    pg.wait_for_timeout(400)
    check('S2', 'input tanpa karakter alfanumerik ditangani tanpa exception → not-found',
          not pg.js("notfound.hidden") and not pg.state['errors'], pg.state['errors'][:2])
    pg.fill('#memberInput', '0983')
    pg.keyboard.press('Enter')
    pg.wait_for_timeout(700)
    check('S2', 'search ulang setelah error: keadaan bersih (note/notfound hilang, kartu tampil)',
          pg.js("note.hidden") and pg.js("notfound.hidden") and not pg.js("card.hidden"))
    pg.close()


# ══ S3 ═════════════════════════════════════════════════════════════════════
def s3_content(br):
    print('\n[S3] ◆ KONTEN  · About, FAQ, dan permintaan Round 5')
    pg = new_page(br)
    pg.goto(FILE + '#/about')
    pg.wait_for_timeout(500)
    check('S3', 'About: 4 statistik · 3 langkah · 3 tier · panel #contact · band CTA',
          pg.js("""() => [document.querySelectorAll('.stat').length,
             document.querySelectorAll('.grid3 .feature').length,
             document.querySelectorAll('.tier-card').length,
             !!document.getElementById('contact'),
             !!document.querySelector('.cta-band')].join(',')""") == '4,3,3,true,true')
    check('S3', 'badge "Most members" hanya 1 dan tidak menimpa chip "600+ NAS"',
          pg.js("""() => {
             const cards = [...document.querySelectorAll('.tier-card')];
             const n = cards.reduce((a, c) => a + c.querySelectorAll('.t-flag').length, 0);
             const g = cards.find(c => c.querySelector('.t-flag'));
             const f = g.querySelector('.t-flag').getBoundingClientRect();
             const r = g.querySelector('.t-req').getBoundingClientRect();
             const hit = !(f.right < r.left || f.left > r.right || f.bottom < r.top || f.top > r.bottom);
             return n === 1 && !hit; }"""))
    check('S3', 'tinggi ketiga kartu tier rata (grid sehat, bukan kartu menggantung)',
          pg.js("""() => {const h = [...document.querySelectorAll('.tier-card')]
              .map(c => Math.round(c.getBoundingClientRect().height));
             return Math.max(...h) - Math.min(...h) <= 1;}"""))
    check('S3', 'nav persis "About Pacific Nova" | "FAQ", tanpa entri Nova Passport',
          pg.js("[...document.querySelectorAll('.navlinks a')].map(a => a.textContent.trim()).join(' | ')")
          == 'About Pacific Nova | FAQ')
    check('S3', 'chip kicker "MEMBER NAS BALANCE" & eyebrow "PACIFIC NOVA · MEMBERSHIP" hilang dari DOM',
          pg.js("document.querySelectorAll('.kicker, .tag').length") == 0)
    check('S3', 'About tidak punya teks placeholder / lorem',
          not re.search(r'lorem|TODO|placeholder|xxxx', pg.inner_text('.view-about'), re.I))

    pg.goto(FILE + '#/faq')
    pg.wait_for_timeout(500)
    total = pg.js("document.querySelectorAll('#faqList details').length")
    check('S3', f'FAQ terender dari data: {total} pertanyaan, tiap baris ber-tag kategori',
          total == 10 and pg.js("document.querySelectorAll('#faqList .q-tag').length") == 10)
    pg.click('.chips button[data-cat="tier"]')
    pg.wait_for_timeout(300)
    check('S3', 'chip kategori menyaring + aria-pressed pindah ke chip aktif',
          pg.js("document.querySelectorAll('#faqList details').length") == 2
          and pg.js("document.querySelector('.chips button[data-cat=\"tier\"]').getAttribute('aria-pressed')") == 'true'
          and pg.js("document.querySelector('.chips button[data-cat=\"all\"]').getAttribute('aria-pressed')") == 'false')
    pg.fill('#faqFilter', 'expire')
    pg.wait_for_timeout(300)
    check('S3', 'filter + search bekerja bersamaan (tier + "expire" → 0 hasil + empty-state)',
          pg.js("document.querySelectorAll('#faqList details').length") == 0
          and pg.js("faqEmpty.hidden") is False)
    pg.click('.chips button[data-cat="all"]')
    pg.wait_for_timeout(300)
    check('S3', 'search tetap hidup setelah chip kembali ke All',
          pg.js("document.querySelectorAll('#faqList details').length") == 1)
    pg.fill('#faqFilter', '')
    pg.wait_for_timeout(300)
    check('S3', 'search dikosongkan → 10 item kembali, empty-state hilang',
          pg.js("document.querySelectorAll('#faqList details').length") == 10
          and pg.js("faqEmpty.hidden") is True)
    pg.click('#faqList details summary')
    pg.wait_for_timeout(250)
    check('S3', 'baris FAQ bisa dibuka (accordion native <details>)',
          pg.js("document.querySelector('#faqList details').open") is True)
    check('S3', 'isi FAQ lolos esc(): tidak ada tag bocor, semua jawaban panjang',
          pg.js("""[...document.querySelectorAll('.qa-body')].every(d =>
              d.textContent.length > 40 && !d.querySelector('script,img'))"""))
    pg.close()


# ══ S4 ═════════════════════════════════════════════════════════════════════
def s4_responsive(br):
    print('\n[S4] ◆ LAYOUT & BREAKPOINT  · 760px (nav/burger) dan 940px (kartu)')
    pg = new_page(br)
    for w, h in VIEWPORTS:
        pg.set_viewport_size({'width': w, 'height': h})
        pg.goto(FILE)
        pg.wait_for_timeout(320)
        m = pg.js("""() => ({ov: document.documentElement.scrollWidth > innerWidth,
            burger: getComputedStyle(burger).display !== 'none',
            navlinks: getComputedStyle(document.querySelector('.navlinks')).display !== 'none'})""")
        want = w <= 760
        check('S4', f'{w:>4}×{h:<4} tanpa overflow · burger {"ON " if want else "OFF"} · nav desktop {"OFF" if want else "ON "}',
              not m['ov'] and m['burger'] == want and m['navlinks'] != want, m)
    for w, h in [(360, 740), (390, 844), (768, 1024), (940, 900), (1440, 900), (2560, 1300)]:
        pg.set_viewport_size({'width': w, 'height': h})
        for view in ['#/about', '#/faq', '#/passport']:
            pg.goto(FILE + view)
            pg.wait_for_timeout(320)
            check('S4', f'{w:>4}×{h:<4} {view:11s} render penuh, tanpa overflow horizontal',
                  not pg.js("document.documentElement.scrollWidth > innerWidth"))
    pg.goto(FILE + '#/passport')
    pg.fill('#memberInput', '0983')
    pg.keyboard.press('Enter')
    pg.wait_for_timeout(1400)
    for w, h in [(939, 900), (390, 844)]:
        pg.set_viewport_size({'width': w, 'height': h})
        pg.wait_for_timeout(400)
        cols = pg.js("getComputedStyle(card).gridTemplateColumns.split(' ').length")
        check('S4', f'kartu passport di {w}px: {cols} kolom (≤940px wajib 1 kolom)', cols == 1)
    pg.set_viewport_size({'width': 1440, 'height': 900})
    pg.wait_for_timeout(400)
    check('S4', 'kartu passport di desktop: 2 kolom (navy member + activity)',
          pg.js("getComputedStyle(card).gridTemplateColumns.split(' ').length") == 2)
    pg.goto(FILE)
    pg.set_viewport_size({'width': 390, 'height': 844})
    pg.wait_for_timeout(450)
    g = pg.js("""() => {const r = document.querySelector('.content').getBoundingClientRect();
        return {top: Math.round(r.top), bottom: Math.round(innerHeight - r.bottom)};}""")
    check('S4', 'hero mobile: blok copy dikunci di tengah (gap atas ≈ bawah, selisih ≤35px)',
          abs(g['top'] - g['bottom']) <= 35, g)
    pg.set_viewport_size({'width': 1440, 'height': 900})
    pg.wait_for_timeout(450)
    g = pg.js("""() => {const r = document.querySelector('.content').getBoundingClientRect();
        return {top: Math.round(r.top), bottom: Math.round(innerHeight - r.bottom)};}""")
    check('S4', 'hero desktop 1440: sama-sama terpusat (selisih ≤70px)',
          abs(g['top'] - g['bottom']) <= 70, g)
    pg.set_viewport_size({'width': 2560, 'height': 1300})
    pg.wait_for_timeout(450)
    check('S4', 'ultrawide 2560: lebar blok teks dibatasi (judul tidak memanjang jadi 1 baris)',
          pg.js("Math.round(document.querySelector('.content').getBoundingClientRect().width)") <= 800)
    pg.set_viewport_size({'width': 1440, 'height': 640})
    pg.wait_for_timeout(450)
    check('S4', 'layar pendek 640px: H1 mengecil, hero tetap muat tanpa scroll',
          pg.js("document.querySelector('.content').getBoundingClientRect().bottom") <= 640
          and not pg.js("document.body.scrollHeight > innerHeight + 2"))
    pg.close()


# ══ S5 ═════════════════════════════════════════════════════════════════════
def s5_mobile_nav(br):
    print('\n[S5] ◆ HAMBURGER [JS-05]  · layar kecil')
    pg = new_page(br, viewport={'width': 390, 'height': 844})
    pg.goto(FILE)
    pg.wait_for_timeout(400)
    check('S5', 'saat load: sheet benar-benar display:none (bukan transparan yang menahan klik)',
          pg.js("getComputedStyle(sheet).display") == 'none'
          and pg.js("burger.getAttribute('aria-expanded')") == 'false')
    pg.click('#burger')
    pg.wait_for_timeout(300)
    check('S5', 'buka: aria-expanded=true, label → "Close menu", sheet flex, fokus pindah ke item pertama',
          pg.js("burger.getAttribute('aria-expanded')") == 'true'
          and pg.js("burger.getAttribute('aria-label')") == 'Close menu'
          and pg.js("getComputedStyle(sheet).display") == 'flex'
          and pg.js("!!document.activeElement.closest('#sheet')"), )
    n = pg.js("document.querySelectorAll('#sheet a').length")
    check('S5', f'menu memuat {n} tujuan (About · FAQ · Contact · Passport)', n == 4)
    pg.keyboard.press('Escape')
    pg.wait_for_timeout(250)
    check('S5', 'Esc menutup menu', pg.js("sheet.classList.contains('is-open')") is False)
    pg.click('#burger')
    pg.wait_for_timeout(200)
    pg.mouse.click(195, 700)
    pg.wait_for_timeout(250)
    check('S5', 'klik di luar menutup menu', pg.js("sheet.classList.contains('is-open')") is False)
    pg.click('#burger')
    pg.wait_for_timeout(200)
    pg.click("#sheet a[data-route='about']")
    pg.wait_for_timeout(600)
    check('S5', 'pilih About: view berpindah DAN sheet menutup otomatis',
          pg.js("document.body.dataset.view") == 'about'
          and pg.js("sheet.classList.contains('is-open')") is False)
    pg.click('#burger')
    pg.wait_for_timeout(200)
    pg.click("#sheet a[href='#/about#contact']")
    pg.wait_for_timeout(900)
    check('S5', 'Contact di sheet = pindah view lalu scroll ke panel kontak',
          pg.js("document.body.dataset.view") == 'about'
          and 60 < pg.js("document.getElementById('contact').getBoundingClientRect().top") < 200)
    pg.click('#burger')
    pg.wait_for_timeout(200)
    pg.set_viewport_size({'width': 1200, 'height': 844})
    pg.wait_for_timeout(400)
    check('S5', 'melebarkan jendela (≤760 → 1200) menutup sheet: tidak ada menu mobile menggantung',
          pg.js("sheet.classList.contains('is-open')") is False)
    check('S5', 'di 1200px tombol hamburger ikut hilang (nav desktop kembali utuh)',
          pg.js("getComputedStyle(burger).display") == 'none')
    pg.close()


# ══ S6 ═════════════════════════════════════════════════════════════════════
def s6_a11y_motion(br):
    print('\n[S6] ◆ AKSESIBILITAS & MOTION')
    pg = new_page(br)
    pg.goto(FILE)
    pg.wait_for_timeout(400)
    check('S6', 'landmark punya nama: <nav aria-label="Main">, sheet role=group',
          pg.js("document.querySelector('nav').getAttribute('aria-label')") == 'Main'
          and pg.js("sheet.getAttribute('role')") == 'group'
          and pg.js("sheet.getAttribute('aria-label')") == 'Site menu')
    check('S6', 'semua <button>/<input> punya nama aksesibel',
          pg.js("""[...document.querySelectorAll('button,input')].every(e => {
             const t = ((e.getAttribute('aria-label') || '') + (e.textContent || '')).trim();
             const lab = e.id ? document.querySelector('label[for="' + e.id + '"]') : null;
             const wrap = e.closest('label');
             return !!t || !!lab || !!wrap; })"""))
    imgs_ok = pg.js("[...document.images].every(i => i.hasAttribute('alt'))")
    svg_ok = pg.js("[...document.querySelectorAll('svg')].every(s =>"
                   " s.getAttribute('aria-hidden') === 'true' ||"
                   " s.closest('[aria-hidden]') !== null)")
    check('S6', 'semua <img> punya alt; seluruh svg dekoratif aria-hidden', imgs_ok and svg_ok,
          (imgs_ok, svg_ok))
    check('S6', 'pesan validasi = live region (role=status, aria-live=polite)',
          pg.js("note.getAttribute('role')") == 'status' and pg.js("note.getAttribute('aria-live')") == 'polite')
    check('S6', 'area hasil kartu = aria-live=polite (hasil search diumumkan)',
          pg.js("document.querySelector('.result').getAttribute('aria-live')") == 'polite')
    check('S6', 'input search terhubung ke pesannya lewat aria-describedby',
          pg.js("memberInput.getAttribute('aria-describedby')") == 'note')
    check('S6', 'tidak ada role redundant tertinggal di dalam <nav>',
          pg.js("document.querySelectorAll('.navlinks[role=\"navigation\"]').length") == 0)
    check('S6', 'bahasa dokumen dideklarasikan (pembaca layar tidak salah pelafalan)',
          pg.js("document.documentElement.lang") == 'en')
    check('S6', 'tepat satu <h1> per view (struktur heading tidak bercabang)',
          pg.js("document.querySelectorAll('.view:not([hidden]) h1').length") == 1
          and all(pg.evaluate(f"document.getElementById('view-{v}').querySelectorAll('h1').length") == 1
                  for v in ('home', 'about', 'faq', 'passport')))
    check('S6', 'About: tiap bagian punya <h2> (outline dokumen berguna untuk screen reader)',
          pg.evaluate("document.getElementById('view-about').querySelectorAll('h2').length") >= 3)
    check('S6', 'FAQ: tiap baris accordion punya <summary> sebagai label (pengganti h2 di list)',
          pg.evaluate("document.querySelectorAll('#faqList details > summary').length") == 10
          and pg.evaluate("document.querySelectorAll('#faqList details > summary .q-text').length") == 10)
    pg.goto(FILE + '#/passport')
    pg.wait_for_timeout(400)
    seq = []
    for _ in range(6):
        pg.keyboard.press('Tab')
        pg.wait_for_timeout(50)
        seq.append(pg.js("() => {const a = document.activeElement; return a.id || a.className || a.tagName;}"))
    check('S6', f'urutan Tab wajar: brand → nav → aksi → form, tanpa jebakan fokus [{" → ".join(seq)}]',
          'brand' in str(seq[0]) and 'memberInput' in seq and seq.index('memberInput') <= 5, seq)
    # :focus-visible hanya aktif untuk fokus via KEYBOARD, jadi tesnya pakai Tab,
    # bukan .focus() dari script (yang justru akan selalu "lolos" tanpa arti).
    pg.set_viewport_size({'width': 390, 'height': 844})
    pg.goto(FILE)
    pg.wait_for_timeout(300)
    rings = {}
    for _ in range(4):
        pg.keyboard.press('Tab')
        pg.wait_for_timeout(40)
        ident = pg.js("() => {const a = document.activeElement;"
                      "return a.id || a.className || a.tagName;}")
        st = pg.js("() => {const s = getComputedStyle(document.activeElement);"
                   "return s.outlineStyle + '|' + s.outlineWidth;}")
        rings[ident] = st
    keyboard_ring = all(v.split('|')[0] != 'none' and v.split('|')[1] != '0px'
                        for v in rings.values())
    check('S6', f'semua target Tab pertama punya ring fokus keyboard terlihat {sorted(rings)}',
          keyboard_ring and len(rings) >= 3, rings)
    pg.evaluate("memberInput.focus()")
    check('S6', 'kontras teks navy-kartu ≥ 4.5:1 terhadap latar navy',
          pg.js("""() => {
            const lum = (c) => { const [r,g,b] = c.map(v => { v /= 255; return v <= .03928 ? v/12.92 : ((v+.055)/1.055)**2.4; });
              return .2126*r + .7152*g + .0722*b; };
            const f = getComputedStyle(document.querySelector('.tier')).color.match(/\\d+/g).map(Number);
            const L1 = lum(f), L2 = lum([22,43,82]);
            return (Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05) >= 4.5; }"""))
    pg.close()

    ctx = br.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
    pg = ctx.new_page()
    pg.goto(FILE + '#/passport')
    pg.wait_for_timeout(300)
    pg.fill('#memberInput', '0983')
    pg.click('.go')
    pg.wait_for_timeout(250)
    check('S6', 'prefers-reduced-motion: Total NAS langsung 100 (tanpa animasi hitung)',
          pg.evaluate("mTotal.textContent") == '100')
    check('S6', 'prefers-reduced-motion: animasi kartu mati & scroll-behavior jadi auto',
          pg.evaluate("getComputedStyle(card).animationName") == 'none'
          and pg.evaluate("getComputedStyle(document.documentElement).scrollBehavior") == 'auto')
    ctx.close()


# ═══════════════════════════════════════════════════════════════════════════
def main():
    with sync_playwright() as p:
        br = p.chromium.launch(args=['--no-sandbox'], headless='--headed' not in sys.argv)
        for fn in (s0_single_file, s1_router, s2_passport, s3_content,
                   s4_responsive, s5_mobile_nav, s6_a11y_motion):
            fn(br)
        br.close()
    failed = [r for r in results if not r[2]]
    print('\n' + '═' * 70)
    print(f'HASIL QA: {len(results) - len(failed)}/{len(results)} LULUS')
    if failed:
        print('\nYANG GAGAL:')
        for s, n, _, d in failed:
            print(f'  [{s}] {n}  →  {d}')
        sys.exit(1)
    print('Semua kontrak aman: satu file mandiri, router, passport (data +')
    print('keadaan + clock), konten About/FAQ, 15 breakpoint, menu mobile,')
    print('aksesibilitas, dan reduced-motion.')


if __name__ == '__main__':
    main()
