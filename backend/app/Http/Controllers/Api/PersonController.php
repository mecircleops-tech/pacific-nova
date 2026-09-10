<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Person;
use App\Services\NasService;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;

class PersonController extends Controller
{
    /**
     * GET /api/v1/people?q=&tier=&status= — cermin #/influencers.
     * Tier difilter dari angka terhitung (bukan kolom) — sama seperti
     * dashboard; untuk ratusan baris ini cukup, paginasi adalah
     * langkah scaling pertama bila data membesar.
     */
    public function index(Request $request)
    {
        $request->validate([
            'q' => 'nullable|string|max:80',
            'tier' => 'nullable|string|max:60',
            'status' => ['nullable', 'string', Rule::in(Person::STATUSES)],
        ]);

        $query = Person::orderBy('id');
        if ($request->filled('status')) {
            $query->where('status', (string) $request->input('status'));
        }
        if ($request->filled('q')) {
            $q = '%'.trim((string) $request->input('q')).'%';
            $query->where(function ($w) use ($q) {
                $w->where('name', 'like', $q)
                    ->orWhere('member_number', 'like', $q)
                    ->orWhere('handle', 'like', $q);
            });
        }

        $people = $query->get();
        $tiers = NasService::tiers();
        $verified = NasService::verifiedTotals();
        $pending = NasService::pendingCounts();

        $data = [];
        foreach ($people as $person) {
            $payload = NasService::personPayload(
                $person,
                $verified[$person->id] ?? ['total' => 0, 'rows' => 0],
                $pending[$person->id] ?? 0,
                $tiers
            );
            if ($request->filled('tier') && $payload['tier']['name'] !== (string) $request->input('tier')) {
                continue;
            }
            $data[] = $payload;
        }

        return response()->json([
            'data' => $data,
            'meta' => [
                'count' => count($data),
                // Kaki tabel: total NAS terverifikasi semua orang.
                'totalNas' => array_sum(array_column($data, 'totalNas')),
            ],
        ]);
    }

    /** POST /api/v1/people — tambah influencer (tier & NAS tidak diketik). */
    public function store(Request $request)
    {
        $validated = $request->validate([
            'name' => 'required|string|max:120',
            'memberNo' => 'required|string|max:40|unique:people,member_number',
            'status' => ['required', 'string', Rule::in(Person::STATUSES)],
            'handle' => 'nullable|string|max:40',
            'joined' => 'nullable|date',
        ]);

        $person = Person::create([
            'name' => $validated['name'],
            'member_number' => $validated['memberNo'],
            'status' => $validated['status'],
            'handle' => $validated['handle'] ?? null,
            'joined_at' => $validated['joined'] ?? null,
        ]);

        return response()->json(NasService::personPayload($person->fresh()), 201);
    }

    /** GET /api/v1/people/{person} — profil + riwayat entry. */
    public function show(Person $person)
    {
        $pending = NasService::pendingCounts()[$person->id] ?? 0;

        return response()->json([
            'person' => NasService::personPayload($person, null, $pending),
            'history' => $person->entries()->orderByDesc('date')->orderByDesc('id')
                ->get()->map(fn ($r) => NasService::entryPayload($r))->values(),
        ]);
    }

    /** PUT /api/v1/people/{person} — edit (tier & NAS tetap terhitung). */
    public function update(Request $request, Person $person)
    {
        $validated = $request->validate([
            'name' => 'required|string|max:120',
            'memberNo' => ['required', 'string', 'max:40', Rule::unique('people', 'member_number')->ignore($person->id)],
            'status' => ['required', 'string', Rule::in(Person::STATUSES)],
            'handle' => 'nullable|string|max:40',
            'joined' => 'nullable|date',
        ]);

        $person->update([
            'name' => $validated['name'],
            'member_number' => $validated['memberNo'],
            'status' => $validated['status'],
            'handle' => $validated['handle'] ?? null,
            'joined_at' => $validated['joined'] ?? null,
        ]);

        $pending = NasService::pendingCounts()[$person->id] ?? 0;

        return response()->json(NasService::personPayload($person->fresh(), null, $pending));
    }

    /**
     * DELETE /api/v1/people/{person} — hapus orang + seluruh ledger-nya
     * (FK cascade), cermin tombol hapus dashboard.
     */
    public function destroy(Person $person)
    {
        $entries = $person->entries()->count();
        $person->delete();

        return response()->json([
            'message' => 'Influencer dihapus.',
            'deletedEntries' => $entries,
        ]);
    }
}
