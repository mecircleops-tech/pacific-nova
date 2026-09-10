# Laporan QA — Pacific Nova (landing + dashboard admin)
Tanggal: 10 Sep 2026 · Peran: QA Tester (bukan penulis kode)
Objek: `index.html` hasil build (327 KB) dan `dashboard.html` (377 KB) ·
Lingkungan: Chromium (Playwright). Landing diuji lewat `file://`; dashboard lewat
`http://localhost:8001` **plus** 7 asersi tambahan lewat `file://` — yaitu kondisi
sesungguhnya saat user mendownload satu file.

## Ringkasan (bab A–E: landing)

| Aspek | Hasil |
|---|---|
| Audit statis `qa_audit.py` (grup A–H) | **LOLOS**, 0 temuan |
| Suite fungsional `qa_spec.py` | **122/122 LULUS**, 0 gagal |
| Defect ditemukan & diperbaiki selama perapian | **13** (4 ★KRITIS, 6 ◆PENTING, 3 minor) |
| Request keluar file | **0** (logo + hero = data-URI) |
| Console error / warning | **0** |

## A. Defect yang ditemukan lalu diperbaiki

| # | Tingkat | Tag | Gejala sebelum diperbaiki | Akar masalah | Perbaikan | Pagar otomatis sekarang |
|---|---|---|---|---|---|---|
| 1 | ★KRITIS | `MK-00` | Hero bergeser 532px ke bawah; home bisa di-scroll; layout 390px kacau | Teks legenda memuat `-->` → komentar HTML tertutup dini, sisanya **dirender jadi konten** | Legenda ditulis ulang (tanpa `--`); deretan strip diganti `─` | `qa_audit` D6/D7/D8 + `qa_spec` S0 (pageTop=0, nol teks lepas) |
| 2 | ★KRITIS | `BUILD-01` | File build membengkak 327 → 801 KB | Nama token placeholder ditulis juga di dalam komentar; `str.replace()` global → base64 masuk 2× | `build.py` menolak build bila token muncul ≠ 1× | guard di `build.py` (diverifikasi dengan sabotase: exit 1) |
| 3 | ★KRITIS | `JS-07` | 3 titik `innerHTML = '…' + nilai` tanpa escaping; begitu data pindah ke API, satu label bisa jadi `<img onerror>` | Tidak ada sanitizer | helper `esc()` dipakai di `fillRows`/`fillBenefits`/`renderFaq`; id ikon divalidasi ke sprite (`SPRITE`) | `qa_spec` S2: payload `<b>`/`<img onerror>` tidak pernah jadi elemen |
| 4 | ★KRITIS | `JS-08` | Stamp "NAS recently updated" bisa menunjukkan **tanggal kemarin** sambil jam hari ini (nyata sebelum 07:00 WIB) | Satu formatter `timeZone:UTC` dipakai untuk dua kebutuhan | `D_UTC` untuk tanggal ISO history, `D_LOCAL`/`T_LOCAL` untuk stamp | `qa_spec` S2 membandingkan stamp dengan tanggal & jam lokal browser |
| 5 | ◆PENTING | `JS-04`/`JS-09` | `setInterval` clock terus menulis tiap detik seumur tab walau user sudah pindah view | Tidak ada teardown | `stopClock()` dipanggil router saat meninggalkan passport, dan di `reset()`/`showNotFound()` | `qa_spec` S2: stamp beku setelah pindah view; search berulang tidak menumpuk tick |
| 6 | ◆PENTING | `JS-01` | Risiko `ReferenceError` (TDZ): `closeSheet()` memakai `burger`/`sheet` yang baru dideklarasikan 130 baris di bawah | Urutan deklarasi rapuh | Blok DOM handles dipindah ke atas dengan alasan eksplisit di anotasi | `qa_audit` B2 (semua `getElementById` punya pasangan id di DOM) |
| 7 | ◆PENTING | `JS-04` | Deep link `#/passport?member=…` hanya jalan saat load awal; back/forward browser tidak menyinkronkan kartu | Logika search duduk di `boot()` | Sinkronisasi `?member=` dipindah ke `render()` (state `lastMember`) | `qa_spec` S2: 3 jalur deep link (member valid, ganti member, member tak dikenal) |
| 8 | ◆PENTING | `JS-02`/`CSS-12` | Penutup sheet memakai `window.innerWidth > 760` — bisa desync dari CSS saat ada scrollbar | Angka breakpoint ada di dua tempat | `matchMedia('(max-width: 760px)')` + listener `change` | `qa_spec` S5: melebarkan jendela menutup sheet; burger hilang di 1200px |
| 9 | ◆PENTING | `CSS-11a` | Input pencarian **tidak punya ring fokus keyboard** — `.search input{outline:0}` menekan `:focus-visible` global | Spesifisitas | Aturan `:focus-visible` khusus diletakkan setelahnya (urutan penting, dicatat di kode) | `qa_spec` S6: semua target Tab pertama punya outline nyata |
| 10 | ◆PENTING | `MK-08` | Pesan "no record" tidak dibacakan pembaca layar; `aria-invalid` tidak ikut diset saat submit kosong | Tidak ada live region | `role=status` + `aria-live=polite` + `aria-describedby=note`; `aria-invalid` di kedua jalur error | `qa_spec` S6 (live region,-describedby) + S2 (aria-invalid) |
| 11 | · | `JS-04` | `aria-current="false"` tertinggal di link non-aktif | `setAttribute` terus-menerus | `removeAttribute` saat bukan view aktif | `qa_spec` S1 |
| 12 | · | `CSS-*`/`MK-*` | Dead code: `.grid2`, `.serif`, `details.qa .qa-body + .qa-body`, class `.cta` & `.intro` tanpa aturan, `role="navigation"` di div dalam `<nav>` (landmark ganda) | Sisa iterifikasi | Semuanya dihapus; label dipindah ke `<nav aria-label="Main">`, sheet dapat `role=group` | `qa_audit` A1/A2 (CSS mati & yatim) |
| 13 | · | `CSS-13` | `scroll-behavior: smooth` tetap jalan saat `prefers-reduced-motion: reduce` | Belum dicakup blok reduce | `html { scroll-behavior: auto }` di dalam media query itu | `qa_spec` S6 (reduced-motion context) |

