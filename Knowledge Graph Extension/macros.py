from SPARQLWrapper import SPARQLWrapper, JSON

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"

# ---------------- PREFIX ---------------- #

PREFIX = {
    "wd": "http://www.wikidata.org/entity/",
    "scho": "http://schema.org/",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
}

# ---------------- SCHEMA TYPES ---------------- #

SCHEMA_TYPES = {
    "artist": "Person",
    "instrument": "MusicInstrument",
    "event": "MusicEvent",
    "group": "MusicGroup",
    "album": "MusicAlbum",
    "song": "MusicRecording",
    "genre": "MusicGenre"
}


# ---------------- FRONTEND ENTITY CONFIG ---------------- #

# Entity types that can be opened directly by the frontend graph.
DISPLAY_ENTITY_TYPES = {"Person", "MusicGroup", "MusicAlbum"}

# Artefact about-links should only point to entities the graph can display.
ALLOWED_ARTEFACT_ABOUT_TYPES = DISPLAY_ENTITY_TYPES

# Shared mapping between frontend entity types and JSON file names.
ENTITY_FILE_STUBS = {
    "Person": "person",
    "MusicGroup": "musicgroup",
    "MusicAlbum": "musicalbum",
    "Artefact": "artefact",
}

# Type lookup order used when resolving an artefact about-link.
# Groups are checked before people to avoid bands being labelled as Person.
DISPLAY_TYPE_LOOKUP_ORDER = ["MusicGroup", "Person", "MusicAlbum"]

# ---------------- WIKIDATA PROPERTIES ---------------- #

WIKIDATA_PROPERTIES = {
    "artist": {
        "instrument": "P1303",
        "country": "P27",
        "date_of_birth": "P569",
        "member_of": "P463",
        "influenced_by": "P737",
    },
    "group": {
        "genre": "P136",
        "country": "P495",
        "inception": "P571",
        "has_member": "P527",
        "influenced_by": "P737",
    },
    "song": {
        "performer": "P175",
        "producer": "P162",
        "genre": "P136",
        "publication_date": "P577",
        "album": "P361"
    },
    "album": {
        "artist": "P175",
        "genre": "P136",
        "publication_date": "P577"
    }
}

# ---------------- TYPE LAYERS ---------------- #

TYPE_TO_LAYERS = {
    "Person": ["MusicGroup", "MusicGenre", "Person"],
    "MusicGroup": ["Person", "MusicAlbum", "MusicGenre", "Person"],
    "MusicAlbum": ["MusicRecording"],
    "MusicGenre": ["MusicGroup"],
}

# ---------------- VALIDATION CONFIG ---------------- #

# True = strict (only real artists)
# False = expand everything
STRICT_ARTIST_VALIDATION = False

# ---------------- DISPLAY LIMITS ---------------- #

MAIN_ALBUM_LIMIT = 5
MAIN_GENRE_LIMIT = 3

# ---------------- VALIDATE ARTIST ---------------- #

def validate_artist(q_code: str) -> bool:
    """
    Validate whether a Wikidata entity is an artist.

    Behaviour:
    - If STRICT_ARTIST_VALIDATION = False -> always returns True
    - Otherwise checks profession (P106)
    """
    if not STRICT_ARTIST_VALIDATION:
        return True

    sparql = SPARQLWrapper(WIKIDATA_ENDPOINT)

    query = f"""
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>

        ASK WHERE {{
            wd:{q_code} wdt:P106 ?profession .
            VALUES ?profession {{
                wd:Q177220
                wd:Q639669
                wd:Q36834
                wd:Q488205
            }}
        }}
    """

    try:
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        return bool(results.get("boolean", False))

    except Exception as e:
        print(f"Validation failed for {q_code}: {e}")
        return False
