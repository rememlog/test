from pydantic import BaseModel, Field


class HorseScore(BaseModel):
    horse_id: str
    horse_name: str
    jockey: str
    trainer: str
    model_probability: float = Field(ge=0, le=1)
    market_probability: float = Field(ge=0, le=1)
    value_gap: float
    score: float = Field(ge=0, le=100)
    reasons: list[str]


class RaceRanking(BaseModel):
    race_id: str
    track: str
    distance_m: int
    horses: list[HorseScore]


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
