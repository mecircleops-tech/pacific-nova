<?php

use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\ContentController;
use App\Http\Controllers\Api\ExportController;
use App\Http\Controllers\Api\LeaderboardController;
use App\Http\Controllers\Api\MetaController;
use App\Http\Controllers\Api\NasEntryController;
use App\Http\Controllers\Api\OverviewController;
use App\Http\Controllers\Api\PersonController;
use App\Http\Controllers\Api\TierController;
use Illuminate\Support\Facades\Route;

/*
 * Pacific Nova API v1.
 * Kontrak bentuk: payload mengikuti key localStorage dashboard (camelCase:
 * memberNo, personId, …) supaya wiring frontend kelak tanpa mapping.
 * Kecuali login/logout, semua endpoint butuh header:
 *   Authorization: Bearer <token>
 */

Route::prefix('v1')->group(function () {
    // --- Publik: login + konten landing page -------------------------------
    Route::post('auth/login', [AuthController::class, 'login']);
    Route::get('public/faq', [ContentController::class, 'publicFaq']);
    Route::get('public/about', [ContentController::class, 'publicAbout']);

    // --- Admin --------------------------------------------------------------
    Route::middleware('auth:sanctum')->group(function () {
        Route::post('auth/logout', [AuthController::class, 'logout']);
        Route::get('auth/me', [AuthController::class, 'me']);

        Route::get('meta', [MetaController::class, 'show']);
        Route::get('overview', [OverviewController::class, 'show']);
        Route::get('export', ExportController::class);

        Route::get('people', [PersonController::class, 'index']);
        Route::post('people', [PersonController::class, 'store']);
        Route::get('people/{person}', [PersonController::class, 'show']);
        Route::put('people/{person}', [PersonController::class, 'update']);
        Route::delete('people/{person}', [PersonController::class, 'destroy']);

        // /nas/export didefinisikan SEBELUM /nas/{entry} agar tidak
        // ditangkap sebagai {entry} = "export".
        Route::get('nas/export', [NasEntryController::class, 'export']);
        Route::get('nas', [NasEntryController::class, 'index']);
        Route::post('nas', [NasEntryController::class, 'store']);
        Route::post('nas/{entry}/verify', [NasEntryController::class, 'verify']);
        Route::post('nas/{entry}/undo', [NasEntryController::class, 'undo']);
        Route::patch('nas/{entry}/note', [NasEntryController::class, 'updateNote']);
        Route::delete('nas/{entry}', [NasEntryController::class, 'destroy']);

        Route::get('leaderboard', [LeaderboardController::class, 'show']);

        Route::get('tiers', [TierController::class, 'index']);
        Route::put('tiers', [TierController::class, 'update']);

        Route::get('content/faq', [ContentController::class, 'faq']);
        Route::put('content/faq', [ContentController::class, 'updateFaq']);
        Route::get('content/about', [ContentController::class, 'about']);
        Route::put('content/about', [ContentController::class, 'updateAbout']);
        Route::get('content/contact', [ContentController::class, 'contact']);
        Route::put('content/contact', [ContentController::class, 'updateContact']);
        Route::get('content/benefits', [ContentController::class, 'benefits']);
        Route::put('content/benefits', [ContentController::class, 'updateBenefits']);
    });
});
