<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Tier;
use App\Services\NasService;
use Illuminate\Http\Request;

class TierController extends Controller
{
    /** GET /api/v1/tiers — daftar tier terurut ambang. */
    public function index()
    {
        return response()->json([
            'data' => NasService::tiers()->map(fn ($t) => NasService::tierPayload($t))->values(),
        ]);
    }

    /**
     * PUT /api/v1/tiers — geser ambang tier (cermin Manage Content → About).
     * Tier semua orang ikut berubah seketika karena tier selalu
     * dihitung ulang saat dibaca — tidak ada kolom yang perlu di-migrate.
     */
    public function update(Request $request)
    {
        $validated = $request->validate([
            'tiers' => 'required|array|min:1',
            'tiers.*.id' => 'required|integer|exists:tiers,id',
            'tiers.*.min' => 'required|integer|min:0|max:1000000',
            'tiers.*.note' => 'nullable|string|max:500',
        ]);

        foreach ($validated['tiers'] as $row) {
            Tier::where('id', $row['id'])->update(array_filter([
                'min_nas' => $row['min'],
                'note' => $row['note'] ?? null,
            ], fn ($v) => $v !== null));
        }

        return response()->json([
            'data' => NasService::tiers()->map(fn ($t) => NasService::tierPayload($t))->values(),
        ]);
    }
}