## B. Perilaku yang diterima sengaja (bukan bug — dicatat di kode)

* **Anchor `#/about#contact` ter-clamp** di scroll maksimum (mendarat ±438px, bukan 92px) karena
  panel kontak adalah blok terakhir sebelum band CTA; tidak ada ruang scroll lagi. Ini perilaku
  standar browser — jangan "diperbaiki" dengan menambah padding kosong (dicatat di `JS-03`).
* **`id="history"`** bertabrakan dengan `window.history`; karena itu elemen selalu diambil lewat
  `out.list` dan tidak ada satu pun kode yang menulis `history` telanjang (dicatat di `JS-10`).
* **Kontara `#contact`** dan semua gambar tidak pernah punya path relatif (kontrak satu file).
* Teks antarmuka tetap Bahasa Inggris (bahasa produk); komentar penjelas Bahasa Indonesia.

## C. Inventaris pengujian (122 asersi)

| Bagian | Isi | Jumlah | Hasil |
|---|---|---:|---|
| **S0** | kontrak satu file: 0 request, 0 error, logo & hero data-URI, tanpa konten liar, tahan tanpa JS | 8 | 8 LULUS |
| **S1** | router: 4 view, title, hash asing, aria-current, state nav, anchor | 10 | 10 LULUS |
| **S2** | passport: normalisasi lookup, Total dari history, 7 tanggal unik, My Benefit, zona waktu stamp, clock (hidup/mati), 3 keadaan kartu, clear/Escape, deep link, XSS, input aneh | 27 | 27 LULUS |
| **S3** | konten: About (4/3/3 + contact + CTA), tabrakan badge tier, tinggi kartu, nav Round 5, FAQ 10 + chip + search + empty-state + accordion | 13 | 13 LULUS |
| **S4** | layout: 15 viewport termasuk **tepat di** 759/760/761 dan 939/940/941, 4 view × 6 ukuran, grid kartu, pusat hero 390/1440, ultrawide 2560, layar pendek 640 | 40 | 40 LULUS |
| **S5** | hamburger: state awal, buka/Esc/klik-luar/auto-close, fokus masuk sheet, 4 tujuan, resize 760→1200 | 9 | 9 LULUS |
| **S6** | aksesibilitas & motion: nama landmark/kontrol, alt, live region, describedby, landmark ganda, 1×h1 per view, h2/summary, urutan Tab, ring fokus, kontras navy, reduced-motion | 15 | 15 LULUS |

