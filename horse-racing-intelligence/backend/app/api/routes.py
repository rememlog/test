from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import HorseGraph, KRAStatus, RaceRanking, SyncResult
from app.services.analysis import analyze_entries
from app.services.cache import CacheService
from app.services.demo import horse_graph as demo_horse_graph
from app.services.demo import ranking
from app.services.graph import GraphService
from app.services.kra import ENTRY_SHEET_PATH, RESULT_DETAIL_PATH, KRAClient

router = APIRouter(prefix="/api")


@router.get("/races/demo", response_model=RaceRanking)
def demo_race():
    return ranking()


@router.get("/kra/status", response_model=KRAStatus)
def kra_status():
    client = KRAClient()
    return KRAStatus(
        configured=client.configured,
        entry_sheet_endpoint=ENTRY_SHEET_PATH,
        result_endpoint=RESULT_DETAIL_PATH,
    )


def _cache_key(meet: int, rc_date: str | None, rc_no: int | None) -> str:
    return f"kra:entry:{meet}:{rc_date or 'latest'}:{rc_no if rc_no is not None else 'all'}"


@router.get("/kra/races/analysis", response_model=RaceRanking)
async def kra_race_analysis(
    meet: int = Query(1, ge=1, le=4),
    rc_date: str | None = None,
    rc_no: int | None = Query(None, ge=1, le=20),
    force_refresh: bool = False,
):
    client = KRAClient()
    if not client.configured:
        raise HTTPException(status_code=503, detail="KRA_SERVICE_KEY is not configured. Add the decoded data.go.kr key to .env")

    cache = CacheService()
    key = _cache_key(meet, rc_date, rc_no)
    if not force_refresh:
        try:
            cached = cache.get_json(key)
            if cached:
                return RaceRanking.model_validate(cached)
        except Exception:
            pass

    try:
        entries = await client.fetch_entry_sheet(meet=meet, rc_date=rc_date, rc_no=rc_no)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if not entries:
        raise HTTPException(status_code=404, detail="No KRA entry-sheet rows matched the requested race")

    grouped: dict[str, list] = {}
    for entry in entries:
        grouped.setdefault(entry.race_id, []).append(entry)
    selected = max(grouped.values(), key=lambda xs: (xs[0].race_date, xs[0].race_no))
    analysis = analyze_entries(selected)

    try:
        cache.set_json(key, analysis.model_dump(mode="json"), ttl=300)
    except Exception:
        pass

    try:
        graph = GraphService()
        try:
            graph.upsert_entries(selected)
        finally:
            graph.close()
    except Exception:
        pass
    return analysis


@router.post("/kra/sync", response_model=SyncResult)
async def sync_kra_race(
    meet: int = Query(1, ge=1, le=4),
    rc_date: str | None = None,
    rc_no: int | None = Query(None, ge=1, le=20),
):
    client = KRAClient()
    if not client.configured:
        raise HTTPException(status_code=503, detail="KRA_SERVICE_KEY is not configured")
    try:
        entries = await client.fetch_entry_sheet(meet=meet, rc_date=rc_date, rc_no=rc_no)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if not entries:
        raise HTTPException(status_code=404, detail="No KRA entry-sheet rows matched the requested race")

    grouped: dict[str, list] = {}
    for entry in entries:
        grouped.setdefault(entry.race_id, []).append(entry)
    selected = max(grouped.values(), key=lambda xs: (xs[0].race_date, xs[0].race_no))
    analysis = analyze_entries(selected)

    cached = False
    try:
        CacheService().set_json(_cache_key(meet, rc_date, rc_no), analysis.model_dump(mode="json"), ttl=300)
        cached = True
    except Exception:
        pass

    graph = GraphService()
    try:
        count = graph.upsert_entries(selected)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Neo4j sync failed: {exc}") from exc
    finally:
        graph.close()

    return SyncResult(
        race_id=selected[0].race_id,
        entries=len(selected),
        graph_nodes_upserted=count,
        cached=cached,
        source="kra-entry-sheet",
    )


@router.get("/horses/{horse_id}/graph", response_model=HorseGraph)
def graph(horse_id: str):
    try:
        service = GraphService()
        try:
            result = service.horse_graph(horse_id)
        finally:
            service.close()
        if result.nodes:
            return result
    except Exception:
        pass
    return demo_horse_graph(horse_id)


@router.post("/demo/seed")
def seed_demo():
    service = GraphService()
    try:
        seeded = service.seed_demo()
        return {"ok": True, "seeded": seeded}
    finally:
        service.close()
