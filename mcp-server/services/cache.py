import time
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Each entry: {"value": ..., "expires_at": float}
_store: dict = {}


def _key(*parts) -> str:
    return "|".join(str(p).lower().strip() for p in parts)


def get(key: str) -> Optional[Any]:
    entry = _store.get(key)
    if entry is None:
        return None
    if time.time() > entry["expires_at"]:
        del _store[key]
        logger.info("CACHE EXPIRED: %s", key)
        return None
    logger.info("CACHE HIT: %s", key)
    return entry["value"]


def set(key: str, value: Any, ttl_seconds: int) -> None:
    logger.info("CACHE SET: %s (ttl=%ds)", key, ttl_seconds)
    _store[key] = {"value": value, "expires_at": time.time() + ttl_seconds}


# TTLs
GEOCODE_TTL = 86400   # 24 hours — coordinates don't change
WEATHER_TTL = 600     # 10 minutes
POI_TTL     = 1800    # 30 minutes


def geocode_key(location: str) -> str:
    return _key("geocode", location)


def weather_key(city: str) -> str:
    return _key("weather", city)


def poi_key(lat: float, lon: float, radius_m: int, brand: str, category: str) -> str:
    return _key("poi", round(lat, 4), round(lon, 4), radius_m, brand or "", category or "")
