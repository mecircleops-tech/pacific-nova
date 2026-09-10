<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Cermin DB.nas — SATU sumber angka. Kolom activity berupa slug
     * string (bukan FK) supaya entry yatim tidak meledak, cermin
     * fallback actOf() + kontrak ketahanan S9 dashboard.
     */
    public function up(): void
    {
        Schema::create('nas_entries', function (Blueprint $table) {
            $table->id();
            $table->foreignId('person_id')->constrained('people')->cascadeOnDelete();
            $table->string('activity', 32)->index();
            $table->unsignedInteger('amount');
            $table->date('date')->index();
            $table->string('status', 16)->default('pending')->index();
            $table->text('note')->nullable();
            $table->string('attachment_name', 255)->nullable();
            $table->string('attachment_size', 24)->nullable();
            $table->longText('attachment_data')->nullable();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('nas_entries');
    }
};
