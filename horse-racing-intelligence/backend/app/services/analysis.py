from __future__ import annotations

import math
from datetime import datetime, timezone

from app.models.schemas import HorseEntry, HorseScore, RaceRanking


def _rate(top_count: int, starts: int) -> float:
    return min(1.0, top_count / starts) if starts > 0 else 0.0


def _minmax(value: float, values: list[float]) -> float:
    if not values:
        return 0.0
    lo, hi = min(values), max(values)
    if hi <= lo:
        return 0.5 if hi > 0 else 0.0
    return (value - lo) / (hi - lo)


def analyze_entries(entries: list[HorseEntry], source: str = "kra-entry-sheet") -> RaceRanking:
    if not entries:
        raise ValueError("No race entries to analyze")

    ratings = [e.rating for e in entries]
    earnings = [math.log1p(max(0.0, e.recent_year_earnings or e.career_earnings)) for e in entries]
    raw_scores: list[tuple[HorseEntry, float, dict[str, float], list[str]]] = []

    for entry in entries:
        career_top3 = entry.career_wins + entry.career_seconds + entry.career_thirds
        recent_top3 = entry.recent_year_wins + entry.recent_year_seconds + entry.recent_year_thirds
        career_place = _rate(career_top3, entry.career_starts)
        recent_place = _rate(recent_top3, entry.recent_year_starts)
        career_win = _rate(entry.career_wins, entry.career_starts)
        recent_win = _rate(entry.recent_year_wins, entry.recent_year_starts)
        rating_norm = _minmax(entry.rating, ratings)
        earnings_norm = _minmax(math.log1p(max(0.0, entry.recent_year_earnings or entry.career_earnings)), earnings)

        features = {
            "recent_top3_rate": round(recent_place, 4),
            "career_top3_rate": round(career_place, 4),
            "recent_win_rate": round(recent_win, 4),
            "career_win_rate": round(career_win, 4),
            "rating_norm": round(rating_norm, 4),
            "earnings_norm": round(earnings_norm, 4),
        }
        raw = (
            recent_place * 0.30
            + career_place * 0.20
            + recent_win * 0.15
            + career_win * 0.10
            + rating_norm * 0.15
            + earnings_norm * 0.10
        )
        ranked_reasons = sorted(
            [
                (recent_place, f"최근 1년 3위내 비율 {recent_place * 100:.1f}%"),
                (career_place, f"통산 3위내 비율 {career_place * 100:.1f}%"),
                (recent_win, f"최근 1년 승률 {recent_win * 100:.1f}%"),
                (rating_norm, f"동일 경주 내 레이팅 상대점수 {rating_norm * 100:.0f}"),
                (earnings_norm, f"최근/통산 상금 상대점수 {earnings_norm * 100:.0f}"),
            ],
            key=lambda x: x[0],
            reverse=True,
        )
        raw_scores.append((entry, raw, features, [text for _, text in ranked_reasons[:3]]))

    max_raw = max(score for _, score, _, _ in raw_scores)
    exp_scores = [math.exp((score - max_raw) * 4.0) for _, score, _, _ in raw_scores]
    denom = sum(exp_scores) or 1.0
    horses = []
    for (entry, raw, features, reasons), exp_score in zip(raw_scores, exp_scores):
        horses.append(HorseScore(
            horse_id=entry.horse_id,
            horse_name=entry.horse_name,
            jockey=entry.jockey_name,
            trainer=entry.trainer_name,
            model_probability=round(exp_score / denom, 6),
            market_probability=None,
            value_gap=None,
            score=round(max(0.0, min(100.0, raw * 100)), 1),
            reasons=reasons,
            features=features,
        ))
    horses.sort(key=lambda h: h.model_probability, reverse=True)
    head = entries[0]
    return RaceRanking(
        race_id=head.race_id,
        track=head.track,
        race_date=head.race_date,
        race_no=head.race_no,
        distance_m=head.distance_m,
        source=source,
        fetched_at=datetime.now(timezone.utc),
        horses=horses,
    )
