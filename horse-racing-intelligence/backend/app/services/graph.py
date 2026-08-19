from neo4j import GraphDatabase

from app.core.config import settings
from app.models.schemas import GraphEdge, GraphNode, HorseEntry, HorseGraph
from app.services.demo import HORSES


class GraphService:
    def __init__(self):
        self.driver = GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password))

    def close(self):
        self.driver.close()

    def seed_demo(self) -> int:
        query = """
        MERGE (r:Race {id: 'SEOUL-20260822-07', track: 'SEOUL', distance_m: 1400})
        WITH r
        UNWIND $horses AS h
        MERGE (horse:Horse {id: h.id}) SET horse.name = h.name
        MERGE (j:Jockey {name: h.jockey})
        MERGE (t:Trainer {name: h.trainer})
        MERGE (horse)-[:RIDDEN_BY]->(j)
        MERGE (horse)-[:TRAINED_BY]->(t)
        MERGE (horse)-[:RUNS_IN]->(r)
        RETURN count(horse) AS seeded
        """
        horses = [{"id": h[0], "name": h[1], "jockey": h[2], "trainer": h[3]} for h in HORSES]
        records, _, _ = self.driver.execute_query(query, horses=horses)
        return int(records[0]["seeded"]) if records else 0

    def upsert_entries(self, entries: list[HorseEntry]) -> int:
        if not entries:
            return 0
        query = """
        UNWIND $entries AS e
        MERGE (race:Race {id: e.race_id})
          SET race.track = e.track, race.race_date = e.race_date,
              race.race_no = e.race_no, race.distance_m = e.distance_m
        MERGE (track:Track {name: e.track})
        MERGE (race)-[:HELD_AT]->(track)
        MERGE (horse:Horse {id: e.horse_id})
          SET horse.name = e.horse_name, horse.rating = e.rating
        MERGE (horse)-[ent:ENTERS]->(race)
          SET ent.draw = e.draw, ent.carried_weight = e.carried_weight
        FOREACH (_ IN CASE WHEN e.jockey_id <> '' OR e.jockey_name <> '' THEN [1] ELSE [] END |
          MERGE (j:Jockey {id: CASE WHEN e.jockey_id <> '' THEN e.jockey_id ELSE e.jockey_name END})
          SET j.name = e.jockey_name
          MERGE (horse)-[:RIDDEN_BY]->(j)
        )
        FOREACH (_ IN CASE WHEN e.trainer_id <> '' OR e.trainer_name <> '' THEN [1] ELSE [] END |
          MERGE (t:Trainer {id: CASE WHEN e.trainer_id <> '' THEN e.trainer_id ELSE e.trainer_name END})
          SET t.name = e.trainer_name
          MERGE (horse)-[:TRAINED_BY]->(t)
        )
        FOREACH (_ IN CASE WHEN e.owner_id <> '' OR e.owner_name <> '' THEN [1] ELSE [] END |
          MERGE (o:Owner {id: CASE WHEN e.owner_id <> '' THEN e.owner_id ELSE e.owner_name END})
          SET o.name = e.owner_name
          MERGE (o)-[:OWNS]->(horse)
        )
        RETURN count(horse) AS upserted
        """
        rows = [entry.model_dump(exclude={"raw"}) for entry in entries]
        records, _, _ = self.driver.execute_query(query, entries=rows)
        return int(records[0]["upserted"]) if records else 0

    def horse_graph(self, horse_id: str, limit: int = 40) -> HorseGraph:
        query = """
        MATCH (h:Horse {id: $horse_id})
        OPTIONAL MATCH (h)-[r]-(n)
        RETURN h, collect(DISTINCT n)[0..$limit] AS neighbors,
               collect(DISTINCT r)[0..$limit] AS rels
        """
        records, _, _ = self.driver.execute_query(query, horse_id=horse_id, limit=limit)
        if not records:
            return HorseGraph(horse_id=horse_id, nodes=[], edges=[])
        record = records[0]
        h = record["h"]
        nodes = [GraphNode(id=horse_id, label=h.get("name", horse_id), type="Horse")]
        seen = {horse_id}
        for n in record["neighbors"]:
            node_id = str(n.get("id", n.get("name", n.element_id)))
            if node_id in seen:
                continue
            seen.add(node_id)
            node_type = next(iter(n.labels), "Node")
            nodes.append(GraphNode(id=node_id, label=str(n.get("name", n.get("id", node_id))), type=node_type))
        edges = []
        for rel in record["rels"]:
            source = str(rel.start_node.get("id", rel.start_node.get("name", rel.start_node.element_id)))
            target = str(rel.end_node.get("id", rel.end_node.get("name", rel.end_node.element_id)))
            edges.append(GraphEdge(source=source, target=target, type=rel.type))
        return HorseGraph(horse_id=horse_id, nodes=nodes, edges=edges)
