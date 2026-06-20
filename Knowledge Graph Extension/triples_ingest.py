"""

This module is concerned with adding the triples to the KG. Especially converting a WikiData representation to schema.org as it is the format used in the BME KG

TODO List:
    [1] Loop over a type (e.g instrument, artist) in add_entity etc to parameterise the types of entities we want to add to the KG. (Line 86)

"""
import os
from rdflib import Graph, Namespace, URIRef, Literal, RDF
from find_links import KGValidator, KGLinker
from macros import PREFIX, SCHEMA_TYPES

def validate_qcode(ttl_path, q_code):
    
    v = KGValidator(ttl_path, q_code)
    isExisting = v.validate_kg()
    print(f"Entity {q_code} exists in KG: {isExisting}")

    return isExisting

def get_entity(q_code: str, l = KGLinker()):
    return l.get_wikidata_entity(q_code)


def add_entity_to_kg(ttl_path: str, q_code: str, entity_type: str, label: str, attributes: dict):

    """
    
    Add a new entity to the KG by fetching its information from WikiData and appending it to the .ttl file. The function checks if the entity already exists in the KG before attempting to add it.

    Args:
        ttl_path (str): The file path to the .ttl file of the KG.
        q_code (str): The Q-code of the entity to add.
        attributes : ...
    
    Returns:
        None: (Writes to file)
    
    """

    ## -- Make the KG in rdflib and parse
    g = Graph()
    g.parse(ttl_path, format="ttl")

    subject = URIRef(f"{PREFIX['wd']}{q_code}")

    schema_type = SCHEMA_TYPES.get(entity_type)

    ## -- Create the new entity as a URIRef and add its label and type to the graph
    g.add((subject, URIRef(f"{PREFIX['rdfs']}label"), Literal(label, lang="en")))
    g.add((subject, RDF.type, URIRef(f"{PREFIX['scho']}{schema_type}")))

    for prop, values in attributes.items():

        predicate = URIRef(f"{PREFIX['scho']}{prop}")

        for v in values:
            if isinstance(v, dict):
                obj = URIRef(f"{PREFIX['wd']}{v['qcode']}")
                g.add((subject, predicate, obj))
                g.add((obj, URIRef(f"{PREFIX['rdfs']}label"), Literal(v["label"], lang="en")))
            else:
                g.add((subject, predicate, Literal(v)))
            
    ## -- Serialize the updated graph back to the .ttl file
    g.serialize(destination=ttl_path, format="ttl")



if __name__ == "__main__":
    import os
    import questionary
    from macros import SCHEMA_TYPES

    # --- Path to KG TTL file
    ttl_path = os.path.join(
        os.getcwd(),
        "assets",
        "graphs",
        "bme_knowledge_graph.ttl"
    )

    # -- Get the Wikidata Q-code
    wikidata_id = input("Enter the Wikidata Q-code of the entity to add (e.g., Q26876): ").strip()

    # -- Select entity type (drives property fetching from Wikidata)
    entity_type = questionary.select(
        "Select the type of entity to fetch from Wikidata:",
        choices=list(SCHEMA_TYPES.keys())
    ).ask()

    # -- Check if entity already exists in KG
    if validate_qcode(ttl_path, wikidata_id):
        print(f"Entity {wikidata_id} already exists in the KG.")
        exit()

    # -- Fetch label and attributes from Wikidata
    linker = KGLinker()
    label, attributes = linker.get_wikidata_entity(wikidata_id, entity_type)



    if not label:
        print(f"No data returned for {wikidata_id} of type {entity_type}")
        exit()

    # -- Map internal entity_type to schema.org type
    schema_type = SCHEMA_TYPES.get(entity_type, "Thing")

    # -- Add entity to KG
    add_entity_to_kg(ttl_path, wikidata_id, entity_type, label, attributes)
    print(f"Successfully added {label} ({wikidata_id}) as {schema_type} to the KG")
