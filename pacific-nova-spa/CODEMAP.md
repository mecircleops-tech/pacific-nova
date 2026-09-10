# Peta kode — Pacific Nova (landing + dashboard admin)

Dihasilkan otomatis oleh `qa_map.py` dari kode sumber pada 09 Sep 2026.  
Kolom "Baris" menunjuk nomor baris di file source — jangan di-update manual, jalankan ulang skripnya.

**Cara pakai:** `grep -n "\[JS-08\]" src/dashboard.src.html`  ·  ★KRITIS = jangan dipindah tanpa alasan (halaman rusak / file unduhan tidak mandiri)  ·  ◆PENTING = interaksi atau aksesibilitas yang hilang kalau dilepas.

## Landing page (publik)

`src/index.src.html` · 1469 baris · 39 penanda

| Penanda | Tingkat | Baris | Isi |
|---|---|---:|---|
| `CSS-01` | ★KRITIS | 59 | dasar global |
| `CSS-02` | · | 89 | lapisan latar dekoratif (semua view KECUALI home) |
| `CSS-03` | ★KRITIS | 116 | shell + nav sticky |
| `CSS-04` | ★KRITIS | 199 | mekanisme SPA view |
| `CSS-05` | ★KRITIS | 233 | hero home (judul/subjudul/CTA terpusat, layar lebar & kecil) |
| `CSS-06` | ◆PENTING | 277 | layout dokumen (About + FAQ berbagi kelas yang sama) |
| `CSS-07` | · | 323 | kartu tier (About) |
| `CSS-08` | · | 333 | alat + daftar FAQ (render dari data, lihat [JS-13]) |
| `CSS-09` | · | 370 | band CTA penutup About & FAQ (dipakai dua view, jangan di-duplikat) |
| `CSS-10` | ★KRITIS | 380 | target deep-link #/about#contact |
| `CSS-11` | ◆PENTING | 391 | view My Nova Passport |
| `CSS-11a` | ◆PENTING | 410 | ring fokus keyboard DI DALAM pill pencarian. |
| `CSS-12` | ★KRITIS | 529 | kontrak responsive |
| `CSS-13` | ◆PENTING | 594 | kontrak gerak |
| `JS-00` | · | 983 | KONTRAK SKRIPT |
| `JS-01` | ★KRITIS | 1002 | DOM HANDLES |
| `JS-02` | ◆PENTING | 1030 | satu sumber angka breakpoint |
| `JS-03` | · | 1038 | hash router — format rute |
| `JS-04` | ★KRITIS | 1074 | render() — satu fungsi yang mengganti SEMUA state view |
| `JS-05` | ◆PENTING | 1126 | hamburger layar kecil |
| `JS-06` | ★KRITIS | 1147 | DATA MEMBER — satu-satunya tempat menukar data |
| `JS-07` | ★KRITIS | 1193 | normalisasi, pencarian, dan escaping |
| `JS-08` | ★KRITIS | 1236 | formatter tanggal — dua zona, jangan ditukar |
| `JS-09` | ◆PENTING | 1255 | angka berjalan + clock |
| `JS-10` | · | 1281 | render isi kartu |
| `JS-11` | ★KRITIS | 1318 | tiga keadaan kartu: ada hasil / tidak ketemu / reset |
| `JS-12` | ◆PENTING | 1370 | kejadian pada form |
| `JS-13` | · | 1401 | FAQ: data [JS-06] -> <details>, plus search + chip kategori |
| `JS-14` | ★KRITIS | 1442 | self-check struktur lalu boot |
| `MK-00` | ★KRITIS | 11 | PETA KODE — baca ini sebelum mengedit apa pun |
| `MK-01` | ★KRITIS | 607 | SVG sprite = SATU-satunya sumber ikon. |
| `MK-02` | · | 627 | lapisan dekoratif murni — aria-hidden, pointer-events:none. |
| `MK-03` | ★KRITIS | 639 | navbar = satu-satunya navigasi antar view. |
| `MK-04` | ◆PENTING | 666 | menu layar kecil. Daftarnya adalah cerminan nav |
| `MK-05` | · | 696 | VIEW ABOUT  (#/about) |
| `MK-06` | · | 829 | VIEW FAQ (#/faq) |
| `MK-07` | ★KRITIS | 876 | VIEW MY NOVA PASSPORT (#/passport) |
| `MK-08` | ◆PENTING | 889 | form pencarian member. |
| `MK-09` | · | 913 | empty-state pencarian gagal. #nfQuery diisi lewat |

## Dashboard admin

`src/dashboard.src.html` · 2061 baris · 32 penanda

| Penanda | Tingkat | Baris | Isi |
|---|---|---:|---|
| `CSS-01` | ★KRITIS | 40 | TOKEN DESAIN  ·  disalin persis dari landing page. |
| `CSS-02` | · | 81 | lapisan latar (blob + grain) sama seperti landing |
| `CSS-03` | ◆PENTING | 101 | komponen dasar (dipakai semua halaman) |
| `CSS-04` | ★KRITIS | 173 | halaman LOGIN. |
| `CSS-05` | ★KRITIS | 214 | kerangka aplikasi: sidebar + area konten. |
| `CSS-05a` | ★KRITIS | 305 | batang memakai height:%, jadi kolomnya harus punya |
| `CSS-05b` | ★KRITIS | 297 | .muted / dt / dd di dalam panel navy ikut terang. |
| `CSS-06` | · | 257 | tabel data (Influencer, NAS Report) |
| `CSS-07` | ★KRITIS | 367 | responsive. 960px = ambang sidebar jadi drawer. |
| `CSS-07a` | ★KRITIS | 382 | scrim = elemen .scrim tersendiri (bukan ::after), supaya |
| `CSS-08` | · | 268 | utilitas aksesibilitas: teks khusus pembaca layar, tautan |
| `JS-00` | · | 855 | KONTRAK SKRIPT |
| `JS-01` | · | 895 | TOAST & MODAL |
| `JS-02` | ★KRITIS | 936 | ROUTER + GERBANG AUTH. |
| `JS-03` | · | 988 | LOGIN & LOGOUT |
| `JS-04` | ◆PENTING | 1041 | DRAWER layar kecil. |
| `JS-05` | ★KRITIS | 1066 | DATA TERHITUNG. |
| `JS-06` | ★KRITIS | 1107 | DB + SEED + PERSIST. |
| `JS-07` | · | 1264 | RENDER SEMUA HALAMAN |
| `JS-08` | ★KRITIS | 1682 | CREATE NAS  ·  dua langkah, satu sumber angka. |
| `JS-09` | ★KRITIS | 1810 | MANAGE CONTENT. |
| `JS-10` | ★KRITIS | 2033 | SELF-CHECK lalu BOOT. |
| `MK-00` | ★KRITIS | 11 | PETA KODE  ·  baca ini sebelum mengedit apa pun |
| `MK-01` | ★KRITIS | 423 | SVG sprite = satu-satunya sumber ikon. |
| `MK-02` | ★KRITIS | 474 | HALAMAN LOGIN. |
| `MK-03` | ★KRITIS | 532 | kerangka aplikasi: sidebar (navigasi hash) + main. |
| `MK-04` | · | 589 | OVERVIEW : diisi JS dari DB, tidak ada angka hardcode di markup --> |
| `MK-05` | ◆PENTING | 617 | DATA INFLUENCER. |
| `MK-06` | ◆PENTING | 653 | NAS REPORT + filter + aksi verifikasi --> |
| `MK-07` | · | 690 | LEADERBOARD : peringkat dihitung, bukan disimpan --> |
| `MK-08` | ★KRITIS | 710 | CREATE NAS : form lalu layar verifikasi. |
| `MK-09` | ◆PENTING | 785 | MANAGE CONTENT: FAQ, About (termasuk Contact), |

## Build

| Penanda | Tingkat | Baris | Isi |
|---|---|---:|---|
| `BUILD-01` | ★KRITIS | 33 | satu token = satu titik sisip. replace() bersifat global, jadi |

## Rantai yang harus jalan berurutan

```
src/index.src.html      ← diedit untuk halaman publik
src/dashboard.src.html  ← diedit untuk papan kerja admin
      │  python3 build.py                                   (landing   → index.html)
      │  python3 build.py --src src/dashboard.src.html --out dashboard.html
      │        (inlining + guard [BUILD-01]: token harus tepat 1x)
      ▼
index.html · dashboard.html   ← file mandiri yang di-download user
      │  python3 qa_audit.py     (A–H, kedua pasangan file)
      │  python3 qa_spec.py      (122 asersi fungsional landing)
      │  python3 qa_dash.py      (200 asersi fungsional dashboard)
      ▼
LOLOS / TEMUAN
```
