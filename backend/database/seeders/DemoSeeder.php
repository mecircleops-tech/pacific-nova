<?php

namespace Database\Seeders;

use App\Models\Activity;
use App\Models\ContentItem;
use App\Models\Faq;
use App\Models\NasEntry;
use App\Models\Person;
use App\Models\Tier;
use App\Models\User;
use Carbon\Carbon;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

/**
 * Port 1:1 dari function seed() di [JS-06] dashboard — data demo yang SAMA:
 * 9 influencer · Joshua/0983 total 100 NAS · 3 pending · 7 FAQ · konten About.
 * Dijalankan via: php artisan migrate:fresh --seed
 */
class DemoSeeder extends Seeder
{
    public function run(): void
    {
        // --- admin (kredensial demo — WAJIB diganti di produksi) ------------
        User::create([
            'name' => 'Administrator',
            'username' => 'admin',
            'email' => null,
            'password' => Hash::make('pacificnova'),
        ]);

        // --- tiers -----------------------------------------------------------
        $tiers = [];
        foreach ([
            ['Blue Nova', 0, '#7ea9c6', 'Tier awal, semua benefit dasar jalan.'],
            ['Gold Nova', 600, '#e8c56a', 'Kursi tamu & jendela booking lebih panjang.'],
            ['Platinum Nova', 1500, '#cfd8e3', 'Undangan tertutup dan concierge line.'],
        ] as $i => [$name, $min, $color, $note]) {
            $tiers[$name] = Tier::create([
                'name' => $name, 'min_nas' => $min, 'color' => $color,
                'note' => $note, 'sort_order' => $i + 1,
            ]);
        }

        // --- activities ------------------------------------------------------
        $amounts = [];
        foreach ([
            ['event', 'NAS Event Attending', 50, 'i-ticket', 'per event yang dihadiri'],
            ['activity', 'Join Nova Activity', 10, 'i-spark', 'per sesi aktivitas'],
            ['privilege', 'Use Exclusive Nova Privilege', 5, 'i-gem', 'per pemakaian privilege'],
            ['campaign', 'Campaign Bonus', 25, 'i-star', 'nilai bisa diubah per entry'],
        ] as [$slug, $label, $amount, $icon, $note]) {
            Activity::create([
                'slug' => $slug, 'label' => $label, 'default_amount' => $amount,
                'icon' => $icon, 'note' => $note,
            ]);
            $amounts[$slug] = $amount;
        }

        // --- people (URUTAN = indeks resep $spec di bawah) -------------------
        $people = [];
        foreach ([
            ['Joshua', '0983', 'Active', '@joshua', '2025-11-02'],
            ['Ayu Larasati', 'NV-2026-005310', 'Active', '@ayulars', '2025-06-18'],
            ['Bagas Prakoso', 'NV-2026-004877', 'Active', '@bagaspk', '2025-08-30'],
            ['Chyntia Ayu', 'NV-2026-005128', 'New member', '@chyntia', '2026-07-11'],
            ['Dimas Rahardjo', 'NV-2026-004901', 'Active', '@dimasrh', '2025-04-09'],
            ['Elly Nata', 'NV-2026-005044', 'On hold', '@ellynata', '2025-09-21'],
            ['Fajar Ramadhan', 'NV-2026-005233', 'Active', '@fajarrmd', '2026-01-05'],
            ['Gita Permata', 'NV-2026-005361', 'New member', '@gitapermata', '2026-08-14'],
            ['Hendra Wijaya', 'NV-2026-004702', 'Alumni', '@hendrawj', '2024-10-27'],
        ] as [$name, $memberNo, $status, $handle, $joined]) {
            $people[] = Person::create([
                'name' => $name, 'member_number' => $memberNo, 'status' => $status,
                'handle' => $handle, 'joined_at' => $joined,
            ]);
        }

        // --- ledger terverifikasi (resep deterministik = JS seed()) ---------
        // Joshua = 50 + 40 + 10 = 100; tanggal mundur dari 2026-09-08 dan
        // tidak pernah duplikat dalam satu orang.
        $spec = [
            ['event,1|activity,4|privilege,2', 6],
            ['event,13|activity,10|privilege,8', 5],
            ['event,9|activity,14|privilege,6', 7],
            ['event,1|activity,2', 4],
            ['event,11|activity,18|privilege,10', 6],
            ['event,3|activity,6|privilege,3', 9],
            ['event,5|activity,9', 8],
            ['activity,3', 3],
            ['event,4|activity,7|privilege,4', 12],
        ];
        foreach ($people as $idx => $person) {
            $day = Carbon::create(2026, 9, 8)->startOfDay();
            $step = $spec[$idx][1];
            foreach (explode('|', $spec[$idx][0]) as $chunk) {
                [$act, $count] = explode(',', $chunk);
                for ($n = 0; $n < (int) $count; $n++) {
                    $day->subDays($step);
                    $date = $day->format('Y-m-d');
                    $hasFile = $act === 'event' && $n % 3 === 0;
                    NasEntry::create([
                        'person_id' => $person->id,
                        'activity' => $act,
                        'amount' => $amounts[$act],
                        'date' => $date,
                        'status' => NasEntry::STATUS_VERIFIED,
                        'note' => null,
                        'attachment_name' => $hasFile
                            ? 'checkin-'.substr($person->handle, 1).'-'.$date.'.jpg' : null,
                        'attachment_size' => $hasFile ? (120 + $n * 37).' KB' : null,
                    ]);
                    $step = 3 + (($n * 7 + $idx * 5) % 6);
                }
            }
        }

        // --- 3 entry menunggu verifikasi -------------------------------------
        foreach ([['0983', 'campaign'], ['NV-2026-005310', 'event'], ['NV-2026-005361', 'activity']] as $i => [$memberNo, $act]) {
            $who = Person::where('member_number', $memberNo)->firstOrFail();
            NasEntry::create([
                'person_id' => $who->id,
                'activity' => $act,
                'amount' => $act === 'event' ? 100 : ($act === 'campaign' ? 40 : 10),
                'date' => Carbon::today()->subDays($i)->format('Y-m-d'),
                'status' => NasEntry::STATUS_PENDING,
                'note' => 'menunggu rekap panitia',
                'attachment_name' => 'bukti-'.$act.'-'.($i + 1).'.pdf',
                'attachment_size' => '8'.($i * 3).' KB',
            ]);
        }

        // --- FAQ (7 — sama seperti DB.content.faq dashboard) ------------------
        foreach ([
            ['nas', 'What exactly is a NAS point?', 'NAS is the unit Pacific Nova measures membership value in. One action, one fixed value — an attended event is +50, a Nova Activity is +10, using an exclusive privilege is +5. Points are not currency and cannot be bought.'],
            ['nas', 'When does my balance update?', 'Attendance is reconciled when the organiser closes the guest list, usually within 24 hours. Your card shows the exact timestamp of the last update.'],
            ['nas', 'Do NAS points expire?', 'No — points you earned never expire. But your tier is calculated on a rolling 12 months.'],
            ['tier', 'How do I move up a tier?', 'Cross the NAS threshold of the next tier within 12 months. The upgrade applies the moment the qualifying entry lands.'],
            ['tier', 'Can I lose my tier?', 'A review runs once a year on your membership anniversary. If you fall short you step down one tier — never more than one.'],
            ['privilege', 'What counts as an exclusive privilege?', 'Partner perks you unlock by tier: lounge access, upgrades, late checkout, and the concierge line.'],
            ['account', 'Where do I find my member number?', 'It is printed on your welcome card and in the passport email subject line.'],
        ] as $i => [$cat, $q, $a]) {
            Faq::create(['category' => $cat, 'question' => $q, 'answer' => $a, 'sort_order' => $i + 1]);
        }

        // --- About -------------------------------------------------------------
        ContentItem::create(['group' => ContentItem::GROUP_ABOUT_META, 'label' => 'lede',
            'value' => 'Pacific Nova is a membership built around moments rather than receipts. We count the things you actually show up for — events, activities, and the privileges you use — and turn them into NAS points that open the next door.']);
        ContentItem::create(['group' => ContentItem::GROUP_ABOUT_META, 'label' => 'note',
            'value' => 'Three moves, one balance. Nothing to redeem manually — NAS lands the moment your attendance is confirmed.']);
        foreach ([
            ['24.180', 'Members'], ['312', 'NAS events / year'],
            ['46', 'Partner venues'], ['1:1', 'NAS to reward value'],
        ] as $i => [$v, $l]) {
            ContentItem::create(['group' => ContentItem::GROUP_ABOUT_STAT, 'label' => $l, 'value' => $v, 'sort_order' => $i + 1]);
        }
        foreach ([
            ['i-ticket', 'Show up', 'Attend a NAS event, join a Nova Activity, or check in at a partner venue. Your member number does the rest.'],
            ['i-spark', 'Earn NAS', 'Each action carries a fixed NAS value — +50 for an event, +10 for an activity, +5 for using a privilege.'],
            ['i-gem', 'Climb & spend', 'Your total sets the tier. Tier perks unlock automatically, and privileges spend back the points you earned.'],
        ] as $i => [$icon, $t, $d]) {
            ContentItem::create(['group' => ContentItem::GROUP_ABOUT_STEP, 'label' => $t, 'value' => $d, 'icon' => $icon, 'sort_order' => $i + 1]);
        }

        // --- Contact (6 field) ---------------------------------------------------
        foreach ([
            'email' => 'members@pacificnova.example',
            'emailNote' => 'Balance questions, missing NAS, tier reviews.',
            'phone' => '+62 21 1500 098',
            'phoneNote' => 'Sen–Sab, 08:00–20:00 WIB.',
            'lounge' => 'SCBD, Jakarta',
            'loungeNote' => 'Walk in with your member number to redeem privileges.',
        ] as $i => $value) {
            ContentItem::create(['group' => ContentItem::GROUP_CONTACT, 'label' => $i, 'value' => $value, 'sort_order' => 0]);
        }
        // sort_order contact = urutan field (diisi ulang berurutan).
        $order = 0;
        foreach (ContentItem::where('group', ContentItem::GROUP_CONTACT)->orderBy('id')->get() as $row) {
            $row->update(['sort_order' => ++$order]);
        }

        // --- Benefit per tier ------------------------------------------------------
        foreach ([
            'Blue Nova' => [
                ['i-ticket', 'Priority event registration', 'Always open'],
                ['i-spark', '2 free Nova Activities', 'Per month'],
                ['i-gem', 'Exclusive partner privileges', 'Unlocked'],
            ],
            'Gold Nova' => [
                ['i-ticket', 'Everything in Blue Nova', 'Inherited'],
                ['i-user', '+1 guest on every event', 'Per booking'],
                ['i-clock', '6-hour early booking window', 'Before public'],
            ],
            'Platinum Nova' => [
                ['i-ticket', 'Everything in Gold Nova', 'Inherited'],
                ['i-phone', 'Concierge line, one ring', '24/7'],
                ['i-star', 'Invitation-only gatherings', 'Quarterly'],
            ],
        ] as $tierName => $items) {
            foreach ($items as $i => [$icon, $label, $meta]) {
                ContentItem::create([
                    'group' => ContentItem::GROUP_BENEFIT,
                    'ref_id' => $tiers[$tierName]->id,
                    'label' => $label, 'meta' => $meta, 'icon' => $icon,
                    'sort_order' => $i + 1,
                ]);
            }
        }
    }
}
