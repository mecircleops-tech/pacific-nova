<?php

return [

    /*
     * CORS dev-permisif: dashboard dibuka dari file:// (Origin: null),
     * :8001, atau :8000 — semuanya harus bisa memanggil API dengan
     * token Bearer. Token Bearer tidak butuh supports_credentials.
     *
     * PRODUKSI: ganti allowed_origins dengan domain pasti, mis.
     * ['https://app.pacificnova.example'].
     */

    'paths' => ['api/*', 'sanctum/csrf-cookie'],

    'allowed_methods' => ['*'],

    'allowed_origins' => ['*'],

    'allowed_origins_patterns' => [],

    'allowed_headers' => ['*'],

    'exposed_headers' => [],

    'max_age' => 0,

    'supports_credentials' => false,

];
