<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;

class AuthController extends Controller
{
    /**
     * POST /api/v1/auth/login — cermin layar login dashboard
     * (username + password). Token Sanctum tidak kedaluwarsa sendiri,
     * jadi field "remember" tidak relevan dan diabaikan bila dikirim.
     */
    public function login(Request $request)
    {
        $credentials = $request->validate([
            'username' => 'required|string|max:60',
            'password' => 'required|string|max:120',
        ], [
            'username.required' => 'Isi username dan password dulu.',
            'password.required' => 'Isi username dan password dulu.',
        ]);

        if (! Auth::attempt($credentials)) {
            return response()->json([
                'message' => 'Username atau password salah.',
            ], 422);
        }

        /** @var \App\Models\User $user */
        $user = $request->user();
        $token = $user->createToken('dashboard-admin')->plainTextToken;

        return response()->json([
            'token_type' => 'Bearer',
            'token' => $token,
            'user' => [
                'id' => $user->id,
                'name' => $user->name,
                'username' => $user->username,
            ],
        ]);
    }

    /** POST /api/v1/auth/logout — cabut token sesi ini. */
    public function logout(Request $request)
    {
        $request->user()->currentAccessToken()->delete();

        return response()->json(['message' => 'Keluar. Token sesi ini dicabut.']);
    }

    /** GET /api/v1/auth/me — profil admin pemilik token. */
    public function me(Request $request)
    {
        $user = $request->user();

        return response()->json([
            'id' => $user->id,
            'name' => $user->name,
            'username' => $user->username,
        ]);
    }
}
