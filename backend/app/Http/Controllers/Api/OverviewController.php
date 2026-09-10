<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Services\NasService;

class OverviewController extends Controller
{
    /**
     * GET /api/v1/overview — satu layar #/overview:
     * 4 KPI + bagan 6 bulan + antrean + top 5 + 5 aktivitas terbaru.
     * Semua angka dihitung server-side dari ledger (cermin renderOverview()).
     */
    public function show()
    {
        return response()->json(NasService::overview());
    }
}
