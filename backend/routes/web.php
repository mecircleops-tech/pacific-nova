<?php

use Illuminate\Support\Facades\Route;

// Backend ini API-only: web hanya menjawab status + penunjuk dokumen.
Route::get('/', function () {
    return response()->json([
        'app' => config('app.name'),
        'api' => '/api/v1/meta',
        'health' => '/up',
        'docs' => 'Lihat backend/README.md untuk referensi API.',
    ]);
});
