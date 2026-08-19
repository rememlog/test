from neo4j import GraphDatabase
from app.core.config import settings
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
