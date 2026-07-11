"""
VibeAI - Recommendation Ranking
================================

منطق امتیازدهی مشترک برای Movie و Music Recommendation Engine.

Final Score =
    Mood Match × 50
  + Energy Match × 30
  + Activity Match × 20
"""

import random
from typing import Dict, List, Set


MOOD_WEIGHT = 50
ENERGY_WEIGHT = 30
ACTIVITY_WEIGHT = 20


def genre_match_score(item_genres: List[str], target_genres: List[str]) -> float:
    if not target_genres:
        return 0.0

    item_set: Set[str] = {g.strip().lower() for g in item_genres}
    target_set: Set[str] = {g.strip().lower() for g in target_genres}

    if not item_set:
        return 0.0

    overlap = item_set & target_set
    if not overlap:
        return 0.0

    return min(len(overlap) / len(target_set), 1.0)


def energy_match_score(item_energy: str, target_energy: str) -> float:
    levels = ["low", "medium", "high"]

    if item_energy not in levels or target_energy not in levels:
        return 0.5

    item_idx = levels.index(item_energy)
    target_idx = levels.index(target_energy)
    diff = abs(item_idx - target_idx)

    if diff == 0:
        return 1.0
    elif diff == 1:
        return 0.5
    else:
        return 0.0


def activity_match_score(
    item_tags: List[str],
    target_activity: str,
    activity_mapping: Dict[str, List[str]],
) -> float:
    target_tags = activity_mapping.get(target_activity, [])
    if not target_tags:
        return 0.0

    item_set = {t.strip().lower() for t in item_tags}
    target_set = {t.strip().lower() for t in target_tags}

    if item_set & target_set:
        return 1.0

    return 0.0


def calculate_final_score(
    mood_score: float,
    energy_score: float,
    activity_score: float,
) -> float:
    score = (
        (mood_score * MOOD_WEIGHT)
        + (energy_score * ENERGY_WEIGHT)
        + (activity_score * ACTIVITY_WEIGHT)
    )
    return round(score, 2)


def rank_items(items: List[Dict], score_key: str = "final_score") -> List[Dict]:
    return sorted(items, key=lambda x: x.get(score_key, 0), reverse=True)


def weighted_sample(items: List[Dict], score_key: str, n: int) -> List[Dict]:
    """
    نمونه‌برداری تصادفی وزن‌دار از لیست آیتم‌ها بدون جایگزاری.

    آیتم‌های با امتیاز بالاتر احتمال بیشتری برای انتخاب شدن دارند،
    اما آیتم‌های کم‌امتیاز هم شانس دارند — این باعث می‌شه هر بار
    پیشنهادهای متفاوتی ارائه بشه، حتی با ورودی یکسان.

    حداقل وزن: 8.0 — تا هیچ آیتمی کاملاً کنار گذاشته نشه.
    """
    if len(items) <= n:
        result = list(items)
        random.shuffle(result)
        return result

    # وزن هر آیتم = max(امتیاز, حداقل) → آیتم‌های ضعیف هم شانس دارن
    MIN_WEIGHT = 8.0
    weights = [max(float(item.get(score_key, 0)), MIN_WEIGHT) for item in items]

    result: List[Dict] = []
    pool = list(items)
    pool_weights = list(weights)

    for _ in range(n):
        if not pool:
            break

        total = sum(pool_weights)
        r = random.random() * total
        cumulative = 0.0

        for i, w in enumerate(pool_weights):
            cumulative += w
            if r <= cumulative:
                result.append(pool.pop(i))
                pool_weights.pop(i)
                break

    return result
