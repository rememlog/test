from fastapi import APIRouter, HTTPException
from app.models.schemas import HorseGraph, RaceRanking
from app.services.demo import horse_graph, ranking
from app.services.graph import GraphService

router = APIRouter(prefix="/api")


@router.get("/races/demo", response_model=RaceRanking)
def demo_race():
    return ranking()


@router.get("/races/{race_id}/ranking", response_model=RaceRanking)
def race_ranking(race_id: str):
    if race_id != "SEOUL-20260822-07":
        raise HTTPException(status_code=404, detail="MVP currently contains the demo race only")
    return ranking()


@router.get("/horses/{horse_id}/graph", response_model=HorseGraph)
def graph(horse_id: str):
    return horse_graph(horse_id)


@router.post("/demo/seed")
def seed_demo():
    service = GraphService()
    try:
        seeded = service.seed_demo()
        return {"ok": True, "seeded": seeded}
    finally:
        service.close()