Log mentah lengkap ada di **`QA-RUN.txt`** (sebelah file ini).

## D. Cara menjalankan ulang

```bash
python3 qa_audit.py                 # statis, cepat, tidak butuh browser
python3 qa_spec.py                  # fungsional (playwright + chromium)
python3 build.py && python3 qa_audit.py && python3 qa_spec.py   # penuh
```

Keduanya `exit code 1` kalau ada temuan — siap dijadikan gerbang sebelum mengirim file.

## E. Sisa risiko yang saya nyatakan terbuka

1. **Font.** Inter tidak dimuat (sengaja: tidak ada CDN) → mesin tanpa Inter memakai fallback
   sistem; metrik judul bisa bergeser ±1 baris di layar 360px. Tidak ada overflow (S4), tapi
   tampilan bisa sedikit berbeda antar OS.
2. **`backdrop-filter`** pada nav/panel: Safari lama/Chrome dengan GPU off → glass jadi solid
   transparan. Masih terbaca, tidak ada teks hilang.
3. **Uji pembaca layar manual** (NVDA/VoiceOver) belum dijalankan di lingkungan ini — yang saya
   verifikasi adalah kontrak ARIA/HTML-nya, bukan perilaku tiap screen reader.
4. **Data masih demo** di `MEMBERS`; saat ditukar jadi `fetch`, tambah `try/catch` + pesan gagal
   (`note`) — titik masuknya sengaja disatukan di `JS-06` supaya hanya perlu satu tempat.

---

# Bab 7 — dashboard admin (`dashboard.html`, 377 KB)

Suite baru: **`qa_dash.py` · 200 asersi · 200 LULUS**. Prinsipnya: jangan percaya teks di
layar — angka yang tampil dibandingkan dengan hasil hitung ulang dari `localStorage`
(`pn.admin.db.v2`).

## F. Defect dashboard yang ditemukan lalu diperbaiki

