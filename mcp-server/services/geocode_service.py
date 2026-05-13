import httpx
from fastapi import HTTPException

from config import NOMINATIM_URL, NOMINATIM_USER_AGENT, HTTP_TIMEOUT
from models.geocode import GeocodeResponse
from services.cache import get as cache_get, set as cache_set, geocode_key, GEOCODE_TTL


async def geocode_location(location: str) -> GeocodeResponse:
    cached = cache_get(geocode_key(location))
    if cached:
        return cached
    params = {
        "q": location,
        "format": "json",
        "limit": 1,
    }
    headers = {"User-Agent": NOMINATIM_USER_AGENT}

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.get(NOMINATIM_URL, params=params, headers=headers)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Nominatim geocoding request timed out.")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Upstream geocoding error: {str(e)}")

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Nominatim returned status {response.status_code}.")

    data = response.json()
    if not data:
        raise HTTPException(status_code=404, detail=f"Location '{location}' not found.")

    result = data[0]
    response = GeocodeResponse(
        lat=float(result["lat"]),
        lon=float(result["lon"]),
        display_name=result["display_name"],
    )
    cache_set(geocode_key(location), response, GEOCODE_TTL)
    return response
