from rdflib import URIRef, RDF
import time
import os

from kg_traversal import KGTraverser
from macros import PREFIX


## ---------------- BULK ENRICHER ---------------- ##
class KGBulkEnricher:
    def __init__(self, ttl_path):
        """
        Initialise the bulk enricher with one traverser instance.

        Args:
            ttl_path (str | Path): Path to the TTL knowledge graph file.
        """
        self.traverser = KGTraverser(ttl_path)
        self.traverser.is_full_expansion = True

    def _get_entities_by_type(self, rdf_type):
        """
        Return all Q-codes in the graph with the given RDF type.

        Args:
            rdf_type (str): RDF type name such as "Person" or "MusicGroup".
        """
        return sorted(set(
            str(subject).split("/")[-1]
            for subject in self.traverser.graph.subjects(
                RDF.type,
                URIRef(f"{PREFIX['scho']}{rdf_type}")
            )
        ))

    def get_all_targets(self):
        """
        Collect all base Person and MusicGroup entities from the graph.
        """
        persons = self._get_entities_by_type("Person")
        groups = self._get_entities_by_type("MusicGroup")

        print(f"Found {len(persons)} persons")
        print(f"Found {len(groups)} groups")

        return (
            [(q_code, "Person") for q_code in persons] +
            [(q_code, "MusicGroup") for q_code in groups]
        )

    def enrich_all(self, depth=1):
        """
        Enrich all base Person and MusicGroup entities.

        Args:
            depth (int): Traversal depth for each entity.
        """
        self.traverser.visited = set()
        self.traverser.clear_empty_cache_entries()

        targets = self.get_all_targets()
        print(f"Total targets: {len(targets)}")

        failed = []
        processed = 0
        successful = 0

        for q_code, entity_type in targets:
            print(f"\nEnriching {q_code} ({entity_type})")

            try:
                success = self.traverser.expand_entity(
                    q_code,
                    entity_type,
                    depth=depth,
                    force_refresh=False
                )

                if not success:
                    print(f"No usable enrichment returned for {q_code}")
                    failed.append((q_code, entity_type))
                    continue

            except Exception as e:
                print(f"Failed: {q_code} | {e}")
                failed.append((q_code, entity_type))
                continue

            processed += 1
            successful += 1
            print(f"Progress: {processed}/{len(targets)}")

            if processed % 15 == 0:
                print("Saving progress")
                self.traverser.save()
                time.sleep(5)

            time.sleep(0.2)

        if failed:
            print(f"\nRetrying {len(failed)} failed entities")
            time.sleep(10)

            retry_failed = []

            for q_code, entity_type in failed:
                print(f"Retrying {q_code} ({entity_type})")

                try:
                    success = self.traverser.expand_entity(
                        q_code,
                        entity_type,
                        depth=depth,
                        force_refresh=True
                    )

                    if not success:
                        print(f"Still no usable data for {q_code}")
                        retry_failed.append((q_code, entity_type))

                except Exception as e:
                    print(f"Still failed: {q_code} | {e}")
                    retry_failed.append((q_code, entity_type))

                time.sleep(0.5)

            failed = retry_failed

        print("\nExporting artefacts")
        try:
            self.traverser.export_artefacts()
        except Exception as e:
            print(f"Artefact export failed: {e}")

        print("\nEnrichment complete")
        print(f"Successful enrichments: {successful}")
        print(f"Remaining failures: {len(failed)}")

        if failed:
            print("Failed entities:")
            for q_code, entity_type in failed:
                print(f" - {q_code} ({entity_type})")

        self.traverser.save()


## ---------------- MAIN ---------------- ##
if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ttl_path = os.path.join(project_root, "assets", "graphs", "bme_knowledge_graph.ttl")

    enricher = KGBulkEnricher(ttl_path)
    enricher.enrich_all(depth=1)
