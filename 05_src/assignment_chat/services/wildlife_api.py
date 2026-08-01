# Service 1 (API-backed): looks up animal facts from the iNaturalist
# API (https://api.inaturalist.org/v1/) -- free, no key needed.
#
# This only returns a plain dict of facts, not a finished sentence.
# app.py hands that dict to the model as a tool result, and the model
# (per the system prompt) rewrites it in its own words instead of
# printing it verbatim.

import re
import requests

INATURALIST_URL = "https://api.inaturalist.org/v1/taxa"
TIMEOUT_SECONDS = 8

WILDLIFE_LOOKUP_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "wildlife_lookup",
        "description": (
            "Look up real facts about a specific animal species from a "
            "live wildlife database (iNaturalist). Use this when a "
            "visitor names a specific animal and you want verified "
            "info instead of guessing."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "animal_name": {
                    "type": "string",
                    "description": "Common or scientific name of the animal, e.g. 'snow leopard'.",
                }
            },
            "required": ["animal_name"],
        },
    },
}


def strip_html(text):
    """iNaturalist's wikipedia_summary field has HTML tags in it."""
    if not text:
        return ""
    no_tags = re.sub("<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", no_tags).strip()


def wildlife_lookup(animal_name):
    if not animal_name or not animal_name.strip():
        return {"error": "No animal name was given."}

    try:
        response = requests.get(
            INATURALIST_URL,
            params={"q": animal_name.strip(), "rank": "species", "per_page": 1},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        return {"error": "Couldn't reach the wildlife database (" + type(e).__name__ + ")."}
    except ValueError:
        return {"error": "The wildlife database sent back something I couldn't read."}

    results = data.get("results", [])
    if len(results) == 0:
        return {"error": "No species found matching '" + animal_name + "'."}

    taxon = results[0]

    conservation = taxon.get("conservation_status")
    status = conservation.get("status_name", "not assessed") if conservation else "not assessed"

    common_name = taxon.get("preferred_common_name") or taxon.get("name")
    summary = strip_html(taxon.get("wikipedia_summary"))[:800]

    return {
        "query": animal_name,
        "matched_name": taxon.get("name"),
        "common_name": common_name,
        "rank": taxon.get("rank"),
        "conservation_status": status,
        "wikipedia_summary": summary,
        "observations_count": taxon.get("observations_count"),
        "wikipedia_url": taxon.get("wikipedia_url"),
    }
