<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Services\NasService;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;

class LeaderboardController extends Controller
{
    /**
     * GET /api/v1/leaderboard?period=all|30|90 — cermin #/leaderboard
     * (podium + progress menuju tier berikut).
     */
    public function show(Request $request)
    {
        $request->validate([
            'period' => ['nullable', 'string', Rule::in(['all', '30', '90'])],
        ]);

        $period = $request->string('period', 'all')->toString();
        $days = $period === 'all' ? null : (int) $period;

        return response()->json([
            'period' => $period,
            'ranking' => NasService::ranking($days),
        ]);
    }
}
