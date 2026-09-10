<?php

namespace App\Services;

use App\Http\Controllers\Api\ContentController;
use App\Models\Activity;
use App\Models\ContentItem;
use App\Models\Faq;
use App\Models\NasEntry;
use App\Models\Person;
use App\Models\Tier;
use Carbon\Carbon;
use Illuminate\Support\Collection;

/**
 * Cermin [JS-05] dashboard: kolom NAS, tier, progress, dan peringkat TIDAK
 * disimpan di record orang. Semuanya diturunkan dari ledger lewat service
 * ini — satu sumber angka, tidak ada peluang tabel orang dan daftar entry
 * saling bohong.
 */
class NasService
{
    /** Label bulan singkat Bahasa Indonesia untuk bagan overview. */
    private const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];

    private static ?Collection $activityCache = null;

    /**
     * Total NAS terverifikasi + jumlah baris per orang (satu query).
     * $since = 'YYYY-MM-DD' atau null (semua waktu).
     *
     * @return array<int, array{total:int, rows:int}>
     */
    public static function verifiedTotals(?string $since = null): array
    {
        $query = NasEntry::selectRaw('person_id')
            ->selectRaw("COALESCE(SUM(CASE WHEN status = 'verified' THEN amount ELSE 0 END), 0) AS total")
            ->selectRaw("COALESCE(SUM(CASE WHEN status = 'verified' THEN 1 ELSE 0 END), 0) AS rows")
            ->groupBy('person_id');

        if ($since) {
            $query->where('date', '>=', $since);
        }

        $out = [];
        foreach ($query->get() as $row) {
            $out[(int) $row->person_id] = ['total' => (int) $row->total, 'rows' => (int) $row->rows];
        }

        return $out;
    }

    /**
     * Jumlah entry pending per orang (SELALU semua waktu — cermin
     * pendingOf() yang tidak mengenal $since).
     *
     * @return array<int, int>
     */
    public static function pendingCounts(): array
    {
        return NasEntry::where('status', 'pending')
            ->selectRaw('person_id, COUNT(*) AS c')
            ->groupBy('person_id')
            ->pluck('c', 'person_id')
            ->map(fn ($c) => (int) $c)
            ->all();
    }

    /** Tier tertinggi yang ambangnya terlampaui. Cermin tierOf(). */
    public static function tierFor(int $total, Collection $tiers): Tier
    {
        $out = $tiers->first();
        foreach ($tiers as $tier) {
            if ($total >= (int) $tier->min_nas) {
                $out = $tier;
            }
        }

        return $out;
    }

    /** Tier berikutnya di atas total, atau null bila sudah mentok. Cermin nextTier(). */
    public static function nextTier(int $total, Collection $tiers): ?Tier
    {
        foreach ($tiers as $tier) {
            if ($total < (int) $tier->min_nas) {
                return $tier;
            }
        }

        return null;
    }

    /** Tiers terurut ambang menaik — prasyarat tierFor()/nextTier(). */
    public static function tiers(): Collection
    {
        return Tier::orderBy('min_nas')->orderBy('sort_order')->get();
    }

    /** Peta slug aktivitas → model (untuk label + fallback yatim ala actOf()). */
    public static function activities(): Collection
    {
        // Cache per-request: dipanggil di setiap entryPayload.
        return self::$activityCache ??= Activity::all()->keyBy('slug');
    }

    /**
     * Peringkat: total menurun, nama menaik bila seri. Cermin ranking().
     * $days = null (semua waktu) | 30 | 90.
     */
    public static function ranking(?int $days = null): array
    {
        $since = $days ? Carbon::today()->subDays($days)->format('Y-m-d') : null;
        $tiers = self::tiers();
        $verified = self::verifiedTotals($since);
        $pending = self::pendingCounts();

        $rows = [];
        foreach (Person::orderBy('id')->get() as $person) {
            $agg = $verified[$person->id] ?? ['total' => 0, 'rows' => 0];
            $tier = self::tierFor($agg['total'], $tiers);
            $next = self::nextTier($agg['total'], $tiers);
            $rows[] = [
                'person' => self::personPayload($person, $agg, $pending[$person->id] ?? 0, $tiers),
                'total' => $agg['total'],
                'rows' => $agg['rows'],
                'tier' => self::tierPayload($tier),
                'next' => $next ? self::tierPayload($next) : null,
                'progress' => self::progress($agg['total'], $tier, $next),
            ];
        }

        usort($rows, fn ($a, $b) => $b['total'] <=> $a['total']
            ?: strcmp($a['person']['name'], $b['person']['name']));

        foreach ($rows as $i => &$row) {
            $row['rank'] = $i + 1;
        }

        return $rows;
    }

    /** Persen menuju tier berikut (0–100). */
    public static function progress(int $total, Tier $tier, ?Tier $next): int
    {
        if (! $next || (int) $next->min_nas <= (int) $tier->min_nas) {
            return 100;
        }

        return (int) round(($total - (int) $tier->min_nas)
            / ((int) $next->min_nas - (int) $tier->min_nas) * 100);
    }

    /** Satu layar overview: KPI + bagan + antrean + top 5 + terbaru. Cermin renderOverview(). */
    public static function overview(): array
    {
        $tiers = self::tiers();
        $pending = NasEntry::where('status', 'pending')->with('person')->orderBy('id')->get();
        $monthAgo = Carbon::today()->subDays(30)->format('Y-m-d');
        // Catatan setia: KPI "Aktivitas 30 hari" dan bagan dihitung dari SEMUA
        // entry (termasuk pending), sama seperti dashboard.
        $thisMonth = NasEntry::where('date', '>=', $monthAgo)->get();
        $verifiedSum = (int) NasEntry::where('status', 'verified')->sum('amount');
        $verifiedCount = NasEntry::where('status', 'verified')->count();

        return [
            'kpi' => [
                [
                    't' => 'Influencer terdaftar',
                    'v' => Person::count(),
                    's' => Person::where('status', 'Active')->count().' aktif',
                ],
                [
                    't' => 'Total NAS terverifikasi',
                    'v' => $verifiedSum,
                    's' => $verifiedCount.' entry',
                ],
                [
                    't' => 'Menunggu verifikasi',
                    'v' => $pending->count(),
                    's' => $pending->count() ? 'perlu tindakan' : 'bersih',
                    'hot' => $pending->count() > 0,
                ],
                [
                    't' => 'Aktivitas 30 hari',
                    'v' => $thisMonth->count(),
                    's' => '+'.$thisMonth->sum('amount').' NAS masuk',
                ],
            ],
            'chart' => self::chart6m(),
            'queue' => [
                'total' => $pending->count(),
                'data' => $pending->take(4)->values()->map(fn ($r) => self::entryPayload($r)),
            ],
            'top' => array_slice(self::ranking(), 0, 5),
            'recent' => NasEntry::with('person')->orderByDesc('date')->orderByDesc('id')->limit(5)
                ->get()->map(fn ($r) => self::entryPayload($r))->values(),
        ];
    }

    /** Bagan 6 bulan berjalan (termasuk bulan ini), dari data entry. */
    public static function chart6m(): array
    {
        $buckets = [];
        $start = Carbon::today()->startOfMonth()->subMonths(5);
        for ($i = 0; $i < 6; $i++) {
            $month = $start->copy()->addMonths($i);
            $buckets[] = [
                'key' => $month->format('Y-m'),
                'l' => self::MONTHS[(int) $month->format('n') - 1],
                'v' => 0,
            ];
        }

        $sums = NasEntry::where('date', '>=', $start->format('Y-m-d'))
            ->selectRaw('SUBSTR(date, 1, 7) AS ym, SUM(amount) AS v')
            ->groupBy('ym')
            ->pluck('v', 'ym');

        foreach ($buckets as &$bucket) {
            $bucket['v'] = (int) ($sums[$bucket['key']] ?? 0);
        }

        return ['buckets' => $buckets, 'total' => array_sum(array_column($buckets, 'v'))];
    }

    // -- payload (key camelCase = cermin localStorage dashboard) --------------

    public static function tierPayload(Tier $tier): array
    {
        return [
            'id' => $tier->id,
            'name' => $tier->name,
            'min' => (int) $tier->min_nas,
            'color' => $tier->color,
            'note' => $tier->note,
        ];
    }

    public static function activityPayload(Activity $activity): array
    {
        return [
            'id' => $activity->slug,
            'label' => $activity->label,
            'amount' => (int) $activity->default_amount,
            'icon' => $activity->icon,
            'note' => $activity->note,
        ];
    }

    public static function personPayload(Person $person, ?array $agg = null, int $pending = 0, ?Collection $tiers = null): array
    {
        $agg ??= self::verifiedTotals()[$person->id] ?? ['total' => 0, 'rows' => 0];
        $tiers ??= self::tiers();
        $total = (int) $agg['total'];

        return [
            'id' => $person->id,
            'name' => $person->name,
            'handle' => $person->handle,
            'memberNo' => $person->member_number,
            'status' => $person->status,
            'joined' => $person->joined_at?->format('Y-m-d'),
            'totalNas' => $total,
            'rows' => (int) $agg['rows'],
            'pending' => $pending,
            'tier' => self::tierPayload(self::tierFor($total, $tiers)),
        ];
    }

    public static function entryPayload(NasEntry $entry): array
    {
        $entry->loadMissing('person');
        $activity = self::activities()->get($entry->activity);

        return [
            'id' => $entry->id,
            'personId' => $entry->person_id,
            'person' => $entry->person ? [
                'name' => $entry->person->name,
                'handle' => $entry->person->handle,
                'memberNo' => $entry->person->member_number,
            ] : null,
            'activity' => $entry->activity,
            // Fallback yatim ala actOf(): aktivitas yang dihapus tidak meledak.
            'activityLabel' => $activity?->label ?? $entry->activity,
            'activityIcon' => $activity?->icon ?? 'i-star',
            'amount' => (int) $entry->amount,
            'date' => Carbon::parse($entry->date)->format('Y-m-d'),
            'status' => $entry->status,
            'note' => $entry->note ?? '',
            'attachment' => $entry->attachment_name ? [
                'name' => $entry->attachment_name,
                'size' => $entry->attachment_size,
            ] : null,
        ];
    }

    /**
     * Seluruh DB dalam SATU bentuk localStorage dashboard
     * {v, tiers, statuses, activities, people, nas, content} — untuk
     * endpoint /export (hidrasi + tombol Export JSON).
     */
    public static function exportAll(): array
    {
        $tiers = self::tiers();
        $people = Person::orderBy('id')->get();
        $entries = NasEntry::orderBy('date')->orderBy('id')->get();

        return [
            'v' => 2,
            'tiers' => $tiers->map(fn ($t) => [
                'name' => $t->name, 'min' => (int) $t->min_nas,
                'color' => $t->color, 'note' => $t->note,
            ])->values(),
            'statuses' => Person::STATUSES,
            'activities' => self::activities()->values()->map(fn ($a) => self::activityPayload($a))->values(),
            'people' => $people->map(fn ($p) => [
                'id' => $p->id, 'name' => $p->name, 'memberNo' => $p->member_number,
                'status' => $p->status, 'handle' => $p->handle,
                'joined' => $p->joined_at?->format('Y-m-d'),
            ])->values(),
            'nas' => $entries->map(fn ($r) => [
                'id' => $r->id, 'personId' => $r->person_id, 'activity' => $r->activity,
                'amount' => (int) $r->amount,
                'date' => Carbon::parse($r->date)->format('Y-m-d'),
                'status' => $r->status,
                'attachment' => $r->attachment_name ? [
                    'name' => $r->attachment_name, 'size' => $r->attachment_size,
                ] : null,
                'note' => $r->note ?? '',
            ])->values(),
            'content' => [
                'about' => ContentController::aboutShape(),
                'contact' => ContentController::contactShape(),
                'faq' => Faq::orderBy('sort_order')->get()->map(fn ($f) => [
                    'cat' => $f->category, 'q' => $f->question, 'a' => $f->answer,
                ])->values(),
                'benefits' => ContentController::benefitsShape(),
            ],
        ];
    }
}
