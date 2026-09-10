<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Tier extends Model
{
    protected $fillable = ['name', 'min_nas', 'color', 'note', 'sort_order'];

    protected function casts(): array
    {
        return ['min_nas' => 'integer', 'sort_order' => 'integer'];
    }

    /** Benefit per tier (disimpan sebagai content_items group=benefit). */
    public function benefits(): HasMany
    {
        return $this->hasMany(ContentItem::class, 'ref_id')
            ->where('group', 'benefit')
            ->orderBy('sort_order');
    }
}