| # | Tingkat | Gejala | Akar | Perbaikan | Penjaga sekarang |
|---|---|---|---|---|---|
| 1 | ★KRITIS | Teks legenda ikut tampil di halaman / layout bergeser | komentar HTML memuat `--src` → browser menutup komentar di situ | komentar ditulis ulang tanpa dua strip | `qa_audit.py` D6/D7/D8 (berjalan untuk kedua berkas) |
| 2 | ★KRITIS | Ikon benefit "6-hour early booking window" jadi lingkaran kosong, tanpa error apa pun | seed memakai `i-clock` yang tidak ada di sprite | `<symbol id="i-clock">` ditambahkan | `qa_dash.py` S0.9 — setiap id ikon di data harus punya `<symbol>` |
| 3 | ★KRITIS | Bagan "NAS masuk per bulan" kosong: label bulan ada, batangnya tidak | `height:%` pada `<i>` di dalam `.col` yang tingginya auto (`align-items:flex-end`) → persentase tidak resolve | `.chart` jadi `align-items:stretch`, `.col` `height:100%` | S2.3c (≥4 batang punya tinggi piksel nyata) + S2.3d warna label |
| 4 | ★KRITIS | Label panel re-verification (AKTIVITAS, TANGGAL, BUKTI …) dan "perlu tindakan" di KPI tidak terbaca | `.kv dt` / `.muted` membawa warna gelap ke atas `.panel.navy` | `[CSS-05b]` override warna teks di panel navy | S2.9b (screenshot + assertion computed color) |
| 5 | ★KRITIS | Pada layar ≤960px seluruh topbar tidak bisa diklik; tombol menu mati | scrim drawer diberi kelas `.drawer` — padahal kelas itu sudah dipakai **tombol** → tombol jadi `position:fixed; inset:0` | scrim dipindah ke kelas `.scrim` (+ `#scrim`), `.topbar` diangkat ke z-31 | S8.2b (kotak tombol seukuran tombol) + S8.5b/c (toggle dua arah) |
| 6 | ◆PENTING | Caption tabel terlihat sebagai teks besar di desktop, `skip link` tidak pernah muncul | blok utilitas `[CSS-08]` terselip ke dalam `@media (max-width:420px)` | blok dipindah ke tingkat atas | S8.22 (caption tingginya <2px) + S8.23 + S8.12 |
| 7 | ◆PENTING | Layar login mati: panel ilustrasi tanpa ticker & catatan sesi | `seedTicker()`/`loginNote()` hanya dipanggil `renderAll()`, yang dilewati guard saat guest | dipanggil di cabang guest `[JS-02a]` | S1.8 |
| 8 | ◆PENTING | Nilai NAS default tidak terisi; select aktivitas tampak kosong | `fillSelects()` mengembalikan nilai lama `''` ke select yang tidak punya opsi kosong | fallback opsi pertama `[JS-07c]` | S5.4 |
| 9 | ◆PENTING | Guest yang mengetik `#/report`, setelah login dilempar ke Overview (tautan dalam hilang) | handler login selalu `go('overview')` | hormati hash yang ada kalau valid `[JS-03a]` | S1.1 & S1.5 |
| 10 | ◆PENTING | Kegagalan login tidak diumumkan ke pembaca layar | `#loginErr` bukan live region | `role="alert"` + `aria-live="polite"` | S1.4 |
| 11 | minor | Field kosong disambut pesan "password salah" | satu cabang validasi untuk semua | pesan dipisah: "Isi username dan password dulu." | S1.3 |
| 12 | minor | Id data berubah tiap reload selama belum ada perubahan | seed tidak pernah ditulis ke storage | `[JS-07a]` `save()` saat boot | S0.8 & S9.1b |
| 13 | minor | Password demo tertinggal di kolom setelah logout | — | `$('pass').value = ''` di logout | S1.9 |

Perbaikan tambahan yang tidak gejala tapi mencegah rusak: pratinjau lampiran di panel
review (gambar kecil dari data-URI), tombol `Export JSON`/`Reset demo`, caption tabel,
skip link, `dirty()` di chip sinkron, dan draft content yang **tidak** hangus saat
berpindah tab (S7.4).

## G. Yang diterima sengaja (bukan bug — didokumentasikan di kode)

1. **Kredensial demo tertulis di layar.** Belum ada server; menyembunyikan `admin/pacificnova`
   tidak menambah keamanan apa pun, hanya memperlambat uji coba.
2. **Entri `Create NAS` masuk sebagai `pending`.** Sengaja — angka hanya dihitung setelah
   satu verifikasi lagi di NAS Report.
3. **Lampiran disimpan sebagai metadata** (nama + ukuran); gambar <60 KB ikut disimpan
   sebagai data-URI supaya bisa dipreview. File besar tidak ditahan di `localStorage`
   (kuota 5 MB) dan `save()` menangkap `QuotaExceededError` → chip jadi `gagal simpan`.
4. **Semua data hidup di browser.** Bersihkan storage = kembali ke seed. Export/Reset disediakan.

## H. Inventaris pengujian (200 asersi)

