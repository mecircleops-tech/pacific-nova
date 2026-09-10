# QA Struktur File — Pacific Nova

Tanggal: 10 Sep 2026 · Pelaksana: QA (audit struktur, bukan penulis kode)
Cakupan: seluruh tree `pacific-nova-spa/` (28 berkas, ±12 MB) + struktur root repo.
Metode: semua cek yang bisa jalan tanpa browser dijalankan langsung
(`qa_audit.py`, reproduksi `build.py`, regenerasi `qa_map.py`, pemindaian byte/teks).
Suite browser `qa_spec.py` / `qa_dash.py` **tidak** dijalankan ulang —
`playwright` tidak terinstal di lingkungan ini — jadi klaim 122/122 & 200/200
diverifikasi dari log yang tersimpan, bukan dari eksekusi.

## Ringkasan eksekutif

| Area | Hasil |
|---|---|
| `index.html` ↔ `src/index.src.html` | **SELARAS** — build ulang byte-identik (`cmp` lolos, 0 beda) |
| `dashboard.html` ↔ `src/dashboard.src.html` | **TIDAK SELARAS (P0)** — artefak committed basi, gagal `qa_audit` |
| Kontrak satu-file (0 referensi luar, 0 token sisa) | **LOLOS** di kedua output |
| `CODEMAP.md` ↔ source | **SEGAR** — regenerasi hanya mengubah tanggal |
| Aset `assets/` | Terpakai semua (termasuk `qa-attach.png` oleh `qa_dash.py`) |
| `shots/` (10 PNG, 8,3 MB) | Valid, tapi **tanpa satu pun rujukan/dokumentasi (P1)** |
| Higiene berkas (LF, UTF-8, newline akhir) | **BERSIH** |
| `.gitignore` / README root | **TIDAK ADA (P1)** |
| Secrets / kredensial | Nihil, selain kredensial demo yang memang didokumentasikan |
| `QA-RUN.txt` (landing) | 122 baris `PASS` terhitung — klaim 122/122 **terverifikasi** |
| `QA-DASH-RUN.txt` (dashboard) | Hanya ringkasan 20 baris — klaim 200/200 **tak bisa diaudit dari log (P1)** |

## P0 — harus diputuskan sebelum kirim

### P0-1 · `dashboard.html` yang committed bukan hasil build dari `src/` saat ini

Bukti (semuanya dapat direproduksi, lihat bab “Reproduksi”):

| Sinyal | Build fresh dari `src/` | `dashboard.html` committed |
|---|---|---|
| Ukuran | 386.144 B (**377 KB** — cocok dengan klaim README & QA-REPORT) | 427.763 B (**418 KB**) |
| Baris | 2060 (= `src/dashboard.src.html`) | 2700 (+640 baris) |
| `qa_audit.py` | **LOLOS**, exit 0 | **1 TEMUAN** `A2 .c`, exit 1 |
| Bahasa komentar/marker | Indonesia (`★KRITIS`, `lang="id"`) | Inggris (`★CRITICAL`, `lang="en"`) |
| Blok `[CSS-04a]` (lapisan animasi login `.art-fx`/`.fx-*`) | tidak ada | ada (±24 KB kode+keyframe) |
| Pola `class="' + c + '…"` (rakitan runtime) | tidak ada | ada — ini pemicu temuan A2 |

Drift-nya bukan cuma komentar: setelah komentar dan data-URI dibuang, diff
kode-fungsional masih **1393 baris** (108 KB vs 132 KB).

Dampak:

1. Berkas yang diunduh user **bukan** yang digambarkan `src/`, `CODEMAP.md`,
   README (377 KB), maupun QA-REPORT (bab 7) — semuanya cocok dengan build
   fresh, bukan dengan artefak committed.
2. Klaim QA-REPORT “audit statis LOLOS, 0 temuan” **tidak lagi benar** untuk
   artefak committed (`qa_audit.py` sekarang exit 1 karena A2).
