"""
Spotify Service
=================

اتصال به Spotify Web API با Client Credentials Flow (بدون نیاز به لاگین کاربر)
برای جست‌وجوی یک ترک و گرفتن لینک/پیش‌نمایش/کاور آلبوم آن.

این سرویس هرگز نباید سیستم را Crash کند (بخش 27 مستند) — در صورت نبود
کلیدها، خطای شبکه، یا نبود نتیجه، None برمی‌گرداند تا فراخواننده (music
recommender) بدون این داده هم کار کند.
"""

import os
import time
from typing import Dict, Optional

import requests

from cache import cache


TOKEN_URL = "https://accounts.spotify.com/api/token"
SEARCH_URL = "https://api.spotify.com/v1/search"

CACHE_TTL_HOURS = 24

# توکن دسترسی در حافظه کش می‌شود (نیازی به دیتابیس نیست، اعتبار ~1 ساعت دارد)
_token_cache: Dict[str, float] = {"access_token": "", "expires_at": 0.0}


def _get_access_token() -> Optional[str]:
    """دریافت (یا استفاده از کش) access token با Client Credentials Flow."""
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        return None

    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    try:
        response = requests.post(
            TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return None

    access_token = data.get("access_token")
    if not access_token:
        return None

    # چند ثانیه حاشیه امن قبل از انقضای واقعی
    _token_cache["access_token"] = access_token
    _token_cache["expires_at"] = time.time() + data.get("expires_in", 3600) - 30

    return access_token


def _query_spotify(token: str, query: str, limit: int) -> list:
    response = requests.get(
        SEARCH_URL,
        headers={"Authorization": f"Bearer {token}"},
        params={"q": query, "type": "track", "limit": limit},
        timeout=5,
    )
    response.raise_for_status()
    return response.json().get("tracks", {}).get("items", [])


def search_track(title: str, artist: str) -> Optional[Dict]:
    """
    جست‌وجوی یک ترک در Spotify و بازگرداندن لینک/پیش‌نمایش/کاور آن.

    ابتدا با query دقیق (`track:X artist:Y`) امتحان می‌شود؛ اگر نتیجه‌ای نداشت
    (مثلا به دلیل تفاوت جزئی در عنوان)، یک جست‌وجوی آزاد به عنوان fallback
    انجام می‌شود، اما فقط در صورتی پذیرفته می‌شود که نام هنرمند در نتیجه با
    هنرمند درخواستی همخوانی داشته باشد (برای جلوگیری از برگرداندن کاور/ترک اشتباه).

    خروجی نمونه:
    {"spotify_url": "...", "preview_url": "..." | None, "album_image": "..." | None}

    در صورت هر گونه خطا یا نبود نتیجه‌ی مطمئن، None برمی‌گردد.
    """
    cache_key = cache.build_cache_key("spotify_track", title.strip().lower(), artist.strip().lower())
    cached = cache.get_cached(cache_key)
    if cached is not None:
        return cached or None

    token = _get_access_token()
    if not token:
        return None

    artist_lower = artist.strip().lower()

    try:
        items = _query_spotify(token, f"track:{title} artist:{artist}", limit=1)

        if not items:
            # fallback: جست‌وجوی آزاد + تایید نام هنرمند برای جلوگیری از تطبیق اشتباه
            candidates = _query_spotify(token, f"{title} {artist}", limit=5)
            items = [
                c for c in candidates
                if any(artist_lower in a.get("name", "").lower() for a in c.get("artists", []))
            ][:1]
    except (requests.RequestException, ValueError):
        return None

    if not items:
        # نتیجه‌ی خالی هم کش می‌شود تا دوباره درخواست تکراری نزنیم
        cache.set_cached(cache_key, {}, ttl_hours=CACHE_TTL_HOURS)
        return None

    track = items[0]
    images = track.get("album", {}).get("images", [])

    result = {
        "spotify_url": track.get("external_urls", {}).get("spotify"),
        "preview_url": track.get("preview_url"),
        "album_image": images[0]["url"] if images else None,
    }

    cache.set_cached(cache_key, result, ttl_hours=CACHE_TTL_HOURS)
    return result
