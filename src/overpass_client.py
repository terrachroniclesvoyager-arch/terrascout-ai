"""
Shared Overpass API client with automatic failover between servers.
Used by: osm_explorer, landuse_explorer, water_explorer, archaeology, remote_explorer.
"""

import time
import requests

OVERPASS_SERVERS = [
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

_HEADERS = {"User-Agent": "TerraScoutAI/1.0"}


def query_overpass(query: str, timeout: int = 120) -> dict | None:
    """
    Send an Overpass QL query, trying each server in turn.

    Returns:
        Parsed JSON dict on success, or None if all servers fail.
        On total failure, the last error message is stored in the
        returned dict as {"_error": "message"}.
    """
    last_error = None
    backoff = 1  # seconds, doubles on 429
    for server in OVERPASS_SERVERS:
        try:
            resp = requests.post(
                server,
                data={"data": query.strip()},
                timeout=timeout,
                headers=_HEADERS,
            )
            resp.raise_for_status()
            try:
                return resp.json()
            except (ValueError, requests.exceptions.JSONDecodeError):
                last_error = f"Invalid JSON from {server.split('/')[2]}"
                continue
        except requests.exceptions.Timeout:
            last_error = f"Timeout from {server.split('/')[2]}"
            continue
        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response is not None else "?"
            last_error = f"{code} from {server.split('/')[2]}"
            if code == 429:
                time.sleep(min(backoff, 8))  # Exponential backoff, cap at 8s
                backoff *= 2
                continue
            continue
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            continue
        except Exception as e:
            last_error = str(e)
            continue

    return {"_error": last_error or "All Overpass servers unreachable"}
