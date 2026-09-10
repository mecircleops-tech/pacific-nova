<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class ContentItem extends Model
{
    /**
     * Satu tabel fleksibel untuk konten Manage Content:
     *  - group=about_meta   label=lede|note        value=teks
     *  - group=about_stat   label=L  value=V       (statistik {v,l})
     *  - group=about_step   label=T  value=D  icon (langkah {icon,t,d})
     *  - group=contact      label=nama field       value=teks (6 field)
     *  - group=benefit      ref_id=tier_id  label  meta  icon
     */
    public const GROUP_ABOUT_META = 'about_meta';

    public const GROUP_ABOUT_STAT = 'about_stat';

    public const GROUP_ABOUT_STEP = 'about_step';

    public const GROUP_CONTACT = 'contact';

    public const GROUP_BENEFIT = 'benefit';

    protected $fillable = ['group', 'ref_id', 'label', 'value', 'meta', 'icon', 'sort_order'];

    protected function casts(): array
    {
        return ['ref_id' => 'integer', 'sort_order' => 'integer'];
    }

    public function tier(): BelongsTo
    {
        return $this->belongsTo(Tier::class, 'ref_id');
    }
}
