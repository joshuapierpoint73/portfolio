from typing import Optional
from rdflib import Graph, URIRef
from SPARQLWrapper import SPARQLWrapper, JSON
from urllib.error import HTTPError
from macros import WIKIDATA_PROPERTIES, MAIN_ALBUM_LIMIT, MAIN_GENRE_LIMIT, PREFIX
import time

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"


class QueryBuilder:
    """
    Build SPARQL queries used to fetch entity data from Wikidata.
    """

    PREFIX = """
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX wikibase: <http://wikiba.se/ontology#>
    """

    @staticmethod
    def build_query(q_code: str, properties: dict):
        optional_blocks = []

        for name, pid in properties.items():
            if name == "album":
                continue

            optional_blocks.append(f"""
            OPTIONAL {{
                wd:{q_code} wdt:{pid} ?{name} .
                OPTIONAL {{
                    ?{name} rdfs:label ?{name}Label .
                    FILTER(LANG(?{name}Label) = "en")
                }}
            }}
            """)

        return f"""
        {QueryBuilder.PREFIX}

        SELECT DISTINCT * WHERE {{
            wd:{q_code} rdfs:label ?label .
            FILTER(LANG(?label) = "en")

            {"".join(optional_blocks)}
        }}
        LIMIT 200
        """

    @staticmethod
    def build_album_query_discography(q_code: str):
        return f"""
        {QueryBuilder.PREFIX}

        SELECT DISTINCT ?album ?albumLabel ?albumDate ?form ?formLabel ?sitelinks ?isNotable
        WHERE {{
            wd:{q_code} wdt:P358 ?discography .
            ?discography wdt:P2354 ?albumList .
            ?albumList wdt:P527 ?album .

            ?album wdt:P31 wd:Q482994 .

            OPTIONAL {{ ?album wdt:P577 ?albumDate . }}
            OPTIONAL {{ ?album wdt:P7937 ?form . }}
            OPTIONAL {{ ?album wikibase:sitelinks ?sitelinks . }}
            OPTIONAL {{ wd:{q_code} wdt:P800 ?album . BIND(true AS ?isNotable) }}

            OPTIONAL {{
                ?album rdfs:label ?albumLabel .
                FILTER(LANG(?albumLabel) = "en")
            }}

            OPTIONAL {{
                ?form rdfs:label ?formLabel .
                FILTER(LANG(?formLabel) = "en")
            }}
        }}
        LIMIT 120
        """

    @staticmethod
    def build_album_query_notable(q_code: str):
        return f"""
        {QueryBuilder.PREFIX}

        SELECT DISTINCT ?album ?albumLabel ?albumDate ?form ?formLabel ?sitelinks ?isNotable
        WHERE {{
            wd:{q_code} wdt:P800 ?album .
            ?album wdt:P31 wd:Q482994 .

            OPTIONAL {{ ?album wdt:P577 ?albumDate . }}
            OPTIONAL {{ ?album wdt:P7937 ?form . }}
            OPTIONAL {{ ?album wikibase:sitelinks ?sitelinks . }}
            BIND(true AS ?isNotable)

            OPTIONAL {{
                ?album rdfs:label ?albumLabel .
                FILTER(LANG(?albumLabel) = "en")
            }}

            OPTIONAL {{
                ?form rdfs:label ?formLabel .
                FILTER(LANG(?formLabel) = "en")
            }}
        }}
        LIMIT 40
        """

    @staticmethod
    def build_album_query_direct(q_code: str):
        return f"""
        {QueryBuilder.PREFIX}

        SELECT DISTINCT ?album ?albumLabel ?albumDate ?form ?formLabel ?sitelinks ?isNotable
        WHERE {{
            ?album wdt:P175 wd:{q_code} .
            ?album wdt:P31 wd:Q482994 .

            OPTIONAL {{ ?album wdt:P577 ?albumDate . }}
            OPTIONAL {{ ?album wdt:P7937 ?form . }}
            OPTIONAL {{ ?album wikibase:sitelinks ?sitelinks . }}
            OPTIONAL {{ wd:{q_code} wdt:P800 ?album . BIND(true AS ?isNotable) }}

            OPTIONAL {{
                ?album rdfs:label ?albumLabel .
                FILTER(LANG(?albumLabel) = "en")
            }}

            OPTIONAL {{
                ?form rdfs:label ?formLabel .
                FILTER(LANG(?formLabel) = "en")
            }}
        }}
        LIMIT 80
        """

    @staticmethod
    def build_album_genres_query(album_qcodes):
        if not album_qcodes:
            return None

        values = " ".join(f"wd:{qcode}" for qcode in album_qcodes)

        return f"""
        {QueryBuilder.PREFIX}

        SELECT DISTINCT ?album ?genre ?genreLabel ?genreSitelinks
        WHERE {{
            VALUES ?album {{ {values} }}
            ?album wdt:P136 ?genre .

            OPTIONAL {{
                ?genre rdfs:label ?genreLabel .
                FILTER(LANG(?genreLabel) = "en")
            }}

            OPTIONAL {{
                ?genre wikibase:sitelinks ?genreSitelinks .
            }}
        }}
        """

    @staticmethod
    def build_entity_metadata_query(qcodes):
        if not qcodes:
            return None

        values = " ".join(f"wd:{qcode}" for qcode in qcodes)

        return f"""
        {QueryBuilder.PREFIX}

        SELECT DISTINCT ?entity ?entityLabel ?sitelinks
        WHERE {{
            VALUES ?entity {{ {values} }}

            OPTIONAL {{
                ?entity rdfs:label ?entityLabel .
                FILTER(LANG(?entityLabel) = "en")
            }}

            OPTIONAL {{
                ?entity wikibase:sitelinks ?sitelinks .
            }}
        }}
        """

    @staticmethod
    def build_label_query(q_code: str):
        return f"""
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT ?label WHERE {{
            wd:{q_code} rdfs:label ?label .
        }}
        ORDER BY
            IF(LANG(?label) = "en", 0,
                IF(LANG(?label) = "en-gb", 1, 2))
        LIMIT 1
        """

    @staticmethod
    def build_property_query(q_code: str, pid: str):
        return f"""
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

        SELECT DISTINCT ?value ?valueLabel WHERE {{
            wd:{q_code} wdt:{pid} ?value .

            OPTIONAL {{
                ?value rdfs:label ?valueLabel .
                FILTER(LANG(?valueLabel) = "en")
            }}
        }}
        LIMIT 200
        """


