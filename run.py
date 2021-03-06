import os
import logging
import py2neo
import json

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('py2neo.connect.bolt').setLevel(logging.WARNING)
logging.getLogger('py2neo.connect').setLevel(logging.WARNING)
logging.getLogger('graphio').setLevel(logging.WARNING)
logging.getLogger('neobolt').setLevel(logging.WARNING)

log = logging.getLogger(__name__)

NEO4J_CONFIG_STRING = os.getenv("NEO4J")

try:
    log.info(NEO4J_CONFIG_STRING)
    NEO4J_CONFIG_DICT = json.loads(NEO4J_CONFIG_STRING)
except json.decoder.JSONDecodeError:
    # try to replace single quotes with double quotes
    # JSON always expects double quotes, common mistake when writing JSON strings
    NEO4J_CONFIG_STRING = NEO4J_CONFIG_STRING.replace("'", '"')
    log.info(NEO4J_CONFIG_STRING)
    NEO4J_CONFIG_DICT = json.loads(NEO4J_CONFIG_STRING)

log.info(f'dict {NEO4J_CONFIG_DICT}')
RUN_MODE = os.getenv('RUN_MODE', 'prod')


def create_query_fragments_for_node(label, text_property):
    """
    Create :Fragment nodes for text stored on nodes.

    :param label: The label of the text node
    :param text_property: Name of the property containing the text
    :return: Query to create :Fragment nodes
    """
    log.debug("Create query for label {}, text property {}".format(label, text_property))

    q = """CALL apoc.periodic.iterate(
\"MATCH (text_node:{0}) WHERE NOT text_node:CollectionHub AND NOT (text_node)-[:HAS_FRAGMENT]-() RETURN text_node\",
\"WITH text_node,split(text_node.{1}, '. ') AS frags
WHERE size(frags) > 0
WITH text_node,frags,range(0,size(frags)-1) AS r
WITH text_node,frags,r
FOREACH ( entry in r | CREATE (f:Fragment:From{0}) 
                SET f.text = frags[entry], f.sequence = entry, f.kind = labels(text_node)[0]
                MERGE (text_node)-[:HAS_FRAGMENT]->(f) )\",
{{batchSize: 100, iterateList: true, parallel: false}}
)""".format(label, text_property)

    log.debug(q)
    return q


def create_query_link_fragments(label):
    """
    Query to link the :Fragment nodes.

    :param label: Label of text node
    :return: The query
    """
    log.debug("Create query to link fragments from {}".format(label))

    q = """CALL apoc.periodic.iterate(
    \"MATCH (f:Fragment:From{0}) WHERE f.sequence > 0 RETURN f\",
    \"MATCH (f)<--(n)-->(f2:Fragment:From{0})
    WHERE f2.sequence = f.sequence - 1
    MERGE (f2)-[:NEXT]->(f)\",
    {{batchSize: 5, iterateList: true, parallel: true}}
)""".format(label)

    log.debug(q)
    return q


if __name__ == '__main__':
    if RUN_MODE.lower() == 'test':
        log.info("Run tests")
    else:
        graph = py2neo.Graph(**NEO4J_CONFIG_DICT)
        log.debug(graph)

        # create index
        try:
            graph.run("CREATE INDEX ON :Fragment(sequence)")
        except py2neo.database.work.ClientError:
            log.info("Create index on :Fragment(sequence) fails, likely Neo4j 4 which throws error when trying to create existing index.")

        # create fragments for Body_text
        log.debug("Create fragments for BodyText and Abstract")

        text_nodes = [
            ('BodyText', 'text'),
            ('Abstract', 'text'),
            ('PatentDescription', 'text'),
            ('PatentTitle', 'text'),
            ('PatentAbstract', 'text'),
            ('PatentClaim', 'text')
        ]

        for label, prop in text_nodes:
            query_fragments = create_query_fragments_for_node(label, prop)
            graph.run(query_fragments)

            #query_link_fragments = create_query_link_fragments(label)
            #graph.run(query_link_fragments)
