# Pacific Nova — landing + dashboard admin (masing-masing satu file)

Dua berkas berdiri sendiri, satu bahasa desain:

| Berkas | Isi | Ukuran |
|---|---|---|
| `index.html` | 4 view publik: `#/`, `#/about`, `#/faq`, `#/passport` (Nova Passport + kartu member) | ±327 KB |
| `dashboard.html` | papan kerja admin: Login, Data Influencer, NAS Report (report + leaderboard + create), Manage Content | ±377 KB |

Keduanya **mandiri**: seluruh CSS/JS inline, logo dan gambar di-inline sebagai data URI,
nol request keluar. Tidak ada CDN, tidak ada `node_modules`, tidak ada folder aset yang
harus ikut terunduh. Jalan dari klik ganda (`file://`) maupun dari server.

## Yang boleh di-download user

```
index.html        ← halaman publik
dashboard.html    ← dashboard admin
```

`src/index.src.html` dan `src/dashboard.src.html` **bukan** untuk user — itu template yang
masih berisi token placeholder, jadi kalau dibuka akan tampak rusak (logo pecah, hero putih).

## Berkas pendukung (tidak untuk user)

| Path | Isi |
|---|---|
| `src/*.src.html` | template sumber — satu-satunya yang boleh diedit manual |
| `assets/hero-bg.jpg` + `assets/pacific-nova-logo.png` | gambar yang di-inline setiap build (default) |
| `assets/hero-bg.png` | alternatif hero lossless untuk `--bg` (output ±3,1 MB) |
| `assets/qa-attach.png` | fixture upload 8×8 untuk `qa_dash.py` |
| `shots/*.png` | bukti visual QA: 8 tangkapan layar dashboard (±7 MB) — arsip, bukan bagian produk |
| `QA-*.md` / `QA-*.txt`, `CODEMAP.md` | laporan QA, log mentah, dan peta kode |

Pemetaan `shots/` → rute: `dash-login` (layar masuk) · `dash-overview` (`#/overview`) ·
`dash-influencers` (`#/influencers`) · `dash-report` (`#/report`) ·
`dash-leaderboard` (`#/leaderboard`) · `dash-review` (`#/create`, layar re-verification) ·
`dash-content` (`#/content`) · `dash-mobile` (drawer ≤960px).

## Rantai kerja

```
src/index.src.html       ──[ python3 build.py ]──▶  index.html
src/dashboard.src.html   ──[ python3 build.py --src src/dashboard.src.html --out dashboard.html ]──▶  dashboard.html
                                   │
                                   ├─ python3 qa_audit.py   (statis A–H, MEMERIKSA KEDUA pasangan file)
                                   ├─ python3 qa_spec.py    (122 asersi fungsional · landing)
                                   ├─ python3 qa_dash.py   (200 asersi fungsional · dashboard)
                                   └─ python3 qa_map.py     (regenerasi CODEMAP.md: 72 penanda)
```

| Perintah | Kapan |
|---|---|
| `python3 build.py` | setelah mengedit `src/index.src.html` |
| `python3 build.py --src src/dashboard.src.html --out dashboard.html` | setelah mengedit `src/dashboard.src.html` |
| `python3 build.py --bg assets/hero-bg.png` | hero lossless, output ±3,1 MB |
| `python3 qa_audit.py` | cek cepat tanpa browser; `exit 1` kalau ada temuan |
| `python3 qa_spec.py` / `python3 qa_dash.py` | suite Chromium (`pip install playwright && playwright install chromium`) |
| `python3 qa_map.py` | setelah menambah/memindah blok anotasi |

`qa_dash.py` membandingkan angka di layar dengan angka yang **dihitung ulang dari
localStorage** — jadi ia menangkap bug tipe "NAS tersimpan dua kali" atau "yang pending
ikut dihitung". Kalau server `:8001` mati, suite otomatis pindah ke `file://`.

## Memakai dashboard

Buka `dashboard.html` → **username `admin` / password `pacificnova`** (kredensial demo,
dipajang di layar masuk; belum ada server sungguhan).

| Rute | Fungsi |
|---|---|
| `#/overview` | KPI, bagan NAS per bulan, antrean verifikasi, papan peringkat sementara, aktivitas terbaru |
| `#/influencers` | CRUD influencer: Nama, Member Number, Tier, Nova Status, **NAS** |
| `#/report` | semua entry NAS: filter (orang/status/cari), verifikasi, undo, catatan, hapus, ekspor CSV |
| `#/leaderboard` | peringkat per periode (semua waktu / 30 hari / 90 hari), podium + bar progress |
| `#/create` | catat NAS → **layar re-verification** → `Lanjutkan prosesnya` |
| `#/content` | FAQ, About (+Contact), dan benefit per tier |