| Bagian | Isi | Jumlah | Hasil |
|---|---|---:|---|
| **S0** | boot & file mandiri: 0 request keluar, 0 error konsol, logo & ilustrasi data-URI, 6 rute, seed dipersistenkan, **sprite ↔ data**, bentuk DB, 3 pending awal | 11 | 11 LULUS |
| **S1** | login: guard `#/report` saat guest, password salah, field kosong, live region, deep link dipertahankan, remember me → localStorage vs sessionStorage, logout, ticker | 10 | 10 LULUS |
| **S2** | overview: 4 KPI vs hitung ulang, bagan 6 bulan (punya tinggi, warna label), top 5, antrean, 5 aktivitas terbaru, chip sidebar, kontras teks navy, tanpa NaN | 14 | 14 LULUS |
| **S3** | data influencer: **kolom NAS = Σ verified per orang (9 baris)**, kontrak Joshua·0983·100·Blue Nova, jumlah entry, cari/filter tier+status (AND), total footer, tambah + 2 validasi + edit + riwayat + hapus (ledger ikut bersih), hint | 24 | 24 LULUS |
| **S4** | report: semua entry, urut tanggal desc (12 baris), 4 KPI, filter status/orang/cari, verifikasi → verified+nominal, undo, catatan, hapus, modal bukti, ekspor CSV, caption | 18 | 18 LULUS |
| **S5** | **create NAS 2 langkah**: tanggal default & kalender, opsi dari daftar influencer, 4 validasi (orang, 0, plafon, masa depan), auto-fill dari activity type, lampiran, review menampilkan orang + aktivitas + tanggal + **+NAS** + bukti (dengan pratinjau) + status awal + **NAS sekarang → sesudah** + tier + riwayat, `Kembali` tidak menulis apa pun, `Lanjutkan prosesnya` commit **pending**, form reset, sorotan baris, **pending tidak dihitung**, setelah disahkan +N tepat, tier ikut naik | 36 | 36 LULUS |
| **S6** | leaderboard: podium 3, urutan menurun, posisi 1 = maksimum, 30 hari = Σ dalam rentang, tab `aria-selected`, bar ≤100%, petunjuk tier | 10 | 10 LULUS |
| **S7** | manage content: FAQ (edit = draf, +1 baris, urutan, hapus, validasi, kategori, simpan, bertahan setelah reload), About (lede/statistik/langkah), **ambang tier → tabel influencer ikut berubah lalu kembali**, Contact 6 field + `aria-invalid`, benefit per tier (label/meta/ikon/jumlah/hapus, opsi ikon ⊂ sprite), salin JSON | 32 | 32 LULUS |
| **S8** | responsif & a11y: 1280/900/400, drawer (buka, scrim, Esc, toggle dua arah, auto-tutup saat pilih rute), tanpa scroll horizontal, semua tombol & kontrol ternamai, skip link, fokus masuk/keluar modal, `scope=col`, alt gambar, `aria-current` | 27 | 27 LULUS |
| **S9** | ketahanan data: localStorage korup (sesi tidak ikut hilang, DB di-seed ulang), entry yatim tanpa crash, HTML di data di-escape, leaderboard tetap urut dengan data aneh, 0 error konsol, 0 teks cacat | 11 | 11 LULUS |
| **S10** | `file://` murni (berkas unduhan): login, data terbaca, tabel 9 orang, kontrak Joshua, report terisi, 0 request keluar, 0 error | 7 | 7 LULUS |

Log mentah: **`QA-DASH-RUN.txt`**.

## I. Cara menjalankan ulang (kedua berkas)

```bash
python3 build.py && python3 build.py --src src/dashboard.src.html --out dashboard.html
python3 qa_audit.py && python3 qa_spec.py && python3 qa_dash.py
python3 qa_map.py                 # regenerasi CODEMAP.md setelah memindah blok
```

Semua `exit code 1` kalau ada temuan → siap jadi gerbang sebelum file dikirim.
`qa_dash.py` memakai `http://localhost:8001` kalau server hidup, dan otomatis jatuh ke
`file://` kalau tidak.

## J. Sisa risiko bab 7 (dinyatakan terbuka)

1. **Belum ada backend.** `load()`/`save()` adalah satu-satunya titik yang perlu ditukar
   `fetch`; `try/catch` baru ada untuk kuota penyimpanan, bukan untuk jaringan gagal.
2. **Role tunggal.** Semua yang login adalah `admin` (peran/izin belum ada lantainya).
3. **Uji manual screen reader** (NVDA/VoiceOver) belum dijalankan di lingkungan ini — yang
   diverifikasi adalah kontrak ARIA/fokus/label, bukan perilaku tiap pembicara.
4. **Lampiran besar** sengaja tidak ditahan → di produksi perlu tautan ke storage; kolom
   `attachment.dataUrl` sudah disiapkan supaya tidak mengubah bentuk record.
5. **Font**: sama seperti landing — Inter tidak dimuat dari CDN, jadi metrik bisa bergeser
   di mesin tanpa Inter. Tabel sudah diuji sampai 400px (S8.7/S8.8), tapi angka lebar
   kolom bukan dijamin identik antar OS.
