<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /** About, Contact, Benefit — lihat App\Models\ContentItem. */
    public function up(): void
    {
        Schema::create('content_items', function (Blueprint $table) {
            $table->id();
            $table->string('group', 32)->index();
            $table->unsignedBigInteger('ref_id')->nullable()->index();
            $table->string('label', 191)->nullable();
            $table->text('value')->nullable();
            $table->string('meta', 191)->nullable();
            $table->string('icon', 32)->nullable();
            $table->integer('sort_order')->default(0);
            $table->timestamps();
            $table->index(['group', 'sort_order']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('content_items');
    }
};