3. Menjalankan `qa_dash.py` terhadap artefak committed berarti menguji kode
   yang tidak ada di `src/` — hasilnya tidak mewakili source of truth mana pun.

Rekomendasi: tetapkan `src/dashboard.src.html` sebagai source of truth (sesuai
rantai build yang didokumentasikan), lalu `rebuild → qa_audit → qa_dash.py →
commit`. Catatan keputusan produk: rebuild akan **menghapus lapisan animasi
login** (`art-fx`) yang hanya ada di artefak basi — kalau animasi itu diinginkan,
backport dulu ke `src/`, baru rebuild. Jangan kirim artefak baru tanpa
`qa_dash.py` (butuh `pip install playwright && playwright install chromium`).

## P1 — perbaiki dalam sprint ini

### P1-1 · `shots/` = 8,3 MB (69% isi repo) tanpa rujukan apa pun

10 PNG valid (9× 1440×900, 2× di antaranya retina 2880×1800, 1× mobile 430×920;
isi `dash-login.png` diperiksa visual — valid, UI Bahasa Indonesia). Tetapi
`grep` ke seluruh `.py`/`.html`/`.md` tidak menemukan satu pun rujukan ke
`shots/`, dan tidak ada dokumen yang menjelaskan untuk apa folder ini
(bukti visual QA? materi rilis?). Opsi: (a) dokumentasikan satu paragraf di
README, atau (b) keluarkan dari git ( unpaid, simpan sebagai artefak rilis /
LFS), atau (c) hapus bila sudah tidak dipakai.

### P1-2 · `QA-DASH-RUN.txt` hanya ringkasan — klaim 200/200 tak teraudit

`QA-RUN.txt` memuat 122 baris `PASS` (terhitung, cocok dengan klaim) — bagus.
`QA-DASH-RUN.txt` hanya 20 baris rekap per blok (11+10+14+24+18+36+10+32+27+11+7
= 200, penjumlahannya benar) **tanpa satu pun baris per-asesi**. Berbeda dengan
landing, tidak ada jejak yang memungkinkan audit independen tiap asersi
dashboard. Rekomendasi: simpan keluaran penuh `qa_dash.py` (tambahkan mode
verbose per-asesi bila belum ada) sebagai `QA-DASH-RUN.txt`, atau catat flag
yang menghasilkan rincian itu.

### P1-3 · Tanpa `.gitignore`, tanpa README root, nesting ganda

- Tidak ada `.gitignore` di root maupun di `pacific-nova-spa/`. Risiko nyata:
  artefak sementara QA (`*.stripped`, `__pycache__/`, `.playwright/`) mudah
  ikut ter-commit. Rekomendasi: `.gitignore` minimal
  (`__pycache__/`, `*.stripped`, `*.log`, `.playwright/`).
- Tidak ada README di root repo; satu-satunya isi root adalah folder
  `pacific-nova-spa/`, sehingga path menjadi `pacific-nova/pacific-nova-spa/…`
  (“repo dalam repo”) dan pendatang baru tidak tahu harus mulai dari mana.
  Rekomendasi: README root 5–10 baris yang menunjuk ke `pacific-nova-spa/README.md`,
  atau ratakan struktur (pekerjaan lebih besar — butuh kesepakatan).

## P2 — minor / kosmetik

