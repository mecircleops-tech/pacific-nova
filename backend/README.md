# Pacific Nova — Backend API (Laravel + MySQL)

Pengganti `localStorage` dashboard (`pn.admin.db.v2`) — satu sumber angka yang
sesungguhnya, di MySQL. Frontend (`pacific-nova-spa/`) belum di-wiring ke API
ini (masih localStorage); wiring adalah tahap berikutnya. Panduan instalasi
lengkap: **[PANDUAN-LARAGON.md](PANDUAN-LARAGON.md)**.

| | |
|---|---|
| Framework | Laravel 11 · PHP ≥ 8.2 · MySQL 5.7+/8.x (via Laragon) |
| Auth | Laravel Sanctum, token Bearer |
| Base URL dev | `http://127.0.0.1:8000/api/v1` (`php artisan serve`) |
| Base URL vhost | `http://pacific-nova.test/api/v1` (Apache Laragon, opsional) |
| Seeder demo | `admin` / `pacificnova` — **wajib diganti di produksi** |

## Keputusan desain (kontrak yang jangan dilepas)

1. **Payload = bentuk localStorage dashboard.** Key memakai camelCase
   (`memberNo`, `personId`, `totalNas`, …) persis `DB` di `[JS-06]` — bukan
   snake_case Laravel. Tujuannya satu: wiring frontend kelak tinggal
   `load() → fetch`, tanpa mapping. Pengecualian satu-satunya adalah input
   `PUT /tiers` (`min`, dokumentasi di bawah).
2. **Angka tidak pernah disimpan.** Tier, total NAS, progress, dan peringkat
   selalu dihitung ulang dari `nas_entries` oleh `App\Services\NasService`
   (cermin `[JS-05]`). Menggeser ambang tier langsung mengubah semua tier —
   tanpa kolom yang perlu di-migrate.
3. **Hanya `verified` yang dihitung.** `pending` tidak pernah masuk total,
   bagan, atau leaderboard — kecuali KPI antrean (cermin `nasOf()`).
4. **Kolom `activity` adalah slug string, bukan FK.** Entry yatim (aktivitas
   dihapus) tetap tampil dengan fallback label — cermin `actOf()` + kontrak
   ketahanan S9. Sebaliknya `person_id` adalah FK cascade: hapus orang →
   ledger-nya ikut bersih (cermin tombol hapus dashboard).
5. **Create NAS selalu `pending`.** Pengesahan hanya lewat `POST /nas/{id}/verify`
   (dua mata: penginput → pengesah).
6. **Simpan konten = bulk replace.** `PUT /content/*` mengganti SELURUH blok
   dalam satu transaksi — cermin UX Manage Content (draf → Simpan).
7. **Tanpa paginasi di v1.** Koleksi dikembalikan utuh seperti array
   localStorage. Paginasi (`?page&per_page`) adalah langkah scaling pertama
   bila data membesar.

## Struktur

```
backend/
├── app/
│   ├── Http/Controllers/Api/   Auth, Meta, Overview, Person, NasEntry,
│   │                           Leaderboard, Tier, Content, Export
│   ├── Models/                 User, Person, NasEntry, Activity, Tier,
│   │                           Faq, ContentItem
│   └── Services/NasService.php SATU sumber angka (tier/total/ranking/overview/export)
├── bootstrap/app.php           wiring aplikasi (routing + CORS)
├── config/cors.php             CORS dev-permisif (ketatkan di produksi!)
├── database/
│   ├── migrations/             users, tiers, activities, people,
│   │                           nas_entries, faqs, content_items
│   └── seeders/DemoSeeder.php  port 1:1 function seed() [JS-06]
├── routes/api.php              seluruh endpoint v1
└── PANDUAN-LARAGON.md          instalasi step-by-step (Windows)
```

## Mulai cepat (ringkas — detail di PANDUAN-LARAGON.md)

```bash
cd backend
composer install
copy .env.example .env            # Windows; Linux/macOS: cp
php artisan key:generate
# buat database MySQL `pacific_nova` (HeidiSQL Laragon), lalu:
php artisan migrate --seed
php artisan serve                 # http://127.0.0.1:8000
```

## Referensi API

Header untuk semua endpoint kecuali login & `public/*`:

```
Authorization: Bearer <token>
Accept: application/json
```

