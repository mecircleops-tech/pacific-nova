<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Activity;
use App\Models\NasEntry;
use App\Services\NasService;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;
use Symfony\Component\HttpFoundation\StreamedResponse;

class NasEntryController extends Controller
{
    /**
     * GET /api/v1/nas?person_id=&status=&q= — cermin #/report.
     * Urut tanggal desc; pencarian mencakup nama/nomor/note/aktivitas.
     */
    public function index(Request $request)
    {
        $request->validate([
            'person_id' => 'nullable|integer|exists:people,id',
            'status' => ['nullable', 'string', Rule::in([NasEntry::STATUS_PENDING, NasEntry::STATUS_VERIFIED])],
            'q' => 'nullable|string|max:80',
        ]);

        $query = NasEntry::with('person')->orderByDesc('date')->orderByDesc('id');
        if ($request->filled('person_id')) {
            $query->where('person_id', $request->integer('person_id'));
        }
        if ($request->filled('status')) {
            $query->where('status', (string) $request->input('status'));
        }
        if ($request->filled('q')) {
            $q = '%'.trim((string) $request->input('q')).'%';
            $query->where(function ($w) use ($q) {
                $w->where('note', 'like', $q)
                    ->orWhere('activity', 'like', $q)
                    ->orWhereHas('person', fn ($p) => $p
                        ->where('name', 'like', $q)
                        ->orWhere('member_number', 'like', $q));
            });
        }

        $entries = $query->get();

        return response()->json([
            'data' => $entries->map(fn ($r) => NasService::entryPayload($r))->values(),
            'kpi' => [
                'verifiedTotal' => (int) NasEntry::where('status', 'verified')->sum('amount'),
                'verifiedCount' => NasEntry::where('status', 'verified')->count(),
                'pendingCount' => NasEntry::where('status', 'pending')->count(),
                'shown' => $entries->count(),
            ],
        ]);
    }

    /**
     * POST /api/v1/nas — catat NAS, SELALU masuk sebagai pending
     * (cermin Create NAS: dua mata — penginput lalu pengesah).
     * Validasi = cermin pesan JS-08: orang wajib, 1–9999, tanggal wajib
     * dan tidak boleh masa depan.
     */
    public function store(Request $request)
    {
        $validated = $request->validate([
            'personId' => 'required|integer|exists:people,id',
            'activity' => ['required', 'string', Rule::in(Activity::pluck('slug')->all())],
            'amount' => 'required|integer|min:1|max:9999',
            'date' => 'required|date|before_or_equal:today',
            'note' => 'nullable|string|max:2000',
            'attachmentName' => 'nullable|string|max:255',
            'attachmentSize' => 'nullable|string|max:24',
            // ±82 ribu karakter base64 ≈ 60 KB — batas pratinjau data-URI
            // (cermin aturan lampiran dashboard; selebihnya metadata saja).
            'attachmentData' => 'nullable|string|max:82000',
        ], [
            'personId.required' => 'Pilih influencer dulu. Daftarnya datang dari Data Influencer.',
            'personId.exists' => 'Influencer tidak dikenal.',
            'amount.min' => 'Nilai NAS harus antara 1 dan 9999.',
            'amount.max' => 'Nilai NAS harus antara 1 dan 9999.',
            'date.required' => 'Tanggal wajib diisi.',
            'date.before_or_equal' => 'Tanggal belum terjadi — pilih hari ini atau sebelumnya.',
        ]);

        $entry = NasEntry::create([
            'person_id' => $validated['personId'],
            'activity' => $validated['activity'],
            'amount' => $validated['amount'],
            'date' => $validated['date'],
            'status' => NasEntry::STATUS_PENDING,
            'note' => $validated['note'] ?? null,
            'attachment_name' => $validated['attachmentName'] ?? null,
            'attachment_size' => $validated['attachmentSize'] ?? null,
            'attachment_data' => $validated['attachmentData'] ?? null,
        ]);

        return response()->json(NasService::entryPayload($entry->fresh()), 201);
    }

    /** POST /api/v1/nas/{entry}/verify — sahkan (✓ di NAS Report). */
    public function verify(NasEntry $entry)
    {
        if ($entry->status !== NasEntry::STATUS_PENDING) {
            return response()->json(['message' => 'Hanya entry pending yang bisa diverifikasi.'], 422);
        }
        $entry->update(['status' => NasEntry::STATUS_VERIFIED]);

        return response()->json(NasService::entryPayload($entry->fresh()));
    }

    /** POST /api/v1/nas/{entry}/undo — kembalikan ke pending. */
    public function undo(NasEntry $entry)
    {
        if ($entry->status !== NasEntry::STATUS_VERIFIED) {
            return response()->json(['message' => 'Hanya entry terverifikasi yang bisa di-undo.'], 422);
        }
        $entry->update(['status' => NasEntry::STATUS_PENDING]);

        return response()->json(NasService::entryPayload($entry->fresh()));
    }

    /** PATCH /api/v1/nas/{entry}/note — simpan catatan. */
    public function updateNote(Request $request, NasEntry $entry)
    {
        $validated = $request->validate(['note' => 'nullable|string|max:2000']);
        $entry->update(['note' => $validated['note'] ?? null]);

        return response()->json(NasService::entryPayload($entry->fresh()));
    }

    /** DELETE /api/v1/nas/{entry} — hapus satu baris ledger. */
    public function destroy(NasEntry $entry)
    {
        $entry->delete();

        return response()->json(['message' => 'Entry NAS dihapus.']);
    }

    /**
     * GET /api/v1/nas/export — CSV dengan 8 kolom persis tombol
     * Export CSV dashboard (Tanggal…Attachment, CRLF, quoted).
     */
    public function export(): StreamedResponse
    {
        $file = 'nas-report-'.now()->format('Y-m-d').'.csv';

        return response()->streamDownload(function () {
            $out = fopen('php://output', 'w');
            $line = fn (array $cols) => fwrite($out, implode(',', array_map(
                fn ($c) => '"'.str_replace('"', '""', (string) $c).'"', $cols
            ))."\r\n");

            $line(['Tanggal', 'Nama', 'Member number', 'Activity type', 'NAS', 'Status', 'Catatan', 'Attachment']);
            NasEntry::with('person')->orderByDesc('date')->orderByDesc('id')
                ->chunk(500, function ($entries) use ($line) {
                    $labels = NasService::activities()->map->label;
                    foreach ($entries as $r) {
                        $line([
                            $r->date->format('Y-m-d'),
                            $r->person?->name ?? '',
                            $r->person?->member_number ?? '',
                            $labels[$r->activity] ?? $r->activity,
                            $r->amount,
                            $r->status,
                            $r->note ?? '',
                            $r->attachment_name ?? '',
                        ]);
                    }
                });
            fclose($out);
        }, $file, ['Content-Type' => 'text/csv; charset=utf-8']);
    }
}
