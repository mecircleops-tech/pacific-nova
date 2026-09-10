<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Person;
use App\Services\NasService;

class MetaController extends Controller
{
    /**
     * GET /api/v1/meta — referensi untuk semua select di form:
     * tiers (ambang+warna), statuses, activities (label+nominal+ikon).
     */
    public function show()
    {
        return response()->json([
            'tiers' => NasService::tiers()->map(fn ($t) => NasService::tierPayload($t))->values(),
            'statuses' => Person::STATUSES,
            'activities' => NasService::activities()->values()
                ->map(fn ($a) => NasService::activityPayload($a))->values(),
        ]);
    }
}