| # | Temuan | Rekomendasi |
|---|---|---|
| P2-1 | Estimasi `README` “`--bg hero-bg.png` → output ±4,5 MB” kedaluwarsa; hasil aktual **3,1 MB** (PNG 2,2 MB, 1920×1080) | Perbarui angka di `README.md` + docstring `build.py` |
| P2-2 | Aturan `qa_audit` A2 menandai kelas rakitan runtime (`'…' + c + '…'`) sebagai yatim — false-positive-prone; lolos di `src/` baru hanya karena polanya berubah, bukan karena dijaga | Dokumentasikan pengecualian pola rakitan-runtime di `qa_audit.py`, atau hindari pola itu secara konvensi |
| P2-3 | `QA-RUN.txt` punya 9 baris trailing-whitespace (artefak log) | Abaikan, atau `sed -i 's/[ \t]*$//'` sekali jalan |
| P2-4 | `shots/dash-board.png` vs `shots/dash-people.png` — nama “board” ambigu, tidak 1:1 dengan rute (`#/overview`, `#/influencers`, …) | Rename agar monoton dengan nama rute |
| P2-5 | Riwayat git = 1 commit `first commit` — seluruh evolusi (13 defect landing + 13 defect dashboard di QA-REPORT) tak terlacak | Ke depan: commit kecil per perbaikan agar QA bisa `bisect` |

## Yang dinyatakan SEHAT (tidak perlu tindakan)

- **Kontrak satu-file**: kedua output committed — 0 referensi `src=`/`href=` eksternal
  di markup, 0 token `__HERO_BG__`/`__LOGO_URI__` tersisa, masing-masing token
  tepat 1× di `src/`. Guard `[BUILD-01]` bekerja (build gagal bila token ≠ 1×).
- **`index.html` selaras penuh**: `cmp` build fresh vs committed identik biner.
- **`CODEMAP.md` segar**: regenerasi `qa_map.py` → 72 penanda (39+32+1), beda
  hanya baris tanggal. Klaim “1469/2061 baris” = hitungan `split('\n')`,
  konsisten dengan `wc -l` 1468/2060 + newline akhir — bukan drift.
- **Aset**: `hero-bg.jpg` (158 KB, 1920×1080 — default build), `hero-bg.png`
  (lossless opsional, terdokumentasi), `pacific-nova-logo.png` (368×132 —
  cocok dengan asersi S0 `naturalWidth == 368`), `qa-attach.png` (fixture
  upload 8×8, dipakai `qa_dash.py:381`).
- **Higiene**: LF di semua berkas teks (temu `CR` hanya di byte biner PNG),
  UTF-8 semua, newline akhir ada semua, tanpa bit executable (wajar — semua
  dijalankan via `python3`), tanpa BOM. Satu-satunya trailing-ws di `.md`
  adalah jeda-baris Markdown yang disengaja di `CODEMAP.md`.
- **Secrets**: tidak ada API key/token privat. Kredensial `admin/pacificnova`
  hardcoded di dashboard adalah kredensial demo yang dipajang di UI dan
  didokumentasikan di README + QA-REPORT bab G/J — diterima untuk demo,
  wajib diganti skema auth sebelum produksi (risiko sudah dinyatakan terbuka).
- **Screenshot**: 10/10 header PNG valid.

## Reproduksi temuan P0 (tempel langsung)

```bash
cd pacific-nova-spa
python3 qa_audit.py                      # exit 1: A2 .c di dashboard.html committed
python3 build.py --src src/dashboard.src.html --out /tmp/qa_dash.html
cmp dashboard.html /tmp/qa_dash.html     # BERBEDA (±41 KB)
ls -la dashboard.html /tmp/qa_dash.html  # 427.763 vs 386.144 byte
python3 qa_audit.py src/dashboard.src.html /tmp/qa_dash.html   # LOLOS, exit 0
```

Perintah pemulihan setelah keputusan produk (lihat P0-1):

```bash
cd pacific-nova-spa
python3 build.py --src src/dashboard.src.html --out dashboard.html
python3 qa_audit.py && python3 qa_dash.py   # qa_dash butuh playwright+chromium
```

## Batasan QA ini

1. Suite browser tidak dieksekusi ulang (tanpa `playwright`/Chromium di sini).
2. Isi visual screenshot diperiksa 1 dari 10 (`dash-login.png`); sisanya
   divalidasi header/dimensi/ukuran PNG saja.
