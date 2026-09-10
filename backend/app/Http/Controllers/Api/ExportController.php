<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Services\NasService;

class ExportController extends Controller
{
    /**
     * GET /api/v1/export — seluruh DB dalam SATU bentuk localStorage
     * dashboard {v, tiers, statuses, activities, people, nas, content}.
     * Dipakai untuk hidrasi awal + tombol Export JSON.
     */
    public function __invoke()
    {
        return response()->json(NasService::exportAll());
    }
}
