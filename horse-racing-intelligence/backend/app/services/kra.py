from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.models.schemas import HorseEntry

ENTRY_SHEET_PATH = "API26_2/entrySheet_2"
RESULT_DETAIL_PATH = "API156/raceRsutDtl"


def _first(row: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return default


def _as_int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return default
    try:
        return int(float(str(value).replace(",", "")))
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return default


def extract_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    node: Any = payload
    if isinstance(node, dict) and "response" in node:
        node = node["response"]
    if isinstance(node, dict) and "body" in node:
        node = node["body"]
    if isinstance(node, dict) and "items" in node:
        node = node["items"]
    if isinstance(node, dict) and "item" in node:
        node = node["item"]
    if node in (None, ""):
        return []
    if isinstance(node, list):
        return [x for x in node if isinstance(x, dict)]
    if isinstance(node, dict):
        return [node]
    return []


def normalize_entry(row: dict[str, Any]) -> HorseEntry:
    meet = str(_first(row, "meet", "meetName", "meetNm", default="UNKNOWN"))
    race_date = str(_first(row, "rcDate", "rc_date", "raceDate", default=""))
    race_no = _as_int(_first(row, "rcNo", "rc_no", "raceNo"))
    horse_id = str(_first(row, "hrNo", "hr_no", "horseNo", default=""))
    horse_name = str(_first(row, "hrName", "hr_name", "horseName", default=horse_id or "UNKNOWN"))
    draw = _as_int(_first(row, "chulNo", "chul_no", "gateNo", "draw"))
    race_id = f"{meet}-{race_date}-{race_no:02d}"
    return HorseEntry(
        race_id=race_id,
        track=meet,
        race_date=race_date,
        race_no=race_no,
        distance_m=_as_int(_first(row, "rcDist", "rc_dist", "distance")),
        draw=draw,
        horse_id=horse_id or f"{race_id}-DRAW-{draw}",
        horse_name=horse_name,
        jockey_id=str(_first(row, "jkNo", "jk_no", default="")),
        jockey_name=str(_first(row, "jkName", "jk_name", default="")),
        trainer_id=str(_first(row, "trNo", "tr_no", default="")),
        trainer_name=str(_first(row, "trName", "tr_name", default="")),
        owner_id=str(_first(row, "owNo", "ow_no", default="")),
        owner_name=str(_first(row, "owName", "ow_name", default="")),
        rating=_as_float(_first(row, "rating", "ratingValue")),
        carried_weight=_as_float(_first(row, "wgBudam", "wg_budam", "burdenWeight")),
        career_starts=_as_int(_first(row, "rcCntT", "rc_cnt_t", "careerStarts")),
        career_wins=_as_int(_first(row, "ord1CntT", "ord1_cnt_t", "careerWins")),
        career_seconds=_as_int(_first(row, "ord2CntT", "ord2_cnt_t", "careerSeconds")),
        career_thirds=_as_int(_first(row, "ord3CntT", "ord3_cnt_t", "careerThirds")),
        recent_year_starts=_as_int(_first(row, "rcCntY", "rc_cnt_y", "recentYearStarts")),
        recent_year_wins=_as_int(_first(row, "ord1CntY", "ord1_cnt_y", "recentYearWins")),
        recent_year_seconds=_as_int(_first(row, "ord2CntY", "ord2_cnt_y", "recentYearSeconds")),
        recent_year_thirds=_as_int(_first(row, "ord3CntY", "ord3_cnt_y", "recentYearThirds")),
        career_earnings=_as_float(_first(row, "chaksunT", "chaksun_t", "careerEarnings")),
        recent_year_earnings=_as_float(_first(row, "chaksunY", "chaksun_y", "recentYearEarnings")),
        recent_6m_earnings=_as_float(_first(row, "chaksun6m", "chaksun_6m", "recent6mEarnings")),
        raw=row,
    )


class KRAClient:
    """HTTP adapter for KRA Open APIs on data.go.kr."""

    def __init__(self):
        self.base_url = settings.kra_api_base_url.rstrip("/")
        self.service_key = settings.kra_service_key.strip()

    @property
    def configured(self) -> bool:
        return bool(self.service_key)

    async def get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.configured:
            raise RuntimeError("KRA_SERVICE_KEY is not configured")
        query = dict(params or {})
        query["serviceKey"] = self.service_key
        query.setdefault("_type", "json")
        query.setdefault("pageNo", 1)
        query.setdefault("numOfRows", 100)
        timeout = httpx.Timeout(20.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(f"{self.base_url}/{path.lstrip('/')}", params=query)
            response.raise_for_status()
            try:
                payload = response.json()
            except ValueError as exc:
                raise RuntimeError("KRA API returned non-JSON; check service key/API approval") from exc
        self._raise_api_error(payload)
        return payload

    @staticmethod
    def _raise_api_error(payload: dict[str, Any]) -> None:
        response = payload.get("response", payload) if isinstance(payload, dict) else {}
        header = response.get("header", {}) if isinstance(response, dict) else {}
        code = str(header.get("resultCode", header.get("result_code", "")))
        message = header.get("resultMsg", header.get("result_msg", ""))
        if code and code not in {"00", "0", "0000"}:
            raise RuntimeError(f"KRA API error {code}: {message}")

    async def fetch_entry_sheet(self, meet: int = 1, rc_date: str | None = None, rc_no: int | None = None, num_rows: int = 100) -> list[HorseEntry]:
        params: dict[str, Any] = {"meet": meet, "numOfRows": num_rows}
        if rc_date:
            params["rc_date"] = rc_date.replace("-", "")
        if rc_no is not None:
            params["rc_no"] = rc_no
        payload = await self.get_json(ENTRY_SHEET_PATH, params)
        entries = [normalize_entry(row) for row in extract_items(payload)]
        if rc_date:
            target = rc_date.replace("-", "")
            entries = [e for e in entries if not e.race_date or e.race_date.replace("-", "") == target]
        if rc_no is not None:
            entries = [e for e in entries if e.race_no == rc_no]
        return entries

    async def fetch_result_detail(self, meet: int | None = None, rc_date: str | None = None, rc_no: int | None = None, num_rows: int = 100) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"numOfRows": num_rows}
        if meet is not None:
            params["meet"] = meet
        if rc_date:
            params["rc_date"] = rc_date.replace("-", "")
        if rc_no is not None:
            params["rc_no"] = rc_no
        payload = await self.get_json(RESULT_DETAIL_PATH, params)
        return extract_items(payload)