| Method & Path | Fungsi |
|---|---|
| `POST /api/v1/auth/login` | `{username, password}` → `{token, user}` |
| `POST /api/v1/auth/logout` | cabut token sesi ini |
| `GET /api/v1/auth/me` | profil pemilik token |
| `GET /api/v1/meta` | `{tiers, statuses, activities}` untuk semua select |
| `GET /api/v1/overview` | 4 KPI + bagan 6 bulan + antrean + top 5 + terbaru |
| `GET /api/v1/export` | seluruh DB bentuk localStorage `{v, tiers, …, content}` |
| `GET /api/v1/people?q=&tier=&status=` | tabel influencer + `totalNas` + `tier` + footer |
| `POST /api/v1/people` | tambah (`name, memberNo, status, handle?, joined?`) |
| `GET /api/v1/people/{id}` | profil + `history` |
| `PUT /api/v1/people/{id}` | edit |
| `DELETE /api/v1/people/{id}` | hapus + ledger ikut bersih |
| `GET /api/v1/nas?person_id=&status=&q=` | report + `kpi`, urut tanggal desc |
| `POST /api/v1/nas` | catat → selalu `pending` (1–9999, ≤ hari ini) |
| `POST /api/v1/nas/{id}/verify` | sahkan pending → verified |
| `POST /api/v1/nas/{id}/undo` | kembalikan verified → pending |
| `PATCH /api/v1/nas/{id}/note` | simpan catatan |
| `DELETE /api/v1/nas/{id}` | hapus baris |
| `GET /api/v1/nas/export` | CSV 8 kolom (sebagai unduhan) |
| `GET /api/v1/leaderboard?period=all\|30\|90` | peringkat + progress tier |
| `GET /api/v1/tiers` | daftar tier |
| `PUT /api/v1/tiers` | `{tiers:[{id, min, note?}]}` geser ambang |
| `GET /api/v1/content/faq` | daftar FAQ |
| `PUT /api/v1/content/faq` | `{items:[{cat, q, a}]}` bulk |
| `GET /api/v1/content/about` | `{lede, stats, steps, note}` |
| `PUT /api/v1/content/about` | bulk |
| `GET /api/v1/content/contact` | 6 field kontak |
| `PUT /api/v1/content/contact` | bulk |
| `GET /api/v1/content/benefits?tier_id=` | benefit satu tier |
| `PUT /api/v1/content/benefits` | `{tier_id, items:[{icon, label, meta}]}` bulk |
| `GET /api/v1/public/faq` | FAQ untuk landing (tanpa auth) |
| `GET /api/v1/public/about` | About+Contact+Tiers+Benefits untuk landing (tanpa auth) |

### Contoh

```bash
# 1. login → simpan token
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"pacificnova"}'
# → {"token_type":"Bearer","token":"1|...","user":{...}}

TOKEN=1|...   # ganti dengan token di atas (Git Bash); di CMD: set TOKEN=...

# 2. tabel influencer (kontrak: Joshua · 0983 · 100 · Blue Nova)
curl -s "http://127.0.0.1:8000/api/v1/people?q=0983" -H "Authorization: Bearer $TOKEN"

# 3. catat NAS (selalu pending) lalu sahkan
curl -s -X POST http://127.0.0.1:8000/api/v1/nas \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"personId":1,"activity":"event","amount":50,"date":"2026-09-10"}'
curl -s -X POST http://127.0.0.1:8000/api/v1/nas/157/verify -H "Authorization: Bearer $TOKEN"

# 4. leaderboard 30 hari + overview
curl -s "http://127.0.0.1:8000/api/v1/leaderboard?period=30" -H "Authorization: Bearer $TOKEN"
curl -s http://127.0.0.1:8000/api/v1/overview -H "Authorization: Bearer $TOKEN"
```

### Error

Validasi gagal → `422` + pesan Bahasa Indonesia (cermin string dashboard,
mis. `Nilai NAS harus antara 1 dan 9999.`). Token salah/kadaluarsa → `401`
`Unauthenticated`. Transisi status ilegal (verifikasi yang bukan pending) →
`422` + penjelasan.

## Perintah harian

```bash
php artisan migrate --seed        # instal / tambah migrasi baru
php artisan migrate:fresh --seed  # RESET total ke data demo (= tombol Reset demo)
php artisan route:list --path=api # daftar endpoint terdaftar
php artisan tinker                # cek cepat: App\Models\Person::count()
```

Ganti password admin demo:

```bash
php artisan tinker --execute="App\Models\User::where('username','admin')->first()->update(['password' => 'ganti-ini']);"
```

## Checklist produksi (jangan lewatkan)

- `APP_ENV=production`, `APP_DEBUG=false`, `APP_URL` domain asli.
- Ganti password `admin` + pertimbangkan 2+ akun (role tunggal = risiko
  terbuka J.2 di QA-REPORT).
- `config/cors.php`: `allowed_origins` = domain pasti (bukan `*`).
- Kredensial DB bukan `root`/kosong; user MySQL khusus dengan hak minimal.
- `php artisan config:cache && php artisan route:cache` setelah deploy.
- Backup terjadwal `mysqldump pacific_nova`.

## Batasan v1 (dinyatakan terbuka)

1. Tanpa paginasi & tanpa rate-limit kustom (bawaan throttle api Laravel aktif).
2. Lampiran = metadata + data-URI ≤ ±60 KB (cermin dashboard); file besar
   butuh object storage (`attachment_data` siap diganti URL).
3. Role tunggal `admin` (cermin dashboard).
4. Test otomatis belum ada — smoke test = skrip curl di PANDUAN-LARAGON.md.