3. Tidak ada histori git untuk menentukan arah drift P0 (kapan tepatnya
   `dashboard.html` dan `src/` berpisah) — hanya ada satu commit.

## Status tindak lanjut (10 Sep 2026 — opsi full-fix)

| Temuan | Status | Bukti |
|---|---|---|
| P0-1 artefak basi | **SELESAI** (struktur) · validasi browser **TERTUNDA** | rebuild → 386.144 B (377 KB) ✓ · `qa_audit.py` exit 0 ✓ · `cmp` byte-identik ✓ |
| P1-1 shots/ tak terdokumentasi | **SELESAI** | didokumentasikan di `README.md` (“Berkas pendukung”); 2 duplikat dihapus → 8 berkas, 7,2 MB |
| P1-2 log dash tanpa rincian | **SEBAGIAN** | flag `--verbose` ([QA-06]) ditambahkan ke `qa_dash.py`, stub-test lolos; regenerasi log + 200/200 menunggu env browser |
| P1-3 .gitignore + README root | **SELESAI** | `.gitignore` dan `README.md` root ditambahkan |
| P2-1 estimasi ±4,5 MB | **SELESAI** | dikoreksi → ±3,1 MB di `README.md` + docstring `build.py` (terukur 3100 KB, lolos audit) |
| P2-2 FP-A2 kelas runtime | **SELESAI** | catatan konvensi di `qa_audit.py`, tanpa perubahan perilaku |
| P2-3 trailing-ws log | **SELESAI** | dibersihkan; 122 `PASS` utuh |
| P2-4 nama shots ambigu | **SELESAI** | `dash-board.png` + `dash-people.png` terbukti duplikat konten-identik (1x vs 2x) lalu dihapus; sisa 8 berkas 1:1 dengan rute |
| P2-5 histori 1 commit | TERBUKA (proses) | — |

Catatan keputusan P0-1: rebuild menghapus lapisan animasi login (`art-fx`,
±24 KB) yang hanya ada di artefak basi — diterima sebagai pengembalian ke
source of truth `src/` (pilihan full-fix). Bila animasi itu diinginkan kembali,
implementasikan ulang di `src/dashboard.src.html`, rebuild, lalu jalankan
`qa_dash.py` penuh sebelum kirim.

### Catatan insiden saat perbaikan (transparansi)

Saat menerapkan flag `--verbose`, dua edit paralel ke `qa_dash.py` dalam satu
blok tool menyisipkan 5 baris sampah di sekitar S4.9 (terdeteksi seketika via
`py_compile`: `SyntaxError` baris 302). Berkas dikembalikan murni dari git,
kedua edit diterapkan ulang atomik dalam satu proses dengan assert tepat-1×,
lalu diverifikasi: diff persis 2 hunk yang dimaksud, `py_compile` lolos,
stub-test `check()` (verbose + default) lolos, dan semua berkas lain yang
diedit paralel diaudit (hanya berisi perubahan yang dimaksud). Pelajaran yang
dicatat: jangan pernah melakukan edit paralel ke berkas yang sama.

### Mengapa suite browser belum dijalankan ulang

`pip install playwright` berhasil (venv terisolasi `/tmp/qaenv`, tidak menyentuh
repo), tetapi unduhan Chromium gagal — koneksi TLS ke `cdn.playwright.dev`
di-reset (`ECONNRESET`), tidak ada browser sistem, dan tidak ada akses root
untuk dependensi OS. Perintah validasi yang harus dijalankan di lingkungan
dengan akses CDN sebelum artefak hasil rebuild dikirim:

```bash
cd pacific-nova-spa
python3 -m http.server 8001 &           # qa_dash memakai :8001 bila hidup
python3 qa_dash.py --verbose > QA-DASH-RUN.txt   # 200 asersi dashboard hasil rebuild
python3 qa_spec.py > QA-RUN.txt                  # 122 asersi landing (regresi)
```
