# Panduan Instalasi Backend via Laragon (Windows)

Target: API Pacific Nova jalan di `http://127.0.0.1:8000` dengan database MySQL
`pacific_nova` berisi data demo (9 influencer, 156 entry NAS). Waktu: ±20 menit.

> Ringkasan perintah (detail per langkah di bawah):
>
> ```bat
> cd C:\laragon\www\pacific-nova\backend
> composer install
> copy .env.example .env
> php artisan key:generate
> php artisan migrate --seed
> php artisan serve
> ```

## 0. Prasyarat

- Windows 10/11 64-bit, ±1 GB ruang kosong.
- Hak administrator (untuk instalasi + port 80/3306).
- Repo ini sudah ada di komputer (clone atau copy folder).

## 1. Install Laragon

1. Unduh **Laragon Full** dari <https://laragon.org/download/>.
2. Jalankan installer → Next → Next → Install → Finish. Lokasi default
   `C:\laragon` — biarkan default agar path di panduan ini cocok.
3. Jalankan Laragon → klik tombol **Start**. Lampu Apache + MySQL harus hijau.
   Bila merah, lihat [Troubleshooting](#troubleshooting).

## 2. Pastikan PHP ≥ 8.2 + ekstensi MySQL

1. Laragon → Menu → **PHP → Version** → pilih `php-8.2…` atau lebih baru.
   (Bila hanya ada 8.1: Menu → PHP → Quick add → unduh 8.2/8.3.)
2. Buka **Terminal** (klik kanan Laragon → Terminal), lalu cek:
   ```bat
   php -v
   ```
   Harus tampil `PHP 8.2.x` atau `8.3.x` (CLI).
3. Cek ekstensi wajib:
   ```bat
   php -m | findstr /i "pdo_mysql mbstring openssl tokenizer xml ctype fileinfo curl"
   ```
   Semua harus muncul. Bila ada yang hilang: Menu → PHP → Extensions →
   centang yang kurang → **Restart** Laragon.

## 3. Buat database `pacific_nova`

1. Laragon → Menu → **Database → HeidiSQL** (terinstal bawaan).
2. Session Laragon/MySQL → Open (user `root`, password **kosong**).
3. Klik kanan → **Create new → Database** → nama `pacific_nova` →
   collation `utf8mb4_unicode_ci` → OK.
4. Alternatif via Terminal:
   ```bat
   mysql -u root -e "CREATE DATABASE IF NOT EXISTS pacific_nova CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
   ```

## 4. Taruh project di `www`

Salin/clone repo sehingga strukturnya persis seperti ini:

```
C:\laragon\www\pacific-nova\
├── backend\          ← Laravel (folder ini)
│   ├── .env.example
│   ├── artisan
│   ├── composer.json
│   └── ...
└── pacific-nova-spa\ ← frontend statis (index.html, dashboard.html, …)
```

## 5. Instal dependensi PHP

Di Terminal Laragon:

```bat
cd C:\laragon\www\pacific-nova\backend
composer install
```

Tunggu hingga muncul `Generating optimized autoload files` tanpa error.
(Cek composer: `composer --version` — Laragon sudah membawanya.)

## 6. Konfigurasi `.env`

```bat
copy .env.example .env
php artisan key:generate
```

Buka `backend\.env`, pastikan 5 baris ini (default Laragon — biasanya sudah benar):

```ini
APP_URL=http://127.0.0.1:8000
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=pacific_nova
DB_USERNAME=root
DB_PASSWORD=
```

> `DB_PASSWORD` kosong = default user `root` Laragon. Bila Anda pernah
> mengganti password root MySQL, isi di sini.

## 7. Migrasi + seed data demo

```bat
php artisan migrate --seed
```

Ekspektasi: deretan `DONE` untuk 7 migrasi + `Seeding: Database\Seeders\DemoSeeder`.
Verifikasi isi tabel (HeidiSQL atau tinker):

```bat
php artisan tinker --execute="echo 'users='.App\Models\User::count().PHP_EOL.'tiers='.App\Models\Tier::count().PHP_EOL.'activities='.App\Models\Activity::count().PHP_EOL.'people='.App\Models\Person::count().PHP_EOL.'nas='.App\Models\NasEntry::count().PHP_EOL.'faq='.App\Models\Faq::count().PHP_EOL;"
```

Harus tampil persis:

```
users=1
tiers=3
activities=4
people=9
nas=156
faq=7
```

Reset total ke data demo kapan pun (= tombol Reset demo):

```bat
php artisan migrate:fresh --seed
```

## 8. Jalankan server (jalur utama: `artisan serve`)

```bat
php artisan serve
```

Buka browser: `http://127.0.0.1:8000` → JSON status aplikasi.
Cek kesehatan: `http://127.0.0.1:8000/up` → HTTP 200.

> Biarkan jendela Terminal ini terbuka selama memakai API. Hentikan dengan
> `Ctrl+C`.

### 8b. (Opsional) Virtual host Apache `http://pacific-nova.test`

Untuk URL cantik tanpa `:8000`. Buat file
`C:\laragon\etc\apache2\sites-enabled\pacific-nova.test.conf`
(nama custom — JANGAN diawali `auto.` agar tidak ditimpa Laragon):

```apache
<VirtualHost *:80>
    DocumentRoot "C:/laragon/www/pacific-nova/backend/public"
    ServerName pacific-nova.test
    <Directory "C:/laragon/www/pacific-nova/backend/public">
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
```

Lalu: Laragon → Menu → **Apache → Reload**, dan ubah `.env`:
`APP_URL=http://pacific-nova.test`. Buka `http://pacific-nova.test`.
(Laragon mengelola entri hosts `*.test` otomatis.)

## 9. Smoke test API (wajib — ±3 menit)

Di Terminal **kedua** (Git Bash Laragon; sesuaikan `set TOKEN=` bila pakai CMD):

```bash
cd /c/laragon/www/pacific-nova/backend

# 1) login → salin token dari respons
curl -s -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"pacificnova"}'
# → {"token_type":"Bearer","token":"1|...","user":{"username":"admin",...}}

TOKEN='1|...'   # ← ganti dengan token Anda

# 2) kontrak data (harus: Joshua · 0983 · 100 · Blue Nova)
curl -s "http://127.0.0.1:8000/api/v1/people?q=0983" -H "Authorization: Bearer $TOKEN"

# 3) overview (4 KPI + bagan + antrean + top 5 + terbaru)
curl -s http://127.0.0.1:8000/api/v1/overview -H "Authorization: Bearer $TOKEN"

# 4) leaderboard 30 hari
curl -s "http://127.0.0.1:8000/api/v1/leaderboard?period=30" -H "Authorization: Bearer $TOKEN"

# 5) tulis → sahkan (pending TIDAK dihitung sebelum verify)
curl -s -X POST http://127.0.0.1:8000/api/v1/nas \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"personId":1,"activity":"event","amount":50,"date":"2026-09-10"}'
# → {...,"status":"pending",...} catat "id"-nya, mis. 157
curl -s -X POST http://127.0.0.1:8000/api/v1/nas/157/verify -H "Authorization: Bearer $TOKEN"
# → {...,"status":"verified",...}

# 6) FAQ publik (tanpa token — untuk landing)
curl -s http://127.0.0.1:8000/api/v1/public/faq
```

Semua harus HTTP 200/201. Bila ada yang gagal → [Troubleshooting](#troubleshooting).

## 10. Menghubungkan dashboard (tahap berikutnya, belum di panduan ini)

Backend ini sengaja dibentuk 1:1 dengan `localStorage` dashboard sehingga
wiring-nya kecil: `load()` → `GET /api/v1/export`, `save()` → POST/PUT
per endpoint, login → `POST /auth/login` + simpan Bearer token. Wiring
frontend BUKAN bagian panduan ini — dashboard masih memakai localStorage
sampai tahap itu dikerjakan.

---

## Troubleshooting

| Gejala | Penyebab umum → Solusi |
|---|---|
| Laragon Start: MySQL merah | Port 3306 dipakai (MySQL lain/Skype) → Laragon → Menu → Preferences → Services & Ports → ganti port MySQL (lalu sesuaikan `DB_PORT` di `.env`) |
| `SQLSTATE[HY000] [1045] Access denied` | Password root salah → samakan `DB_PASSWORD` dengan password root HeidiSQL |
| `SQLSTATE[HY000] [1049] Unknown database` | DB belum dibuat → ulangi Langkah 3 |
| `could not find driver` | Ekstensi `pdo_mysql` mati → Langkah 2.3 |
| `No application encryption key` | Lupa `key:generate` → Langkah 6 |
| `composer: command not found` | Terminal bukan milik Laragon → buka via klik kanan Laragon → Terminal |
| `POST /api/...` → 404 (hanya di vhost Apache) | `DocumentRoot` tidak ke `backend\public` → perbaiki conf Langkah 8b + Reload Apache |
| `401 Unauthenticated` | Token salah/hilang → login ulang; format header `Bearer <token>` persis |
| `419` / CORS error dari dashboard | Pastikan request ke base URL yang benar + header `Accept: application/json`; Bearer tidak butuh kredensial cookie |
| `PUT /tiers` tidak mengubah tier tabel | Normal bila cache: `php artisan optimize:clear`; tier dihitung saat baca |
| Migrasi macet di tengah | `php artisan migrate:fresh --seed` untuk ulang dari nol (data demo kembali) |

Perintah berguna:

```bat
php artisan route:list --path=api   :: daftar endpoint terdaftar
php artisan optimize:clear          :: bersihkan semua cache
php artisan migrate:fresh --seed    :: reset total ke data demo
```
