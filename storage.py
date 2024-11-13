from neo4j import GraphDatabase

from models import InsertRequest, Node

class Neo4jStorage:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()

    def get_all_nodes(self):
        with self.driver.session() as session:
            query = "MATCH (n) RETURN n.id AS id, labels(n) AS label"
            result = session.run(query)
            nodes = [{"id": record["id"], "label": record["label"][0]} for record in result]
            return nodes

    def get_node_with_relations(self, node_id):
        with self.driver.session() as session:
            query = """
                MATCH (n)-[r]->(m) WHERE id(n) = $id
                RETURN n {.*} AS node, id(n) AS node_id, type(r) AS relationship_type, 
                       m {.*} AS end_node, id(m) AS end_node_id
            """
            result = session.run(query, id=node_id)
            relations = []
            for record in result:
                relations.append({
                    "node": {
                        "id": record["node_id"],
                        "city": record["node"].get("home_town", ""),
                        "name": record["node"].get("name", ""),
                        "sex": record["node"].get("sex", 0),
                        "screen_name": record["node"].get("screen_name", "")
                    },
                    "relationship_type": record["relationship_type"],
                    "end_node": {
                        "id": record["end_node_id"],
                        "name": record["end_node"].get("name", ""),
                        "screen_name": record["end_node"].get("screen_name", "")
                    }
                })
            return relations

    def add_node_and_relationships(self, data: InsertRequest):
        with self.driver.session() as session:
            query = """
                MERGE (n:User {id: $id, name: $name, screen_name: $screen_name, sex: $sex, home_town: $city})
            """
            session.run(query, id=data.node.id, name=data.node.name,
                        screen_name=data.node.screen_name, sex=data.node.sex,
                        city=data.node.city)
            for rel in data.relationships:
                if rel.type.upper() not in ["FOLLOWS", "SUBSCRIBES"]:
                    continue
                end_node = self.get_one_by_id(rel.end_node_id)
                query = f"""
                    MATCH (n:User {{id: $id}})
                    MATCH (m:{end_node["label"]} {{id: $end_node_id}})
                    MERGE (n)-[r:{rel.type.upper()}]->(m)
                """
                session.run(query, id=data.node.id, end_node_id=rel.end_node_id)

    def delete_node_and_relationships(self, node_id):
        with self.driver.session() as session:
            query = "MATCH (n) WHERE n.id=$id DETACH DELETE n"
            session.run(query, id=node_id)

    def get_one_by_id(self, node_id) -> Node:
        with self.driver.session() as session:
            query = "MATCH (n) WHERE n.id = $id RETURN id(n) AS id, labels(n) AS label"
            result = session.run(query, id=node_id)
            record = result.single()
            if record:
                return {"id": record["id"], "label": record["label"][0]}
            return None