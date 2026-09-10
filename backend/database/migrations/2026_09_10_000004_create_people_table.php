<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Cermin DB.people. Tier & NAS SENGAJA tidak ada di sini —
     * keduanya selalu dihitung ulang dari nas_entries (NasService).
     */
    public function up(): void
    {
        Schema::create('people', function (Blueprint $table) {
            $table->id();
            $table->string('name', 120);
            $table->string('handle', 40)->nullable();
            $table->string('member_number', 40)->unique();
            $table->string('status', 32)->default('Active')->index();
            $table->date('joined_at')->nullable();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('people');
    }
};
