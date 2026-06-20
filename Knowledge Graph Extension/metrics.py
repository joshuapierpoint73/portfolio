""" Metrics for the KG extension. """
import os
import json
import re
import time


WIKIDATA_QCODE_RE = re.compile(r"^https?://www\.wikidata\.org/entity/Q(\d+)$", re.IGNORECASE)
URI_RE = re.compile(r"^https?://", re.IGNORECASE)
METRIC_PATH_CACHE = None

def process_triple(s, p, o, filepath, full_expansion=False):
    """ Process a triple for metrics.

    Args:
        s (str): Subject.
        p (str): Predicate.
        o (str): Object.
        filepath (str): Path to the metrics JSON file.
        full_expansion (bool): Whether the expansion was full or partial. If it is a full one, wipe the JSON metric file.
    
    Returns:
        None
     
    """

    filepath = _ensure_metric_json()

    if full_expansion:
        os.system("cls")
        print("Full expansion detected. Resetting metrics.json\nPress CTRL + C to cancel.")
        time.sleep(5)
        with open(filepath, "w") as f:
            json.dump({}, f)

    try:
        with open(filepath, "r") as f:
            prev_data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        prev_data = {}
    
    updated_data = dict(prev_data)
    updated_data["total_triples"] = prev_data.get("total_triples", 0) + 1
    updated_data[f"{s}"] = prev_data.get(f"{s}", 0) + 1
    updated_data[f"{o}"] = prev_data.get(f"{o}", 0) + 1

    sorted_data = _sort_metric_data(updated_data)

    with open(filepath, "w") as f:
        json.dump(sorted_data, f, indent=4)


def _sort_metric_data(metrics):
    """Sort metrics by key groups so Q-code counters are listed first."""
    sorted_items = sorted(metrics.items(), key=_metric_sort_key)
    return dict(sorted_items)


def _metric_sort_key(item):
    """Sort order: total -> Wikidata Q-codes -> other URIs -> labels/dates."""
    key, value = item
    count = value if isinstance(value, int) else 0

    if key == "total_triples":
        return (0, 0, 0, "")

    match = WIKIDATA_QCODE_RE.match(key)
    if match:
        q_number = int(match.group(1))
        return (1, -count, q_number, key.lower())

    if URI_RE.match(key):
        return (2, -count, 0, key.lower())

    return (3, -count, 0, key.lower())


def _ensure_metric_json():
    """ Ensure the metric JSON file exists. """
    global METRIC_PATH_CACHE

    if METRIC_PATH_CACHE is not None:
        return METRIC_PATH_CACHE

    cwd = os.getcwd()
    metrics_dir = os.path.join(cwd, "assets", "metrics")
    os.makedirs(metrics_dir, exist_ok=True)
    metric_path = os.path.join(metrics_dir, "expansion_metrics.json")

    if not os.path.exists(metric_path):
        with open(metric_path, "w") as f:
            f.write("{}")
            print("Created expansion_metrics.json file.")

    else:
        print("expansion_metrics.json file already exists.")

    METRIC_PATH_CACHE = metric_path
    return metric_path
