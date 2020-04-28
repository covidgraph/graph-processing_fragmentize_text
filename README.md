# Requirements
## Client
py2neo

## Server
The Neo4J server needs to have APOC installed. Just grab the version you need from https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/ and put it in the plugins/ directory of your Neo4J installation.

# create :Fragment nodes for publications

## Body_text
```
CALL apoc.periodic.iterate(
"MATCH (text_node:Body_text) WHERE NOT text_node:CollectionHub RETURN text_node",
"WITH text_node,split(text_node.text, '. ') AS frags
WHERE size(frags) > 0
WITH text_node,frags,range(0,size(frags)-1) AS r
WITH text_node,frags,r
FOREACH ( entry in r | CREATE (f:Fragment:FromBody_text) 
			SET f.text = frags[entry], f.sequence = entry, f.kind = labels(text_node)[0]
			MERGE (text_node)-[:HAS_FRAGMENT]->(f) )",
{batchSize: 100, iterateList: true, parallel: false}
)
```

`WHERE size(frags) > 0` checks if the property was 
 
 only works if the text property is not null

### link Fragments
```
MATCH (f:Fragment:FromBody_text) 
WHERE f.sequence > 0
MATCH (f)<--(n)-->(f2:TestFragment:FromBody_text)
WHERE f2.sequence = f.sequence - 1
MERGE (f2)-[:NEXT]->(f)
```


## Abstract
```
CALL apoc.periodic.iterate(
"MATCH (text_node:Abstract) WHERE NOT text_node:CollectionHub RETURN text_node",
"WITH text_node,split(text_node.text, '. ') AS frags
WHERE size(frags) > 0
WITH text_node,frags,range(0,size(frags)-1) AS r
WITH text_node,frags,r
FOREACH ( entry in r | CREATE (f:Fragment:FromAbstract) 
			SET f.text = frags[entry], f.sequence = entry, f.kind = labels(text_node)[0]
			MERGE (text_node)-[:HAS_FRAGMENT]->(f) )",
{batchSize: 100, iterateList: true, parallel: false}
)
```

### link Fragments
```
MATCH (f:TestFragment:FromAbstract) 
WHERE f.sequence > 0
MATCH (f)<--(n)-->(f2:TestFragment:FromAbstract)
WHERE f2.sequence = f.sequence - 1
MERGE (f2)-[:NEXT]->(f)
```
