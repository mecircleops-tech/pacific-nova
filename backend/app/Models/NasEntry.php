<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class NasEntry extends Model
{
    public const STATUS_PENDING = 'pending';

    public const STATUS_VERIFIED = 'verified';

    protected $fillable = [
        'person_id',
        'activity',
        'amount',
        'date',
        'status',
        'note',
        'attachment_name',
        'attachment_size',
        'attachment_data',
    ];

    protected $hidden = [
        // Data-URI lampiran hanya untuk pratinjau; tidak ikut payload list.
        'attachment_data',
    ];

    protected function casts(): array
    {
        return ['amount' => 'integer', 'date' => 'date'];
    }

    public function person(): BelongsTo
    {
        return $this->belongsTo(Person::class, 'person_id');
    }
}
