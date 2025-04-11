import json
from typing import Dict
from langchain_community.graphs import Neo4jGraph

from docuquery.constants.neo4j import EMBEDDING_NODE_LABEL

BASE_ENTITY_LABEL = "__Entity__"
EXCLUDED_LABELS = ["_Bloom_Perspective_", "_Bloom_Scene_"] + [EMBEDDING_NODE_LABEL]
EXCLUDED_RELS = ["_Bloom_HAS_SCENE_"]

node_properties_query = """
CALL apoc.meta.data()
YIELD label, other, elementType, type, property
WHERE NOT type = "RELATIONSHIP" AND elementType = "node" 
  AND NOT label IN $EXCLUDED_LABELS
WITH label AS nodeLabels, collect({property:property, type:type}) AS properties
RETURN {labels: nodeLabels, properties: properties} AS output

"""

rel_properties_query = """
CALL apoc.meta.data()
YIELD label, other, elementType, type, property
WHERE NOT type = "RELATIONSHIP" AND elementType = "relationship"
      AND NOT label in $EXCLUDED_LABELS
WITH label AS nodeLabels, collect({property:property, type:type}) AS properties
RETURN {type: nodeLabels, properties: properties} AS output
"""

rel_query = """
CALL apoc.meta.data()
YIELD label, other, elementType, type, property
WHERE type = "RELATIONSHIP" AND elementType = "node"
UNWIND other AS other_node
WITH * WHERE NOT label IN $EXCLUDED_LABELS
    AND NOT other_node IN $EXCLUDED_LABELS
RETURN {start: label, type: property, end: toString(other_node)} AS output
"""

CACHE_JSON = "./schema_cache.json"


class Neo4jGraphPlus(Neo4jGraph):
    def refresh_schema(self) -> None:
        """
        Refreshes the Neo4j graph schema information.
        """
        from neo4j.exceptions import ClientError

        schema_json = {}
        try:
            with open(CACHE_JSON, "r") as file:
                schema_json = json.load(file)
        except FileNotFoundError:
            print(f"Error: The file {CACHE_JSON} does not exist.")

        if schema_json:
            node_properties = schema_json.get("node_properties")
            rel_properties = schema_json.get("relationship_properties")
            relationships = schema_json.get("relationships")
        else:
            node_properties = [
                el["output"]
                for el in self.query(
                    node_properties_query,
                    params={"EXCLUDED_LABELS": EXCLUDED_LABELS + [BASE_ENTITY_LABEL]},
                )
            ]
            rel_properties = [
                el["output"]
                for el in self.query(
                    rel_properties_query, params={"EXCLUDED_LABELS": EXCLUDED_RELS}
                )
            ]
            relationships = [
                el["output"]
                for el in self.query(
                    rel_query,
                    params={"EXCLUDED_LABELS": EXCLUDED_LABELS + [BASE_ENTITY_LABEL]},
                )
            ]

            schema_json["node_properties"] = node_properties
            schema_json["relationship_properties"] = rel_properties
            schema_json["relationships"] = relationships

            with open(CACHE_JSON, "w") as file:
                json.dump(schema_json, file, indent=4)

        # Get constraints & indexes
        try:
            constraint = self.query("SHOW CONSTRAINTS")
            index = self.query("SHOW INDEXES YIELD *")
        except (
            ClientError
        ):  # Read-only user might not have access to schema information
            constraint = []
            index = []

        self.structured_schema = {
            "node_props": {el["labels"]: el["properties"] for el in node_properties},
            "rel_props": {el["type"]: el["properties"] for el in rel_properties},
            "relationships": relationships,
            "metadata": {"constraint": constraint, "index": index},
        }

        # Format node properties
        formatted_node_props = []
        for el in node_properties:
            props_str = ", ".join(
                [f"{prop['property']}: {prop['type']}" for prop in el["properties"]]
            )
            formatted_node_props.append(f"{el['labels']} {{{props_str}}}")

        # Format relationship properties
        formatted_rel_props = []
        for el in rel_properties:
            props_str = ", ".join(
                [f"{prop['property']}: {prop['type']}" for prop in el["properties"]]
            )
            formatted_rel_props.append(f"{el['type']} {{{props_str}}}")

        # Format relationships
        formatted_rels = [
            f"(:{el['start']})-[:{el['type']}]->(:{el['end']})" for el in relationships
        ]

        self.schema = "\n".join(
            [
                "Node properties are the following:",
                ",".join(formatted_node_props),
                "Relationship properties are the following:",
                ",".join(formatted_rel_props),
                "The relationships are the following:",
                ",".join(formatted_rels),
            ]
        )
