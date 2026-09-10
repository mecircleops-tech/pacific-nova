<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Activity extends Model
{
    protected $fillable = ['slug', 'label', 'default_amount', 'icon', 'note'];

    protected function casts(): array
    {
        return ['default_amount' => 'integer'];
    }
}
