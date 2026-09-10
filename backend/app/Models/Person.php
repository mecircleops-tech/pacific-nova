<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Person extends Model
{
    /** Cermin DB.statuses — satu-satunya daftar status yang sah. */
    public const STATUSES = ['Active', 'New member', 'On hold', 'Alumni'];

    protected $table = 'people';

    protected $fillable = ['name', 'handle', 'member_number', 'status', 'joined_at'];

    protected function casts(): array
    {
        return ['joined_at' => 'date'];
    }

    /** Ledger orang ini. Hapus orang → ledger ikut bersih (FK cascade). */
    public function entries(): HasMany
    {
        return $this->hasMany(NasEntry::class, 'person_id');
    }
}