Hal yang perlu diketahui admin:

- **Tier dan angka NAS tidak pernah diketik.** Keduanya diturunkan dari entry yang
  *terverifikasi* (`[JS-05]`). Menambah 30 NAS bisa menaikkan tier; menggeser ambang
  tier di Manage Content → About langsung mengubah semua tier di tabel.
- **Create NAS masuk sebagai `pending`.** Baru setelah tombol ✓ di NAS Report, angkanya
  dihitung ke total. Itu sengaja: satu entri selalu melewati dua mata (yang menginput,
  yang mengesahkan).
- Semua perubahan tersimpan di `localStorage` (`pn.admin.db.v2`, sesi di
  `pn.admin.auth.v2`). Centang "tetap masuk" → `localStorage`; lepas → `sessionStorage`.
  Tombol **Export JSON** mengunduh seluruh basis data, **Reset demo** mengembalikan seed.
- Manage Content bekerja di atas **draf**: chip di kanan atas berubah jadi "belum
  disimpan", dan `Simpan perubahan` yang memindahkan draf ke DB. Tombol `Salin JSON`
  menyalin blok yang bisa ditempel langsung ke `src/index.src.html` (strukturnya sama).

## Mengubah hal yang sering diubah

| Mau apa | Ke mana |
|---|---|
| Ganti teks hero / About / FAQ publik | `src/index.src.html`, blok `[MK-05]`, `[MK-06]` |
| Tambah / ubah pertanyaan FAQ dari admin | `#/content` → tab FAQ (lalu tempel JSON-nya ke landing) |
| Ganti data member demo dengan API nyata | konstanta `MEMBERS` di `[JS-06]` landing |
| Ganti seluruh sumber data admin dengan API nyata | objek `DB` + `load()/save()` di `[JS-06]` dashboard |
| Tambah kolom / aturan NAS | fungsi turunan di `[JS-05]` (`nasOf`, `tierOf`, `nextTier`, `ranking`) |
| Tambah activity type atau nilai NAS default | `DB.activities` di `[JS-06]` seed (bisa diedit tanpa menyentuh kode) |
| Ganti gambar hero / logo | `--bg` / `--logo` saat build |
| Tambah ikon | `<symbol>` di `[MK-01]`; id-nya harus sama dengan yang dipakai data (`qa_dash.py` S0.9 menjaga ini) |

Menukar `localStorage` dengan API sungguhan cukup di satu tempat di dashboard: ganti isi
`load()` dengan `fetch`, dan `save()` dengan `POST`. Selama bentuk objeknya sama
(`v, tiers, statuses, activities, people, nas, content`), seluruh renderer tidak
perlu disentuh. Bungkus `fetch` dengan `try/catch` dan tampilkan `toast(..., 'bad')`
saat gagal — `save()` sudah melakukan itu untuk kuota penyimpanan penuh.

## Kontrak yang jangan dilepas

1. **Satu file per hasil build.** Tidak boleh ada `src=`/`href=` ke luar (`data:` atau `#`
   saja). Itu sebabnya gambar selalu di-inline.
2. **Satu token = satu titik sisip.** Nama placeholder tidak boleh muncul di
   komentar/dokumentasi; `replace()` bersifat global (dijaga `[BUILD-01]`).
3. **Komentar HTML tidak boleh memuat `--`.** Browser menutup komentar di situ dan sisa
   teksnya jadi konten nyata — ini pernah menggeser hero 532px, dan (bab 7) nyaris
   menjebak legenda `dashboard.src.html` lewat tulisan `--src` di komentar.
4. **Angka breakpoint CSS = angka di JS.** Landing: 760px; dashboard: 960px
   (`MQ_DRAWER`). `qa_audit.py` grup G menurunkan angka ini dari CSS, bukan ditulen.
5. **Semua nilai dinamis lewat `esc()`** sebelum masuk `innerHTML` (kedua berkas).
6. **Id dalam sprite = kontrak dengan data.** Ikon yang direferensikan seed tapi tidak
   ada `<symbol>`-nya tidak error — hanya jadi lingkaran kosong. Diperiksa S0.9.
7. **Nama kelas tidak boleh ditabrakkan.** Kelas `.drawer` di dashboard adalah *tombol*
   menu; menaruh scrim dengan kelas yang sama membuat seluruh topbar tidak bisa diklik.

Peta lengkap penanda kode (72 baris, dibangkitkan, nomornya tidak bisa basi): **`CODEMAP.md`**.
Riwayat defect & cara menjalankan QA: **`QA-REPORT.md`** (log mentah: `QA-RUN.txt`, `QA-DASH-RUN.txt`).
