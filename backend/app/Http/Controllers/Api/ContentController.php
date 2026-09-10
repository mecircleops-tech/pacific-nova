<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\ContentItem;
use App\Models\Faq;
use App\Models\Tier;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class ContentController extends Controller
{
    // -- FAQ ---------------------------------------------------------------

    /** GET /api/v1/content/faq (admin) — daftar FAQ terurut. */
    public function faq()
    {
        return response()->json(['data' => self::faqShape()]);
    }

    /** GET /api/v1/public/faq (publik, untuk landing) — tanpa auth. */
    public function publicFaq()
    {
        return response()->json(['data' => self::faqShape()]);
    }

    /**
     * PUT /api/v1/content/faq — simpan SELURUH daftar sekaligus (bulk).
     * Cermin UX Manage Content: edit = draf, Simpan = ganti semua.
     */
    public function updateFaq(Request $request)
    {
        $validated = $request->validate([
            'items' => 'required|array|min:1|max:100',
            'items.*.cat' => 'required|string|max:32',
            'items.*.q' => 'required|string|max:500',
            'items.*.a' => 'required|string|max:5000',
        ]);

        DB::transaction(function () use ($validated) {
            Faq::query()->delete();
            foreach ($validated['items'] as $i => $item) {
                Faq::create([
                    'category' => $item['cat'],
                    'question' => $item['q'],
                    'answer' => $item['a'],
                    'sort_order' => $i + 1,
                ]);
            }
        });

        return response()->json(['data' => self::faqShape()]);
    }

    // -- About ---------------------------------------------------------------

    /** GET /api/v1/content/about — lede + statistik + langkah + note. */
    public function about()
    {
        return response()->json(self::aboutShape());
    }

    /** GET /api/v1/public/about (publik, untuk landing) — tanpa auth. */
    public function publicAbout()
    {
        return response()->json(array_merge(self::aboutShape(), [
            'contact' => self::contactShape(),
            'tiers' => Tier::orderBy('min_nas')->get()->map(fn ($t) => [
                'name' => $t->name, 'min' => (int) $t->min_nas,
                'color' => $t->color, 'note' => $t->note,
            ])->values(),
            'benefits' => self::benefitsShape(),
        ]));
    }

    /** PUT /api/v1/content/about — simpan blok About sekaligus. */
    public function updateAbout(Request $request)
    {
        $validated = $request->validate([
            'lede' => 'required|string|max:2000',
            'note' => 'nullable|string|max:1000',
            'stats' => 'required|array|min:1|max:12',
            'stats.*.v' => 'required|string|max:40',
            'stats.*.l' => 'required|string|max:80',
            'steps' => 'required|array|min:1|max:12',
            'steps.*.icon' => 'required|string|max:32',
            'steps.*.t' => 'required|string|max:120',
            'steps.*.d' => 'required|string|max:1000',
        ]);

        DB::transaction(function () use ($validated) {
            ContentItem::whereIn('group', [
                ContentItem::GROUP_ABOUT_META,
                ContentItem::GROUP_ABOUT_STAT,
                ContentItem::GROUP_ABOUT_STEP,
            ])->delete();

            ContentItem::create(['group' => ContentItem::GROUP_ABOUT_META, 'label' => 'lede', 'value' => $validated['lede']]);
            ContentItem::create(['group' => ContentItem::GROUP_ABOUT_META, 'label' => 'note', 'value' => $validated['note'] ?? '']);
            foreach ($validated['stats'] as $i => $s) {
                ContentItem::create(['group' => ContentItem::GROUP_ABOUT_STAT, 'label' => $s['l'], 'value' => $s['v'], 'sort_order' => $i + 1]);
            }
            foreach ($validated['steps'] as $i => $s) {
                ContentItem::create(['group' => ContentItem::GROUP_ABOUT_STEP, 'label' => $s['t'], 'value' => $s['d'], 'icon' => $s['icon'], 'sort_order' => $i + 1]);
            }
        });

        return response()->json(self::aboutShape());
    }

    // -- Contact ---------------------------------------------------------------

    /** GET /api/v1/content/contact — 6 field kontak. */
    public function contact()
    {
        return response()->json(self::contactShape());
    }

    /** PUT /api/v1/content/contact — simpan 6 field sekaligus. */
    public function updateContact(Request $request)
    {
        $validated = $request->validate([
            'email' => 'required|string|max:120',
            'emailNote' => 'required|string|max:255',
            'phone' => 'required|string|max:60',
            'phoneNote' => 'required|string|max:255',
            'lounge' => 'required|string|max:120',
            'loungeNote' => 'required|string|max:255',
        ]);

        DB::transaction(function () use ($validated) {
            ContentItem::where('group', ContentItem::GROUP_CONTACT)->delete();
            $i = 0;
            foreach ($validated as $field => $value) {
                ContentItem::create(['group' => ContentItem::GROUP_CONTACT, 'label' => $field, 'value' => $value, 'sort_order' => ++$i]);
            }
        });

        return response()->json(self::contactShape());
    }

    // -- Benefit per tier -------------------------------------------------------

    /** GET /api/v1/content/benefits?tier_id= — benefit satu tier. */
    public function benefits(Request $request)
    {
        $request->validate(['tier_id' => 'required|integer|exists:tiers,id']);

        return response()->json([
            'tier_id' => $request->integer('tier_id'),
            'data' => self::benefitList($request->integer('tier_id')),
        ]);
    }

    /** PUT /api/v1/content/benefits — simpan benefit satu tier sekaligus. */
    public function updateBenefits(Request $request)
    {
        $validated = $request->validate([
            'tier_id' => 'required|integer|exists:tiers,id',
            'items' => 'required|array|min:1|max:20',
            'items.*.icon' => 'required|string|max:32',
            'items.*.label' => 'required|string|max:200',
            'items.*.meta' => 'required|string|max:120',
        ]);

        DB::transaction(function () use ($validated) {
            ContentItem::where('group', ContentItem::GROUP_BENEFIT)
                ->where('ref_id', $validated['tier_id'])->delete();
            foreach ($validated['items'] as $i => $item) {
                ContentItem::create([
                    'group' => ContentItem::GROUP_BENEFIT,
                    'ref_id' => $validated['tier_id'],
                    'label' => $item['label'],
                    'meta' => $item['meta'],
                    'icon' => $item['icon'],
                    'sort_order' => $i + 1,
                ]);
            }
        });

        return response()->json([
            'tier_id' => $validated['tier_id'],
            'data' => self::benefitList($validated['tier_id']),
        ]);
    }

    // -- bentuk kanonik (dipakai endpoint + /export) -----------------------------

    public static function faqShape(): array
    {
        return Faq::orderBy('sort_order')->get()->map(fn ($f) => [
            'cat' => $f->category, 'q' => $f->question, 'a' => $f->answer,
        ])->values()->all();
    }

    public static function aboutShape(): array
    {
        $meta = ContentItem::where('group', ContentItem::GROUP_ABOUT_META)->pluck('value', 'label');

        return [
            'lede' => $meta['lede'] ?? '',
            'stats' => ContentItem::where('group', ContentItem::GROUP_ABOUT_STAT)->orderBy('sort_order')
                ->get()->map(fn ($s) => ['v' => $s->value, 'l' => $s->label])->values(),
            'steps' => ContentItem::where('group', ContentItem::GROUP_ABOUT_STEP)->orderBy('sort_order')
                ->get()->map(fn ($s) => ['icon' => $s->icon, 't' => $s->label, 'd' => $s->value])->values(),
            'note' => $meta['note'] ?? '',
        ];
    }

    public static function contactShape(): array
    {
        $fields = ['email', 'emailNote', 'phone', 'phoneNote', 'lounge', 'loungeNote'];
        $values = ContentItem::where('group', ContentItem::GROUP_CONTACT)->pluck('value', 'label');

        return array_merge(array_fill_keys($fields, ''), $values->only($fields)->all());
    }

    /** Benefit dikelompokkan per NAMA tier — cermin DB.content.benefits. */
    public static function benefitsShape(): array
    {
        $tiers = Tier::orderBy('min_nas')->get()->keyBy('id');
        $out = [];
        foreach ($tiers as $tier) {
            $out[$tier->name] = self::benefitList($tier->id);
        }

        return $out;
    }

    private static function benefitList(int $tierId): array
    {
        return ContentItem::where('group', ContentItem::GROUP_BENEFIT)
            ->where('ref_id', $tierId)->orderBy('sort_order')
            ->get()->map(fn ($b) => [
                'icon' => $b->icon, 'label' => $b->label, 'meta' => $b->meta,
            ])->values()->all();
    }
}
