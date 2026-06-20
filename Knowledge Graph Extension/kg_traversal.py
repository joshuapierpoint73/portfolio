from rdflib import Graph, URIRef, Literal, RDF
from find_links import KGLinker
from macros import (
    ALLOWED_ARTEFACT_ABOUT_TYPES,
    DISPLAY_TYPE_LOOKUP_ORDER,
    ENTITY_FILE_STUBS,
    SCHEMA_TYPES,
    PREFIX,
    validate_artist,
)

import pickle
import os
from tqdm import tqdm
import json
from pathlib import Path
import questionary
from metrics import process_triple


## ---------------- KG TRAVERSAL ---------------- ##
class KGTraverser:
    def __init__(self, ttl_path, cache_path="cache.pkl"):
        """
        Initialise graph, cache, and traversal settings.

        Args:
            ttl_path (str | Path): Path to the TTL file for the knowledge graph.
            cache_path (str): Path to the cache file.
        """
        self.ttl_path = Path(ttl_path).resolve()
        self.project_root = Path(__file__).resolve().parent

        self.is_full_expansion = False
        self.metrics_reset_done = False

        self.graph = Graph()
        self.graph.parse(self.ttl_path.as_uri(), format="ttl")

        self.visited = set()
        self.linker = KGLinker()

        self.cache_path = self.project_root / cache_path
        self.entity_cache = {}
        self.validation_cache = {}

        self._load_cache()

        self.traversaljson_path = self.ttl_path.parent.parent / "entity"
        os.makedirs(self.traversaljson_path, exist_ok=True)

        self.schema_to_wd_type = {
            "Person": "artist",
            "MusicGroup": "group",
            "MusicAlbum": "album",
            "MusicRecording": "song",
        }

        self.entity_type_to_schema_key = {
            "Person": "artist",
            "MusicGroup": "group",
            "MusicAlbum": "album",
            "MusicRecording": "song",
            "MusicGenre": "genre",
            "MusicInstrument": "instrument"
        }

        self.metrics_path = os.path.normpath(
            os.path.join(self.ttl_path.parent.parent, "metrics", "expansion_metrics.json")
        )

    # ---------------- CACHE ---------------- #

    def _load_cache(self):
        """Load cached entities if available."""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "rb") as file:
                    data = pickle.load(file)
                    self.entity_cache = data.get("entity_cache", {})
                    self.validation_cache = data.get("validation_cache", {})
                print(f"Cache loaded ({len(self.entity_cache)} entities)")
            except Exception:
                print("Cache corrupted. Resetting.")
                self.entity_cache = {}
                self.validation_cache = {}

    def _save_cache(self):
        """Save entity and validation cache to disk."""
        with open(self.cache_path, "wb") as file:
            pickle.dump({
                "entity_cache": self.entity_cache,
                "validation_cache": self.validation_cache
            }, file)
        print("Cache saved.")

    def clear_empty_cache_entries(self):
        """Remove cached entries that contain no label and no attributes."""
        bad_keys = []

        for key, value in self.entity_cache.items():
            label, attributes = value

            if not label and not any(attributes.values()):
                bad_keys.append(key)

        for key in bad_keys:
            del self.entity_cache[key]

        print(f"Removed {len(bad_keys)} empty cache entries")

    # ---------------- METRICS ---------------- #

    def _record_triple_metric(self, subject, predicate, obj):
        """Record a triple addition/update in the metrics file."""
        should_reset_metrics = self.is_full_expansion and not self.metrics_reset_done

        process_triple(
            subject,
            predicate,
            obj,
            self.metrics_path,
            full_expansion=should_reset_metrics,
        )

        if should_reset_metrics:
            self.metrics_reset_done = True
            self.is_full_expansion = False

    # ---------------- LABEL HELPERS ---------------- #

    def _replace_label(self, subject, new_label):
        """
        Remove bad Q-code labels and store the correct label.
        """
        if not new_label:
            return

        label_predicate = URIRef(f"{PREFIX['rdfs']}label")
        new_literal = Literal(new_label, lang="en")

        old_labels = list(self.graph.objects(subject, label_predicate))
        for old_label in old_labels:
            old_label_str = str(old_label)
            if old_label_str.startswith("Q"):
                self.graph.remove((subject, label_predicate, old_label))

        self.graph.set((subject, label_predicate, new_literal))
        self._record_triple_metric(subject, label_predicate, new_literal)

    def _get_best_label(self, subject):
        """
        Return the best available label for an entity.
        """
        label_predicate = URIRef(f"{PREFIX['rdfs']}label")
        labels = [str(label) for label in self.graph.objects(subject, label_predicate)]

        for label in labels:
            if not label.startswith("Q"):
                return label

        return labels[0] if labels else None

    def _get_display_name(self, q_code: str):
        """
        Return the best display name for a Q-code and repair bad labels if needed.
        """
        subject = URIRef(f"{PREFIX['wd']}{q_code}")
        label = self._get_best_label(subject)

        if not label or label == q_code or label.startswith("Q"):
            fetched_label = self.linker.get_entity_label(q_code, force_refresh=True)

            if fetched_label and fetched_label != q_code:
                self._replace_label(subject, fetched_label)
                return fetched_label

        return label if label else q_code

    def _get_uri_display_name(self, subject):
        """
        Return a readable name for any URI in the graph.
        """
        name = self.graph.value(subject, URIRef(f"{PREFIX['scho']}name"))
        if name:
            return str(name)

        label = self._get_best_label(subject)
        if label:
            return label

        description = self.graph.value(subject, URIRef(f"{PREFIX['scho']}description"))
        if description:
            return str(description)

        subject_id = str(subject).rstrip("/").split("/")[-1]

        if subject_id.startswith("Q"):
            return self._get_display_name(subject_id)

        return subject_id

    # ---------------- GRAPH REFRESH HELPERS ---------------- #

    def _remove_existing_property_links(self, subject, property_names):
        """
        Remove all existing object links for the given schema.org-style properties.
        """
        for prop_name in property_names:
            predicate = URIRef(f"{PREFIX['scho']}{prop_name}")
            for obj in list(self.graph.objects(subject, predicate)):
                self.graph.remove((subject, predicate, obj))

    def _remove_linked_album_dates(self, subject):
        """
        Remove publication_date literals from albums currently linked to the group.
        """
        album_predicate = URIRef(f"{PREFIX['scho']}album")
        date_predicate = URIRef(f"{PREFIX['scho']}publication_date")

        for album_obj in list(self.graph.objects(subject, album_predicate)):
            for old_date in list(self.graph.objects(album_obj, date_predicate)):
                self.graph.remove((album_obj, date_predicate, old_date))

    # ---------------- TRAVERSAL ---------------- #

    def expand(self, q_code: str, entity_type: str = "Person", depth: int = 1, force_refresh: bool = False):
        """
        Recursively expand an entity.
        """
        if depth == 0:
            return False

        if q_code in self.visited:
            return False

        if entity_type is None:
            return False

        if entity_type == "Person":
            if q_code not in self.validation_cache:
                self.validation_cache[q_code] = validate_artist(q_code)

            if not self.validation_cache[q_code]:
                print(f"Skipping invalid artist: {q_code}")
                return False

        print(f"[Depth {depth}] Expanding {q_code} ({entity_type})")
        self.visited.add(q_code)

        wd_type = self.schema_to_wd_type.get(entity_type)
        if wd_type is None:
            print(f"Unsupported entity type: {entity_type}")
            return False

        cache_key = (q_code, entity_type)

        if not force_refresh and cache_key in self.entity_cache:
            label, attributes = self.entity_cache[cache_key]
            print(f"Using cached data for {q_code}")
        else:
            label, attributes = self.linker.get_wikidata_entity(q_code, wd_type)

            if label or any(attributes.values()):
                self.entity_cache[cache_key] = (label, attributes)

        if not label:
            existing_label = self._get_best_label(URIRef(f"{PREFIX['wd']}{q_code}"))
            if existing_label:
                label = existing_label

        if not label and not any(attributes.values()):
            print(f"No data returned for {q_code}")
            return False

        if not label:
            label = q_code

        self.add_entity_to_graph(q_code, label, entity_type, attributes)

        for prop, values in attributes.items():
            next_type = self.get_type_from_property(prop)

            for value in values:
                if not isinstance(value, dict):
                    continue

                if not next_type:
                    continue

                print(f" -> {prop} -> {value['qcode']} ({next_type})")

                if next_type in self.schema_to_wd_type:
                    self.expand(value["qcode"], next_type, depth - 1, force_refresh=force_refresh)

        return True

    # ---------------- JSON TRAVERSAL ---------------- #

    def format_entity(self, q_code: str, entity_type: str):
        """
        Convert one graph entity into the JSON structure used by the frontend.
        """
        if entity_type == "Artefact":
            subject = self._get_artefact_subject(q_code)
            if not subject:
                return None
            return self._format_artefact(subject, q_code)

        name = self._get_display_name(q_code)
        subject = URIRef(f"{PREFIX['wd']}{q_code}")

        if entity_type == "MusicGroup":
            return self._format_music_group(subject, q_code, name)

        if entity_type == "Person":
            return self._format_person(subject, q_code, name)

        if entity_type == "MusicAlbum":
            return self._format_music_album(subject, q_code, name)

        return None

    def _get_artefact_subject(self, artefact_id):
        """Find an artefact URI in the graph using its stored identifier."""
        identifier_predicate = URIRef(f"{PREFIX['scho']}identifier")

        for subject in self.graph.subjects(identifier_predicate, Literal(artefact_id)):
            return subject

        fallback = URIRef(f"http://radio.liv.ac.uk/bme/HumanMadeObject/{artefact_id}")
        if (fallback, None, None) in self.graph:
            return fallback

        return None

    def _get_zone_name(self, zone_uri):
        """Format an exhibition zone as a simple display string."""
        if not zone_uri:
            return None

        zone_id = str(zone_uri).rstrip("/").split("/")[-1]
        zone_name = self.graph.value(zone_uri, URIRef(f"{PREFIX['scho']}name"))

        if not zone_name:
            zone_name = self.graph.value(zone_uri, URIRef(f"{PREFIX['rdfs']}label"))

        if zone_name:
            return str(zone_name)

        if zone_id.startswith("Zone"):
            return zone_id.replace("Zone", "Zone ")

        return zone_id

    def _entity_exists_in_json(self, q_code, entity_type):
        """Check whether a Q-code exists in the JSON file for an entity type."""
        file_stub = ENTITY_FILE_STUBS.get(entity_type)
        if not file_stub:
            return False

        file_path = self.traversaljson_path / f"{file_stub}_data.json"

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except Exception:
            data = []

        if not isinstance(data, list):
            return False

        for item in data:
            if isinstance(item, dict) and item.get("id") == q_code:
                return True

        return False

    def _album_exists_in_group_json(self, q_code):
        """Check whether an album is already listed inside a music group JSON file."""
        file_path = self.traversaljson_path / "musicgroup_data.json"

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except Exception:
            data = []

        if not isinstance(data, list):
            return False

        for group in data:
            if not isinstance(group, dict):
                continue

            for album in group.get("albums", []):
                if isinstance(album, dict) and album.get("id") == q_code:
                    return True

        return False

    def _get_about_entity_type(self, subject):
        """
        Return the frontend entity type for an artefact about-link.

        Artefact about-links are only useful to the graph when they point to
        an entity we actually display: artists, music groups, or albums.
        Anything else is returned as None and filtered out by _format_artefact.
        """
        if str(subject).startswith(PREFIX["wd"]):
            q_code = str(subject).split("/")[-1]

            # Prefer saved display JSON because it reflects what the UI can open.
            for entity_type in DISPLAY_TYPE_LOOKUP_ORDER:
                if self._entity_exists_in_json(q_code, entity_type):
                    return entity_type

            # Albums are sometimes stored as child nodes inside group JSON.
            if self._album_exists_in_group_json(q_code):
                return "MusicAlbum"

        for schema_type in DISPLAY_TYPE_LOOKUP_ORDER:
            rdf_type = URIRef(f"{PREFIX['scho']}{schema_type}")

            if (subject, RDF.type, rdf_type) in self.graph:
                return schema_type

        return None

    def _get_related_artefacts(self, q_code):
        """Return artefacts that are about a Wikidata entity."""
        results = []
        target = URIRef(f"{PREFIX['wd']}{q_code}")
        about_predicate = URIRef(f"{PREFIX['scho']}about")
        name_predicate = URIRef(f"{PREFIX['scho']}name")

        for artefact in self.graph.subjects(about_predicate, target):
            artefact_id = self.graph.value(artefact, URIRef(f"{PREFIX['scho']}identifier"))
            if not artefact_id:
                artefact_id = str(artefact).rstrip("/").split("/")[-1]

            artefact_name = self.graph.value(artefact, name_predicate)
            if not artefact_name:
                artefact_name = self.graph.value(artefact, URIRef(f"{PREFIX['scho']}description"))

            if artefact_id and artefact_name:
                results.append({
                    "id": str(artefact_id),
                    "name": str(artefact_name)
                })

        results.sort(key=lambda item: item["name"].lower())
        return results

    def _format_artefact(self, subject, artefact_id):
        """Format a BME artefact into the JSON structure used by the frontend."""
        name = self.graph.value(subject, URIRef(f"{PREFIX['scho']}name"))
        image = self.graph.value(subject, URIRef(f"{PREFIX['scho']}image"))
        zone = self.graph.value(subject, URIRef(f"{PREFIX['scho']}isPartOf"))
        item_location = self.graph.value(subject, URIRef(f"{PREFIX['scho']}itemLocation"))

        allowed_about_types = ALLOWED_ARTEFACT_ABOUT_TYPES
        about_items = []

        for obj in self.graph.objects(subject, URIRef(f"{PREFIX['scho']}about")):
            if not isinstance(obj, URIRef):
                continue

            linked_type = self._get_about_entity_type(obj)
            if linked_type not in allowed_about_types:
                continue

            linked_id = str(obj).rstrip("/").split("/")[-1]
            linked_name = self._get_uri_display_name(obj)

            about_items.append({
                "id": linked_id,
                "name": linked_name,
                "type": linked_type
            })

        about_items.sort(key=lambda item: (item["type"], item["name"].lower()))

        artefact = {
            "id": str(artefact_id),
            "name": str(name) if name else str(artefact_id),
            "about": about_items,
            "zone": self._get_zone_name(zone),
            "item_location": str(item_location) if item_location else None
        }

        if image:
            artefact["image"] = str(image)

        return {key: value for key, value in artefact.items() if value is not None}

    def _format_music_group(self, subject, q_code, name):
        """
        Format a MusicGroup entity into the JSON structure used by the frontend.
        """
        def extract_list(predicate):
            results = []

            for obj in self.graph.objects(subject, predicate):
                if isinstance(obj, URIRef):
                    linked_q = str(obj).split("/")[-1]
                    linked_name = self._get_display_name(linked_q)

                    results.append({
                        "id": linked_q,
                        "name": linked_name
                    })

            return results

        members = extract_list(URIRef(f"{PREFIX['scho']}has_member"))
        genres = extract_list(URIRef(f"{PREFIX['scho']}genre"))

        albums = []
        for obj in self.graph.objects(subject, URIRef(f"{PREFIX['scho']}album")):
            if isinstance(obj, URIRef):
                album_q = str(obj).split("/")[-1]
                album_name = self._get_display_name(album_q)
                date = self.graph.value(obj, URIRef(f"{PREFIX['scho']}publication_date"))

                year_obj = None
                sort_year = 9999

                if date:
                    year = str(date)[:4]
                    if year.isdigit():
                        sort_year = int(year)

                    year_obj = {
                        "id": f"dt_{year}",
                        "name": year,
                        "value": year
                    }

                albums.append({
                    "id": album_q,
                    "name": album_name,
                    "year": year_obj,
                    "_sort_year": sort_year
                })

        albums.sort(key=lambda x: (x["_sort_year"], x["name"].lower()))

        for album in albums:
            album.pop("_sort_year", None)

        inception = self.graph.value(subject, URIRef(f"{PREFIX['scho']}inception"))

        est_year = None
        if inception:
            year = str(inception)[:4]
            est_year = {
                "id": f"dt_{year}",
                "name": year,
                "value": year
            }

        result = {
            "id": q_code,
            "name": name,
            "members": members,
            "est_year": est_year,
            "genres": genres,
            "albums": albums
        }

        artefacts = self._get_related_artefacts(q_code)
        if artefacts:
            result["artefacts"] = artefacts

        return result

    def _format_music_album(self, subject, q_code, name):
        """
        Format a MusicAlbum entity into the JSON structure used by the frontend.
        """
        def extract_list(predicate):
            results = []

            for obj in self.graph.objects(subject, predicate):
                if isinstance(obj, URIRef):
                    linked_q = str(obj).split("/")[-1]
                    linked_name = self._get_display_name(linked_q)

                    results.append({
                        "id": linked_q,
                        "name": linked_name
                    })

            return results

        artists = extract_list(URIRef(f"{PREFIX['scho']}artist"))
        genres = extract_list(URIRef(f"{PREFIX['scho']}genre"))
        date = self.graph.value(subject, URIRef(f"{PREFIX['scho']}publication_date"))

        year_obj = None
        if date:
            year = str(date)[:4]
            if year:
                year_obj = {
                    "id": f"dt_{year}",
                    "name": year,
                    "value": year
                }

        result = {
            "id": q_code,
            "name": name,
            "artists": artists,
            "genres": genres,
            "year": year_obj
        }

        artefacts = self._get_related_artefacts(q_code)
        if artefacts:
            result["artefacts"] = artefacts

        return result

    def _format_person(self, subject, q_code, name):
        """
        Format a Person entity into the JSON structure used by the frontend.
        """
        def extract_list(predicate):
            results = []

            for obj in self.graph.objects(subject, predicate):
                if isinstance(obj, URIRef):
                    linked_q = str(obj).split("/")[-1]
                    linked_name = self._get_display_name(linked_q)

                    results.append({
                        "id": linked_q,
                        "name": linked_name
                    })

            return results

        memberships = extract_list(URIRef(f"{PREFIX['scho']}member_of"))
        instruments = extract_list(URIRef(f"{PREFIX['scho']}instrument"))

        dob = self.graph.value(subject, URIRef(f"{PREFIX['scho']}date_of_birth"))

        dob_date = None
        if dob:
            raw = str(dob)[:10]
            parts = raw.split("-")
            if len(parts) == 3:
                formatted = f"{parts[2]}/{parts[1]}/{parts[0]}"
                dob_date = {
                    "id": f"dt_{parts[2]}{parts[1]}{parts[0]}",
                    "name": formatted,
                    "value": formatted
                }

        result = {
            "id": q_code,
            "name": name,
            "dob_date": dob_date,
            "memberships": memberships,
            "instruments": instruments
        }

        artefacts = self._get_related_artefacts(q_code)
        if artefacts:
            result["artefacts"] = artefacts

        return result

    def expand_entity(self, q_code: str, entity_type: str = "Person", depth: int = 1, force_refresh: bool = False):
        """
        Expand entity and produce structured JSON output.
        """
        success = self.expand(q_code, entity_type, depth, force_refresh=force_refresh)

        if not success:
            print("Entity could not be enriched")
            return False

        if entity_type == "MusicGroup":
            self.cross_verification(entity_type, q_code)

        formatted = self.format_entity(q_code, entity_type)

        if not formatted:
            print("Unsupported entity type for formatting")
            return False

        self._save_split_json(entity_type, formatted)
        return True

    # ---------------- JSON SAVE ---------------- #

    def _save_split_json(self, type_key, entity_data):
        """
        Save JSON outputs into assets/entity/ folder.
        """
        file_stub = ENTITY_FILE_STUBS.get(type_key, type_key.lower())

        header_file = self.traversaljson_path / f"{file_stub}_header.json"
        data_file = self.traversaljson_path / f"{file_stub}_data.json"

        def load(path):
            if not path.exists():
                return []

            try:
                with open(path, "r", encoding="utf-8") as file:
                    loaded = json.load(file)
                    if isinstance(loaded, list):
                        return loaded
                    if isinstance(loaded, dict):
                        return [loaded]
                    return []
            except Exception:
                return []

        header_data = load(header_file)
        full_data = load(data_file)

        if type_key == "Person":
            header_entry = {
                "id": entity_data["id"],
                "name": entity_data["name"],
                "dob_date": entity_data.get("dob_date")
            }

        elif type_key == "MusicGroup":
            header_entry = {
                "id": entity_data["id"],
                "name": entity_data["name"],
                "est_year": entity_data.get("est_year")
            }

        elif type_key == "MusicAlbum":
            header_entry = {
                "id": entity_data["id"],
                "name": entity_data["name"],
                "year": entity_data.get("year")
            }

        elif type_key == "Artefact":
            header_entry = {
                "id": entity_data["id"],
                "name": entity_data["name"]
            }

        else:
            header_entry = None

        def merge_values(old_value, new_value, field_name=None):
            """
            Merge entity values.
            """
            if isinstance(old_value, dict) and isinstance(new_value, dict):
                merged = dict(old_value)
                for key, value in new_value.items():
                    if key in merged:
                        merged[key] = merge_values(merged[key], value, field_name=key)
                    else:
                        merged[key] = value
                return merged

            if isinstance(old_value, list) and isinstance(new_value, list):
                if field_name == "albums":
                    return list(new_value)

                if field_name == "genres":
                    return list(new_value)

                merged = list(old_value)
                seen = set()

                for item in merged:
                    if isinstance(item, dict):
                        item_id = item.get("id") or item.get("ID")
                        if item_id:
                            seen.add(("id", item_id))
                        elif "name" in item:
                            seen.add(("name", item.get("name")))
                    else:
                        seen.add(("raw", str(item)))

                for item in new_value:
                    if isinstance(item, dict):
                        item_id = item.get("id") or item.get("ID")
                        key = ("id", item_id) if item_id else ("name", item.get("name"))
                    else:
                        key = ("raw", str(item))

                    if key not in seen:
                        merged.append(item)
                        seen.add(key)

                return merged

            return new_value if new_value is not None else old_value

        def merge_entity(old_item, new_item):
            merged = dict(old_item)

            for key, value in new_item.items():
                if key in merged:
                    merged[key] = merge_values(merged[key], value, field_name=key)
                else:
                    merged[key] = value

            old_name = old_item.get("name")
            new_name = new_item.get("name")

            if isinstance(old_name, str) and isinstance(new_name, str):
                if old_name.startswith("Q") and new_name != old_name:
                    merged["name"] = new_name

            return merged

        def upsert(data_list, new_item):
            new_item_id = new_item.get("id") or new_item.get("ID")

            for index, item in enumerate(data_list):
                if not isinstance(item, dict):
                    continue

                item_id = item.get("id") or item.get("ID")
                if item_id and new_item_id and item_id == new_item_id:
                    data_list[index] = merge_entity(item, new_item)
                    return

            data_list.append(new_item)

        if header_entry:
            upsert(header_data, header_entry)

        upsert(full_data, entity_data)

        with open(header_file, "w", encoding="utf-8") as file:
            json.dump(header_data, file, indent=4)

        with open(data_file, "w", encoding="utf-8") as file:
            json.dump(full_data, file, indent=4)

        print(f"Saved split JSON -> {type_key} ({data_file})")

    # ---------------- GRAPH BUILDING ---------------- #

    def add_entity_to_graph(self, q_code, label, entity_type, attributes):
        """
        Insert entity and relationships into the RDF graph.
        """
        subject = URIRef(f"{PREFIX['wd']}{q_code}")

        schema_key = self.entity_type_to_schema_key.get(entity_type)
        schema_type = SCHEMA_TYPES.get(schema_key) if schema_key else None

        if schema_type:
            self._add_triple(
                subject,
                RDF.type,
                URIRef(f"{PREFIX['scho']}{schema_type}")
            )

        self._replace_label(subject, label)

        if entity_type == "MusicGroup":
            refresh_props = []
            if "album" in attributes:
                self._remove_linked_album_dates(subject)
                refresh_props.append("album")
            if "genre" in attributes:
                refresh_props.append("genre")
            if refresh_props:
                self._remove_existing_property_links(subject, refresh_props)

        for prop, values in attributes.items():
            predicate = URIRef(f"{PREFIX['scho']}{prop}")

            for value in values:
                if isinstance(value, dict):
                    obj = URIRef(f"{PREFIX['wd']}{value['qcode']}")

                    self._add_triple(subject, predicate, obj)

                    if value.get("label"):
                        self._replace_label(obj, value["label"])

                    next_type = self.get_type_from_property(prop)
                    next_schema_key = self.entity_type_to_schema_key.get(next_type)
                    next_schema_type = SCHEMA_TYPES.get(next_schema_key) if next_schema_key else None

                    if next_schema_type:
                        self._add_triple(
                            obj,
                            RDF.type,
                            URIRef(f"{PREFIX['scho']}{next_schema_type}")
                        )

                    if value.get("date"):
                        self._add_triple(
                            obj,
                            URIRef(f"{PREFIX['scho']}publication_date"),
                            Literal(value["date"])
                        )

                else:
                    self._add_triple(subject, predicate, Literal(value))

    def _add_triple(self, subject, predicate, obj):
        """
        Add a triple only if it is not already present, then record it for metrics.
        """
        triple = (subject, predicate, obj)

        if triple not in self.graph:
            self.graph.add(triple)
            self._record_triple_metric(subject, predicate, obj)

    # ---------------- TYPE MAPPING ---------------- #

    def get_type_from_property(self, prop):
        """
        Map property names to entity types for traversal.
        """
        return {
            "has_member": "Person",
            "member_of": "MusicGroup",
            "genre": "MusicGenre",
            "album": "MusicAlbum",
            "influenced_by": "Person",
            "instrument": "MusicInstrument"
        }.get(prop)

    # ---------------- CROSS VERIFICATION ---------------- #

    def cross_verification(self, entity_type, q_code):
        """
        Ensure group members are also stored as Person entities.
        """
        if entity_type != "MusicGroup":
            return

        members = self.graph.objects(
            URIRef(f"{PREFIX['wd']}{q_code}"),
            URIRef(f"{PREFIX['scho']}has_member")
        )

        person_file = self.traversaljson_path / "person_data.json"

        try:
            with open(person_file, "r", encoding="utf-8") as file:
                existing = json.load(file)
        except Exception:
            existing = []

        existing_ids = {
            (entry.get("id") or entry.get("ID"))
            for entry in existing
            if isinstance(entry, dict)
        }

        for member in tqdm(members, desc="Cross-verifying members"):
            member_q = str(member).split("/")[-1]

            if member_q not in self.validation_cache:
                self.validation_cache[member_q] = validate_artist(member_q)

            if not self.validation_cache[member_q]:
                continue

            if member_q in existing_ids:
                continue

            if member_q in self.visited:
                continue

            print(f"Adding missing member {member_q}")
            self.expand_entity(member_q, "Person", depth=1)

    # ---------------- ARTEFACT EXPORT ---------------- #

    def _append_artefacts_to_entity_json(self, artefact_links_by_entity):
        """
        Add lightweight artefact links to existing display entity JSON files.
        """
        if not artefact_links_by_entity:
            return 0

        file_names = [
            f"{ENTITY_FILE_STUBS[entity_type]}_data.json"
            for entity_type in DISPLAY_TYPE_LOOKUP_ORDER
            if entity_type in ENTITY_FILE_STUBS
        ]
        updated_count = 0

        for file_name in file_names:
            file_path = self.traversaljson_path / file_name

            if not file_path.exists():
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
            except Exception:
                continue

            if not isinstance(data, list):
                continue

            file_changed = False

            for entity in data:
                if not isinstance(entity, dict):
                    continue

                entity_id = entity.get("id") or entity.get("ID")
                if not entity_id or entity_id not in artefact_links_by_entity:
                    continue

                existing_artefacts = entity.get("artefacts", [])
                if not isinstance(existing_artefacts, list):
                    existing_artefacts = []

                merged = []
                seen = set()

                for artefact in existing_artefacts:
                    if not isinstance(artefact, dict):
                        continue

                    artefact_id = artefact.get("id")
                    artefact_name = artefact.get("name")

                    if not artefact_id or not artefact_name:
                        continue

                    merged.append({
                        "id": artefact_id,
                        "name": artefact_name
                    })
                    seen.add(artefact_id)

                for artefact in artefact_links_by_entity[entity_id]:
                    artefact_id = artefact.get("id")

                    if not artefact_id or artefact_id in seen:
                        continue

                    merged.append({
                        "id": artefact_id,
                        "name": artefact.get("name") or artefact_id
                    })
                    seen.add(artefact_id)
                    file_changed = True

                merged.sort(key=lambda item: item["name"].lower())
                entity["artefacts"] = merged
                updated_count += 1

            if file_changed:
                with open(file_path, "w", encoding="utf-8") as file:
                    json.dump(data, file, indent=4)

        return updated_count

    def export_artefacts(self):
        """
        Extract BME artefacts from the local TTL graph and save them as JSON.
        """
        artefact_type = URIRef("http://www.cidoc-crm.org/cidoc-crm/E22_Human-Made_Object")
        artefact_links_by_entity = {}
        saved = 0

        for subject in sorted(self.graph.subjects(RDF.type, artefact_type), key=lambda item: str(item)):
            artefact_id = self.graph.value(subject, URIRef(f"{PREFIX['scho']}identifier"))
            if not artefact_id:
                artefact_id = str(subject).rstrip("/").split("/")[-1]

            formatted = self._format_artefact(subject, str(artefact_id))
            self._save_split_json("Artefact", formatted)
            saved += 1

            artefact_link = {
                "id": formatted["id"],
                "name": formatted["name"]
            }

            for related_entity in formatted.get("about", []):
                related_id = related_entity.get("id")
                related_type = related_entity.get("type")

                if not related_id:
                    continue

                if related_type not in ALLOWED_ARTEFACT_ABOUT_TYPES:
                    continue

                if related_id not in artefact_links_by_entity:
                    artefact_links_by_entity[related_id] = []

                artefact_links_by_entity[related_id].append(artefact_link)

        updated_entities = self._append_artefacts_to_entity_json(artefact_links_by_entity)

        print(f"Exported {saved} artefacts to JSON")
        print(f"Updated artefact links for {updated_entities} display entity records")
        return saved

    # ---------------- SAVE ---------------- #

    def save(self):
        """Save KG and cache."""
        self.graph.serialize(destination=str(self.ttl_path), format="ttl")
        self._save_cache()
        print("KG saved.")


## ---------------- MAIN ---------------- ##
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    ttl_path = project_root / "assets" / "graphs" / "bme_knowledge_graph.ttl"

    traverser = KGTraverser(ttl_path)

    action = questionary.select(
        "Action:",
        choices=["Expand Wikidata entity", "Export artefacts"]
    ).ask()

    if action == "Export artefacts":
        traverser.export_artefacts()
        traverser.save()
    else:
        q_code = questionary.text("Enter Q-code:").ask()

        entity_type = questionary.select(
            "Entity type:",
            choices=["Person", "MusicGroup", "MusicAlbum", "MusicRecording"]
        ).ask()

        depth = int(questionary.text("Depth (1-3):").ask())

        traverser.expand_entity(q_code, entity_type, depth)
        traverser.save()
