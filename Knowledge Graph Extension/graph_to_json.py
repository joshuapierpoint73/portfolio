from pathlib import Path
from rdflib import Graph, URIRef, Literal, RDF


try:
    from macros import PREFIX, ALLOWED_ARTEFACT_ABOUT_TYPES, DISPLAY_TYPE_LOOKUP_ORDER
except Exception:
    # Local fallback keeps the API independent from Wikidata/SPARQL imports.
    PREFIX = {
        "wd": "http://www.wikidata.org/entity/",
        "scho": "http://schema.org/",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    }
    ALLOWED_ARTEFACT_ABOUT_TYPES = {"Person", "MusicGroup", "MusicAlbum"}
    DISPLAY_TYPE_LOOKUP_ORDER = ["MusicGroup", "Person", "MusicAlbum"]


class GraphJsonReader:
    """
    Read the BME knowledge graph and return JSON-shaped dictionaries for the API.

    The TTL graph is the source of truth. No person_data.json, musicgroup_data.json,
    artefact_data.json, or header JSON files are required by this class.
    """

    CIDOC_ARTEFACT_TYPE = URIRef("http://www.cidoc-crm.org/cidoc-crm/E22_Human-Made_Object")

    def __init__(self, ttl_path, auto_reload=True):
        self.ttl_path = Path(ttl_path).resolve()
        self.auto_reload = auto_reload
        self.graph = Graph()
        self._last_mtime = None
        self.reload()

    # ---------------- GRAPH LOADING ---------------- #

    def reload(self):
        """Reload the TTL graph from disk."""
        self.graph = Graph()
        self.graph.parse(str(self.ttl_path), format="ttl")
        self._last_mtime = self.ttl_path.stat().st_mtime

    def refresh_if_needed(self):
        """Reload the graph if the TTL file has changed since the last request."""
        if not self.auto_reload:
            return

        current_mtime = self.ttl_path.stat().st_mtime
        if self._last_mtime is None or current_mtime != self._last_mtime:
            self.reload()

    # ---------------- URI HELPERS ---------------- #

    def _schema_uri(self, name):
        return URIRef(f"{PREFIX['scho']}{name}")

    def _rdfs_uri(self, name):
        return URIRef(f"{PREFIX['rdfs']}{name}")

    def _wd_uri(self, q_code):
        return URIRef(f"{PREFIX['wd']}{q_code}")

    def _last_uri_part(self, uri):
        return str(uri).rstrip("/").split("/")[-1]

    def _is_wikidata_uri(self, uri):
        return str(uri).startswith(PREFIX["wd"])

    def _literal(self, subject, predicate_name):
        value = self.graph.value(subject, self._schema_uri(predicate_name))
        return str(value) if value is not None else None

    # ---------------- DISPLAY HELPERS ---------------- #

    def get_display_name(self, subject):
        """Return the best readable name for a URI node."""
        for predicate in [self._schema_uri("name"), self._rdfs_uri("label")]:
            values = [str(value) for value in self.graph.objects(subject, predicate)]
            for value in values:
                if value and not value.startswith("Q"):
                    return value

        description = self.graph.value(subject, self._schema_uri("description"))
        if description:
            return str(description)

        return self._last_uri_part(subject)

    def _date_object(self, raw_value, prefix="dt", date_format="year"):
        if raw_value is None:
            return None

        raw = str(raw_value)

        if date_format == "dob":
            date_part = raw[:10]
            parts = date_part.split("-")
            if len(parts) == 3:
                display_value = f"{parts[2]}/{parts[1]}/{parts[0]}"
                return {
                    "id": f"{prefix}_{parts[2]}{parts[1]}{parts[0]}",
                    "name": display_value,
                    "value": display_value,
                }

        year = raw[:4]
        if year:
            return {
                "id": f"{prefix}_{year}",
                "name": year,
                "value": year,
            }

        return None

    def _named_uri_list(self, subject, predicate_name):
        results = []
        seen = set()

        for obj in self.graph.objects(subject, self._schema_uri(predicate_name)):
            if not isinstance(obj, URIRef):
                continue

            item_id = self._last_uri_part(obj)
            if item_id in seen:
                continue

            results.append({
                "id": item_id,
                "name": self.get_display_name(obj),
            })
            seen.add(item_id)

        results.sort(key=lambda item: item["name"].lower())
        return results

    def _get_zone_name(self, zone_uri):
        if not zone_uri:
            return None

        zone_name = self.graph.value(zone_uri, self._schema_uri("name"))
        if not zone_name:
            zone_name = self.graph.value(zone_uri, self._rdfs_uri("label"))

        if zone_name:
            return str(zone_name)

        zone_id = self._last_uri_part(zone_uri)
        if zone_id.startswith("Zone"):
            return zone_id.replace("Zone", "Zone ")

        return zone_id

    # ---------------- TYPE LOOKUP ---------------- #

    def get_entity_type(self, q_code):
        """Return the display type for a Wikidata Q-code, if the API can open it."""
        subject = self._wd_uri(q_code)

        for entity_type in DISPLAY_TYPE_LOOKUP_ORDER:
            if (subject, RDF.type, self._schema_uri(entity_type)) in self.graph:
                return entity_type

        # Some album nodes may be connected through schema:album even if the type
        # triple has not been written yet.
        if (None, self._schema_uri("album"), subject) in self.graph:
            return "MusicAlbum"

        return None

    def _get_about_entity_type(self, subject):
        if not isinstance(subject, URIRef):
            return None

        if self._is_wikidata_uri(subject):
            q_code = self._last_uri_part(subject)
            return self.get_entity_type(q_code)

        for entity_type in DISPLAY_TYPE_LOOKUP_ORDER:
            if (subject, RDF.type, self._schema_uri(entity_type)) in self.graph:
                return entity_type

        return None

    # ---------------- ARTEFACT LOOKUP ---------------- #

    def find_artefact_subject(self, artefact_id):
        identifier = self._schema_uri("identifier")

        for subject in self.graph.subjects(identifier, Literal(artefact_id)):
            return subject

        for subject in self.graph.subjects(RDF.type, self.CIDOC_ARTEFACT_TYPE):
            if self._last_uri_part(subject) == artefact_id:
                return subject

        return None

    def _related_artefacts(self, q_code):
        target = self._wd_uri(q_code)
        results = []
        seen = set()

        for artefact in self.graph.subjects(self._schema_uri("about"), target):
            artefact_id = self.graph.value(artefact, self._schema_uri("identifier"))
            if not artefact_id:
                artefact_id = self._last_uri_part(artefact)

            artefact_id = str(artefact_id)
            if artefact_id in seen:
                continue

            results.append({
                "id": artefact_id,
                "name": self.get_display_name(artefact),
            })
            seen.add(artefact_id)

        results.sort(key=lambda item: item["name"].lower())
        return results

    # ---------------- FORMATTERS ---------------- #

    def format_person(self, q_code):
        subject = self._wd_uri(q_code)
        if (subject, RDF.type, self._schema_uri("Person")) not in self.graph:
            return None

        result = {
            "id": q_code,
            "name": self.get_display_name(subject),
            "dob_date": self._date_object(
                self.graph.value(subject, self._schema_uri("date_of_birth")),
                date_format="dob",
            ),
            "memberships": self._named_uri_list(subject, "member_of"),
            "instruments": self._named_uri_list(subject, "instrument"),
        }

        artefacts = self._related_artefacts(q_code)
        if artefacts:
            result["artefacts"] = artefacts

        return result

    def format_music_group(self, q_code):
        subject = self._wd_uri(q_code)
        if (subject, RDF.type, self._schema_uri("MusicGroup")) not in self.graph:
            return None

        albums = []
        seen_albums = set()

        for album in self.graph.objects(subject, self._schema_uri("album")):
            if not isinstance(album, URIRef):
                continue

            album_id = self._last_uri_part(album)
            if album_id in seen_albums:
                continue

            year = self._date_object(self.graph.value(album, self._schema_uri("publication_date")))
            sort_year = 9999
            if year and str(year.get("value", "")).isdigit():
                sort_year = int(year["value"])

            albums.append({
                "id": album_id,
                "name": self.get_display_name(album),
                "year": year,
                "_sort_year": sort_year,
            })
            seen_albums.add(album_id)

        albums.sort(key=lambda item: (item["_sort_year"], item["name"].lower()))
        for album in albums:
            album.pop("_sort_year", None)

        result = {
            "id": q_code,
            "name": self.get_display_name(subject),
            "members": self._named_uri_list(subject, "has_member"),
            "est_year": self._date_object(self.graph.value(subject, self._schema_uri("inception"))),
            "genres": self._named_uri_list(subject, "genre"),
            "albums": albums,
        }

        artefacts = self._related_artefacts(q_code)
        if artefacts:
            result["artefacts"] = artefacts

        return result

    def format_music_album(self, q_code):
        subject = self._wd_uri(q_code)

        if self.get_entity_type(q_code) != "MusicAlbum":
            return None

        result = {
            "id": q_code,
            "name": self.get_display_name(subject),
            "artists": self._named_uri_list(subject, "artist"),
            "genres": self._named_uri_list(subject, "genre"),
            "year": self._date_object(self.graph.value(subject, self._schema_uri("publication_date"))),
        }

        artefacts = self._related_artefacts(q_code)
        if artefacts:
            result["artefacts"] = artefacts

        return result

    def format_artefact(self, artefact_id):
        subject = self.find_artefact_subject(artefact_id)
        if subject is None:
            return None

        about = []
        seen = set()

        for obj in self.graph.objects(subject, self._schema_uri("about")):
            if not isinstance(obj, URIRef):
                continue

            linked_type = self._get_about_entity_type(obj)
            if linked_type not in ALLOWED_ARTEFACT_ABOUT_TYPES:
                continue

            linked_id = self._last_uri_part(obj)
            if linked_id in seen:
                continue

            about.append({
                "id": linked_id,
                "name": self.get_display_name(obj),
                "type": linked_type,
            })
            seen.add(linked_id)

        about.sort(key=lambda item: (item["type"], item["name"].lower()))

        artefact = {
            "id": artefact_id,
            "name": self.get_display_name(subject),
            "about": about,
            "zone": self._get_zone_name(self.graph.value(subject, self._schema_uri("isPartOf"))),
            "item_location": self._literal(subject, "itemLocation"),
            "image": self._literal(subject, "image"),
        }

        return {key: value for key, value in artefact.items() if value is not None}

    # ---------------- API DATA METHODS ---------------- #

    def get_header(self, entity_id):
        self.refresh_if_needed()

        if entity_id.startswith("Q"):
            entity_type = self.get_entity_type(entity_id)
            if not entity_type:
                return None

            return {
                "id": entity_id,
                "name": self.get_display_name(self._wd_uri(entity_id)),
                "type": entity_type,
            }

        artefact = self.find_artefact_subject(entity_id)
        if artefact is not None:
            return {
                "id": entity_id,
                "name": self.get_display_name(artefact),
                "type": "Artefact",
            }

        return None

    def get_body(self, entity_id):
        self.refresh_if_needed()

        if entity_id.startswith("Q"):
            entity_type = self.get_entity_type(entity_id)

            if entity_type == "Person":
                return self.format_person(entity_id)
            if entity_type == "MusicGroup":
                return self.format_music_group(entity_id)
            if entity_type == "MusicAlbum":
                return self.format_music_album(entity_id)

            return None

        return self.format_artefact(entity_id)

    def get_root_entities(self, root_type):
        self.refresh_if_needed()

        if root_type == "Genre":
            return [
                {"id": genre["id"], "name": genre["name"]}
                for genre in self.build_genre_index().values()
            ]

        if root_type == "Artefact":
            results = []
            for subject in self.graph.subjects(RDF.type, self.CIDOC_ARTEFACT_TYPE):
                artefact_id = self.graph.value(subject, self._schema_uri("identifier"))
                if not artefact_id:
                    artefact_id = self._last_uri_part(subject)

                results.append({
                    "id": str(artefact_id),
                    "name": self.get_display_name(subject),
                })

            results.sort(key=lambda item: item["name"].lower())
            return results

        if root_type not in ["Person", "MusicGroup"]:
            return None

        results = []
        for subject in self.graph.subjects(RDF.type, self._schema_uri(root_type)):
            if not self._is_wikidata_uri(subject):
                continue

            results.append({
                "id": self._last_uri_part(subject),
                "name": self.get_display_name(subject),
            })

        results.sort(key=lambda item: item["name"].lower())
        return results

    def build_genre_index(self):
        self.refresh_if_needed()

        genre_map = {}

        for group in self.graph.subjects(RDF.type, self._schema_uri("MusicGroup")):
            if not self._is_wikidata_uri(group):
                continue

            group_id = self._last_uri_part(group)
            group_name = self.get_display_name(group)

            for genre in self.graph.objects(group, self._schema_uri("genre")):
                if not isinstance(genre, URIRef):
                    continue

                genre_id = self._last_uri_part(genre)
                genre_name = self.get_display_name(genre)

                if genre_id not in genre_map:
                    genre_map[genre_id] = {
                        "id": genre_id,
                        "name": genre_name,
                        "groups": [],
                    }

                genre_map[genre_id]["groups"].append({
                    "id": group_id,
                    "name": group_name,
                })

        for genre in genre_map.values():
            genre["groups"].sort(key=lambda item: item["name"].lower())

        return dict(sorted(genre_map.items(), key=lambda item: item[1]["name"].lower()))

    def expand_genre(self, genre_id):
        self.refresh_if_needed()
        genre = self.build_genre_index().get(genre_id)
        return genre["groups"] if genre else None

    def status(self):
        self.refresh_if_needed()
        return {
            "source": "ttl_graph",
            "ttl_path": str(self.ttl_path),
            "triple_count": len(self.graph),
            "auto_reload": self.auto_reload,
        }
