<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /** Cermin DB.activities — daftar tipe aktivitas + nominal default. */
    public function up(): void
    {
        Schema::create('activities', function (Blueprint $table) {
            $table->id();
            $table->string('slug', 32)->unique();
            $table->string('label', 120);
            $table->unsignedInteger('default_amount');
            $table->string('icon', 32)->default('i-star');
            $table->string('note', 255)->nullable();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('activities');
    }
};
