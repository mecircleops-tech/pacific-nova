# Pacific Nova

Satu folder produk: landing page + dashboard admin, masing-masing satu file HTML mandiri.

- **Mulai dari sini:** [`pacific-nova-spa/README.md`](pacific-nova-spa/README.md) — build, QA, dan cara pakai.
- Yang boleh di-download user: `pacific-nova-spa/index.html` (publik) dan
  `pacific-nova-spa/dashboard.html` (dashboard admin).
- Rantai kerja: `src/*.src.html` → `python3 build.py` → `python3 qa_audit.py` →
  `python3 qa_spec.py` / `python3 qa_dash.py` (butuh Playwright + Chromium).
- Audit struktur file terakhir: [`pacific-nova-spa/QA-STRUCTURE.md`](pacific-nova-spa/QA-STRUCTURE.md).

## Backend (Laravel + MySQL)

- **Instalasi (Windows/Laragon):** [`backend/PANDUAN-LARAGON.md`](backend/PANDUAN-LARAGON.md) — ±20 menit dari nol sampai smoke test hijau.
- **Referensi API:** [`backend/README.md`](backend/README.md) — endpoint, kontrak bentuk, perintah harian.
- Status: backend siap diinstal; dashboard masih memakai `localStorage` sampai
  tahap wiring frontend dikerjakan.
