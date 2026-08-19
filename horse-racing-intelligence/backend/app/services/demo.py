from app.models.schemas import GraphEdge, GraphNode, HorseGraph, HorseScore, RaceRanking

HORSES = [
    ("H001", "글로벌히트", "김태현", "방동석", 0.274, 0.160, ["1400m 거리 적합", "기수 조합 우수", "최근 후반 600m 양호"]),
    ("H002", "블루파이어", "이성재", "문현철", 0.192, 0.188, ["최근 폼 안정", "주로 적합 보통"]),
    ("H003", "스피드킹", "박준호", "최민수", 0.141, 0.122, ["초반 전개 강점", "부담중량 증가"]),
    ("H004", "문라이트", "최시대", "김영관", 0.121, 0.145, ["기수 변경", "최근 마체중 안정"]),
    ("H005", "레드스타", "정정희", "송문길", 0.113, 0.142, ["거리 경험 충분", "시장 대비 모델 저평가"]),
    ("H006", "윈드러너", "유승완", "서인석", 0.081, 0.113, ["최근 성적 변동성 큼"]),
    ("H007", "골든웨이", "문세영", "박재우", 0.078, 0.130, ["기수 강점", "거리 적합도 낮음"]),
]


def ranking() -> RaceRanking:
    rows = []
    for hid, name, jockey, trainer, model_p, market_p, reasons in HORSES:
        gap = model_p - market_p
        score = min(100.0, max(0.0, 50 + gap * 180 + model_p * 70))
        rows.append(HorseScore(horse_id=hid, horse_name=name, jockey=jockey, trainer=trainer, model_probability=model_p, market_probability=market_p, value_gap=round(gap, 3), score=round(score, 1), reasons=reasons))
    rows.sort(key=lambda x: x.model_probability, reverse=True)
    return RaceRanking(race_id="SEOUL-20260822-07", track="SEOUL", distance_m=1400, horses=rows)


def horse_graph(horse_id: str) -> HorseGraph:
    selected = next((x for x in HORSES if x[0] == horse_id), HORSES[0])
    hid, name, jockey, trainer, *_ = selected
    nodes = [GraphNode(id=hid, label=name, type="Horse"), GraphNode(id=f"J-{jockey}", label=jockey, type="Jockey"), GraphNode(id=f"T-{trainer}", label=trainer, type="Trainer"), GraphNode(id="R-SEOUL-20260822-07", label="서울 7R", type="Race"), GraphNode(id="D-1400", label="1400m", type="Distance"), GraphNode(id="TRACK-SEOUL", label="서울경마공원", type="Track")]
    edges = [GraphEdge(source=hid, target=f"J-{jockey}", type="RIDDEN_BY", weight=0.86), GraphEdge(source=hid, target=f"T-{trainer}", type="TRAINED_BY", weight=0.91), GraphEdge(source=hid, target="R-SEOUL-20260822-07", type="RUNS_IN", weight=1.0), GraphEdge(source="R-SEOUL-20260822-07", target="D-1400", type="DISTANCE", weight=1.0), GraphEdge(source="R-SEOUL-20260822-07", target="TRACK-SEOUL", type="HELD_AT", weight=1.0)]
    return HorseGraph(horse_id=hid, nodes=nodes, edges=edges)