class KGValidator:
    def __init__(self, ttl_path: str, q_code: Optional[str] = None):
        self.ttl_path = ttl_path
        self.q_code = q_code

    def validate_kg(self):
        """Check whether a Wikidata entity already exists in the RDF graph."""
        if not self.q_code:
            return False

        graph = Graph()

        try:
            graph.parse(self.ttl_path, format="ttl")
        except Exception as e:
            print(f"Could not validate KG file {self.ttl_path}: {e}")
            return False

        subject = URIRef(f"{PREFIX['wd']}{self.q_code}")
        return (subject, None, None) in graph


class KGLinker:
    """
    Run SPARQL queries and return structured Wikidata entity data.
    """

    last_request_time = 0
    min_interval = 1.0
    cooldown_until = 0

    def __init__(self):
        self.label_cache = {}

    def run_query(self, query):
        sparql = SPARQLWrapper(WIKIDATA_ENDPOINT)
        sparql.setTimeout(15)

        while True:
            try:
                now = time.time()

                if now < KGLinker.cooldown_until:
                    sleep_time = KGLinker.cooldown_until - now
                    print(f"Waiting for Wikidata cooldown: {sleep_time:.1f}s")
                    time.sleep(sleep_time)

                elapsed = now - KGLinker.last_request_time
                if elapsed < KGLinker.min_interval:
                    time.sleep(KGLinker.min_interval - elapsed)

                KGLinker.last_request_time = time.time()

                sparql.setQuery(query)
                sparql.setReturnFormat(JSON)
                return sparql.query().convert()

            except HTTPError as e:
                if e.code == 429:
                    cooldown = 15
                    print(f"Wikidata rate limit reached. Waiting {cooldown}s...")
                    KGLinker.cooldown_until = time.time() + cooldown
                    time.sleep(cooldown)
                else:
                    print(f"Wikidata HTTP error: {e}")
                    return None

            except Exception:
                return None

    def get_entity_label(self, q_code: str, force_refresh: bool = False):
        if not force_refresh and q_code in self.label_cache:
            cached = self.label_cache[q_code]
            if cached:
                return cached

        query = QueryBuilder.build_label_query(q_code)

        for _ in range(2):
            results = self.run_query(query)

            if not results:
                continue

            bindings = results.get("results", {}).get("bindings", [])
            if not bindings:
                continue

            label = bindings[0].get("label", {}).get("value")
            if label:
                self.label_cache[q_code] = label
                return label

        return None

    def _parse_property_rows(self, rows):
        values = []
        seen = set()

        for row in rows:
            if "value" not in row:
                continue

            raw_value = row["value"]["value"]

            if raw_value.startswith("http"):
                qcode_val = raw_value.split("/")[-1]

                if qcode_val in seen:
                    continue
                seen.add(qcode_val)

                value_label = row.get("valueLabel", {}).get("value")
                if not value_label:
                    value_label = self.get_entity_label(qcode_val)

                values.append({
                    "label": value_label,
                    "qcode": qcode_val,
                    "date": None
                })

            else:
                if raw_value not in values:
                    values.append(raw_value)

        return values

    def _fetch_entity_by_fallback(self, q_code: str, properties: dict):
        label = self.get_entity_label(q_code, force_refresh=True)
        attributes = {key: [] for key in properties.keys() if key != "album"}

        for prop_name, pid in properties.items():
            if prop_name == "album":
                continue

            property_query = QueryBuilder.build_property_query(q_code, pid)
            property_results = self.run_query(property_query)

            if not property_results:
                continue

            rows = property_results.get("results", {}).get("bindings", [])
            attributes[prop_name] = self._parse_property_rows(rows)

        return label, attributes

    def _year_from_date(self, raw_date):
        if not raw_date:
            return None

        raw = str(raw_date)
        if len(raw) >= 4 and raw[:4].isdigit():
            return int(raw[:4])

        return None

    def _sitelinks_to_int(self, raw_sitelinks):
        if raw_sitelinks is None:
            return 0

        try:
            return int(str(raw_sitelinks))
        except Exception:
            return 0

    # ---------------- ALBUM RANKING ---------------- #

    def _is_excluded_album_form(self, form_label: str) -> bool:
        if not form_label:
            return False

        excluded_terms = {
            "live album",
            "compilation album",
            "greatest hits album",
            "remix album",
            "soundtrack album",
            "video album",
            "ep",
            "mixtape",
            "karaoke album",
            "spoken word album",
        }

        return form_label.lower().strip() in excluded_terms

    def _is_obviously_not_main_album_by_title(self, album_label: str) -> bool:
        if not album_label:
            return False

        label = album_label.lower().strip()

        blocked_fragments = [
            "music from the film",
            "best of",
            "greatest hits",
            "early years",
            "live at",
            "live ",
            " soundtrack",
            " remixes",
            " remix",
        ]

        return any(fragment in label for fragment in blocked_fragments)

    def _album_score(self, item: dict) -> int:
        score = 0

        form_label = (item.get("form_label") or "").lower().strip()
        sitelinks = self._sitelinks_to_int(item.get("sitelinks"))
        year = self._year_from_date(item.get("date"))

        if item.get("is_notable"):
            score += 120

        if form_label == "studio album":
            score += 60
        elif form_label == "album":
            score += 20

        score += min(sitelinks, 150)

        if year is not None and 1960 <= year <= 1995:
            score += 10

        return score

    def _filter_main_albums(self, album_rows, source_name):
        grouped = {}

        for row in album_rows:
            if "album" not in row:
                continue

            album_id = row["album"]["value"].split("/")[-1]

            if album_id not in grouped:
                grouped[album_id] = {
                    "qcode": album_id,
                    "label": None,
                    "date": None,
                    "form_label": None,
                    "sitelinks": 0,
                    "is_notable": False
                }

            item = grouped[album_id]

            if row.get("albumLabel", {}).get("value"):
                item["label"] = row["albumLabel"]["value"]

            album_date = row.get("albumDate", {}).get("value")
            if album_date and (item["date"] is None or album_date < item["date"]):
                item["date"] = album_date

            form_label = row.get("formLabel", {}).get("value")
            if form_label and not item["form_label"]:
                item["form_label"] = form_label

            sitelinks = row.get("sitelinks", {}).get("value")
            if sitelinks is not None:
                item["sitelinks"] = max(
                    self._sitelinks_to_int(item["sitelinks"]),
                    self._sitelinks_to_int(sitelinks)
                )

            if "isNotable" in row:
                item["is_notable"] = True

        filtered = []

        for item in grouped.values():
            if not item["label"]:
                item["label"] = self.get_entity_label(item["qcode"])

            if self._is_excluded_album_form(item["form_label"]):
                continue

            if self._is_obviously_not_main_album_by_title(item["label"]):
                continue

            filtered.append(item)

        filtered.sort(
            key=lambda x: (
                -self._album_score(x),
                -self._sitelinks_to_int(x.get("sitelinks")),
                self._year_from_date(x.get("date")) or 9999,
                (x.get("label") or "").lower()
            )
        )

        final = filtered[:MAIN_ALBUM_LIMIT]
        print(f"  Albums selected from {source_name}: {len(final)}")

        return [
            {
                "label": item["label"],
                "qcode": item["qcode"],
                "date": item["date"]
            }
            for item in final
        ]

    def _run_album_query(self, query, source_name):
        results = self.run_query(query)

        if not results:
            return []

        rows = results.get("results", {}).get("bindings", [])
        if not rows:
            return []

        return self._filter_main_albums(rows, source_name)

    def _fetch_albums_for_group(self, q_code: str):
        strategies = [
            ("discography", QueryBuilder.build_album_query_discography(q_code)),
            ("notable works", QueryBuilder.build_album_query_notable(q_code)),
            ("direct performer lookup", QueryBuilder.build_album_query_direct(q_code)),
        ]

        for source_name, query in strategies:
            albums = self._run_album_query(query, source_name)

            if albums:
                return albums

        print("  No suitable albums found.")
        return []

    # ---------------- GENRE RANKING ---------------- #

    def _fetch_entity_metadata(self, qcodes):
        metadata = {}

        if not qcodes:
            return metadata

        query = QueryBuilder.build_entity_metadata_query(qcodes)
        if not query:
            return metadata

        results = self.run_query(query)
        if not results:
            return metadata

        for row in results.get("results", {}).get("bindings", []):
            entity_uri = row.get("entity", {}).get("value")
            if not entity_uri:
                continue

            qcode = entity_uri.split("/")[-1]
            label = row.get("entityLabel", {}).get("value")
            sitelinks = self._sitelinks_to_int(row.get("sitelinks", {}).get("value"))

            metadata[qcode] = {
                "label": label,
                "sitelinks": sitelinks
            }

        return metadata

    def _fetch_album_genres(self, album_qcodes):
        counts = {}

        if not album_qcodes:
            return counts

        query = QueryBuilder.build_album_genres_query(album_qcodes)
        if not query:
            return counts

        results = self.run_query(query)
        if not results:
            return counts

        seen_pairs = set()

        for row in results.get("results", {}).get("bindings", []):
            album_uri = row.get("album", {}).get("value")
            genre_uri = row.get("genre", {}).get("value")

            if not album_uri or not genre_uri:
                continue

            album_q = album_uri.split("/")[-1]
            genre_q = genre_uri.split("/")[-1]
            pair = (album_q, genre_q)

            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            if genre_q not in counts:
                counts[genre_q] = {
                    "album_count": 0,
                    "label": row.get("genreLabel", {}).get("value"),
                    "sitelinks": self._sitelinks_to_int(row.get("genreSitelinks", {}).get("value"))
                }

            counts[genre_q]["album_count"] += 1

        return counts

    def _is_broad_genre(self, label: str) -> bool:
        """
        Broad genres are kept because they create useful links between bands.
        """
        if not label:
            return False

        broad_genres = {
            "rock music",
            "pop music",
            "popular music",
            "electronic music",
            "jazz",
            "blues",
            "soul music",
            "hip hop music",
            "folk music",
            "country music",
            "punk rock",
            "heavy metal",
            "reggae",
            "funk",
            "rhythm and blues",
            "dance music",
            "alternative rock",
            "indie rock",
            "hard rock",
            "progressive rock",
            "psychedelic rock",
        }

        return label.lower().strip() in broad_genres

    def _genre_specificity_bonus(self, label: str) -> int:
        """
        Specific genres are still useful, but broad genres are prioritised
        because they improve graph connectivity.
        """
        if not label:
            return 0

        if len(label.split()) >= 2:
            return 8

        return 0

    def _genre_score(self, genre_item: dict) -> int:
        label = genre_item.get("label")
        score = 0

        if genre_item.get("is_direct_group_genre"):
            score += 120

        if self._is_broad_genre(label):
            score += 90

        score += 40 * genre_item.get("album_count", 0)
        score += min(self._sitelinks_to_int(genre_item.get("sitelinks")), 60)
        score += self._genre_specificity_bonus(label)

        return score

    def _rank_group_genres(self, direct_genres, selected_albums):
        genre_map = {}

        for genre in direct_genres or []:
            if not isinstance(genre, dict):
                continue

            qcode = genre.get("qcode")
            if not qcode:
                continue

            genre_map[qcode] = {
                "qcode": qcode,
                "label": genre.get("label"),
                "sitelinks": 0,
                "album_count": 0,
                "is_direct_group_genre": True
            }

        metadata = self._fetch_entity_metadata(list(genre_map.keys()))

        for qcode, meta in metadata.items():
            if qcode in genre_map:
                if meta.get("label"):
                    genre_map[qcode]["label"] = meta["label"]

                genre_map[qcode]["sitelinks"] = max(
                    genre_map[qcode]["sitelinks"],
                    meta.get("sitelinks", 0)
                )

        album_qcodes = [
            album["qcode"]
            for album in selected_albums
            if isinstance(album, dict) and album.get("qcode")
        ]

        album_genres = self._fetch_album_genres(album_qcodes)

        for qcode, data in album_genres.items():
            if qcode not in genre_map:
                genre_map[qcode] = {
                    "qcode": qcode,
                    "label": data.get("label"),
                    "sitelinks": data.get("sitelinks", 0),
                    "album_count": data.get("album_count", 0),
                    "is_direct_group_genre": False
                }
            else:
                genre_map[qcode]["album_count"] = data.get("album_count", 0)
                genre_map[qcode]["sitelinks"] = max(
                    genre_map[qcode]["sitelinks"],
                    data.get("sitelinks", 0)
                )

        ranked = [
            genre
            for genre in genre_map.values()
            if genre.get("label")
        ]

        ranked.sort(
            key=lambda genre: (
                -self._genre_score(genre),
                -genre.get("album_count", 0),
                -self._sitelinks_to_int(genre.get("sitelinks")),
                genre.get("label", "").lower()
            )
        )

        broad_genres = [
            genre for genre in ranked
            if self._is_broad_genre(genre.get("label"))
        ]

        final = []

        # Always try to include one broad genre for graph-level connections.
        if broad_genres:
            final.append(broad_genres[0])

        # Fill the remaining slots using the best overall genres.
        for genre in ranked:
            if len(final) >= MAIN_GENRE_LIMIT:
                break

            if genre not in final:
                final.append(genre)

        print(f"  Genres selected: {len(final)}")

        return [
            {
                "label": genre["label"],
                "qcode": genre["qcode"],
                "date": None
            }
            for genre in final
        ]

    # ---------------- MAIN ENTITY FETCH ---------------- #

    def get_wikidata_entity(self, q_code: str, entity_type: str):
        properties = WIKIDATA_PROPERTIES.get(entity_type, {})

        if not properties:
            print(f"No property mapping found for {entity_type}")
            return None, {}

        print(f"Fetching {q_code} ({entity_type}) from Wikidata...")

        label = None
        attributes = {key: [] for key in properties.keys() if key != "album"}

        main_query = QueryBuilder.build_query(q_code, properties)
        results = self.run_query(main_query)

        rows = []
        if results:
            rows = results.get("results", {}).get("bindings", [])

        if rows:
            seen = set()

            for row in rows:
                if not label and "label" in row:
                    label = row["label"]["value"]

                for prop in attributes:
                    if prop not in row:
                        continue

                    value = row[prop]["value"]

                    if value.startswith("http"):
                        qcode_val = value.split("/")[-1]
                        key = (prop, qcode_val)

                        if key in seen:
                            continue
                        seen.add(key)

                        label_key = f"{prop}Label"
                        value_label = row.get(label_key, {}).get("value")

                        if not value_label:
                            value_label = self.get_entity_label(qcode_val)

                        attributes[prop].append({
                            "label": value_label,
                            "qcode": qcode_val,
                            "date": None
                        })

                    else:
                        if value not in attributes[prop]:
                            attributes[prop].append(value)

        else:
            print("  Main fetch returned no rows. Trying smaller fallback fetch...")
            label, attributes = self._fetch_entity_by_fallback(q_code, properties)

        attributes["album"] = []

        if entity_type == "group":
            attributes["album"] = self._fetch_albums_for_group(q_code)
            attributes["genre"] = self._rank_group_genres(
                attributes.get("genre", []),
                attributes["album"]
            )

        total_values = sum(len(values) for values in attributes.values())
        print(f"Finished {q_code}: label={label}, values={total_values}")

        if not label and total_values == 0:
            return None, {}

        return label, attributes
