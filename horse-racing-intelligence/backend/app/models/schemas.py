from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HorseEntry(BaseModel):
    race_id: str
    track: str
    race_date: str
    race_no: int
    distance_m: int = 0
    draw: int = 0
    horse_id: str
    horse_name: str
    jockey_id: str = ""
    jockey_name: str = ""
    trainer_id: str = ""
    trainer_name: str = ""
    owner_id: str = ""
    owner_name: str = ""
    rating: float = 0.0
    carried_weight: float = 0.0
    career_starts: int = 0
    career_wins: int = 0
    career_seconds: int = 0
    career_thirds: int = 0
    recent_year_starts: int = 0
    recent_year_wins: int = 0
    recent_year_seconds: int = 0
    recent_year_thirds: int = 0
    career_earnings: float = 0.0
    recent_year_earnings: float = 0.0
    recent_6m_earnings: float = 0.0
    raw: dict[str, Any] = Field(default_factory=dict, exclude=True)


class HorseScore(BaseModel):
    horse_id: str
    horse_name: str
    jockey: str
    trainer: str
    model_probability: float = Field(ge=0, le=1)
    market_probability: float | None = Field(default=None, ge=0, le=1)
    value_gap: float | None = None
    score: float = Field(ge=0, le=100)
    reasons: list[str]
    features: dict[str, float] = Field(default_factory=dict)


class RaceRanking(BaseModel):
    race_id: str
    track: str
    race_date: str = ""
    race_no: int = 0
    distance_m: int
    source: str = "demo"
    fetched_at: datetime | None = None
    horses: list[HorseScore]


class KRAStatus(BaseModel):
    configured: bool
    entry_sheet_endpoint: str
    result_endpoint: str
    cache_backend: str = "redis"
    graph_backend: str = "neo4j"


class SyncResult(BaseModel):
    race_id: str
    entries: int
    graph_nodes_upserted: int
    cached: bool
    source: str


class GraphNode(BaseModel):
    id: str
    label: str
    type: str


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str
    weight: float = 1.0


class HorseGraph(BaseModel):
    horse_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
