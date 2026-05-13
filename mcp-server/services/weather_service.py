import httpx
from fastapi import HTTPException

from config import OPEN_METEO_URL, HTTP_TIMEOUT
from models.weather import WeatherResponse
from services.geocode_service import geocode_location
from services.cache import get as cache_get, set as cache_set, weather_key, WEATHER_TTL

WEATHERCODE_TO_CONDITION = {
    0:  "Clear sky",
    1:  "Mainly clear",
    2:  "Partly cloudy",
    3:  "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


async def get_weather(city: str) -> WeatherResponse:
    cached = cache_get(weather_key(city))
    if cached:
        return cached

    geo = await geocode_location(city)

    params = {
        "latitude": geo.lat,
        "longitude": geo.lon,
        "current": "temperature_2m,weathercode,relative_humidity_2m",
    }

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.get(OPEN_METEO_URL, params=params)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Open-Meteo request timed out.")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Upstream weather error: {str(e)}")

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Open-Meteo returned status {response.status_code}.")

    data = response.json()
    current = data.get("current", {})

    temperature = current.get("temperature_2m")
    weathercode = current.get("weathercode")
    humidity = current.get("relative_humidity_2m")

    if temperature is None or weathercode is None or humidity is None:
        raise HTTPException(status_code=502, detail="Incomplete weather data returned from Open-Meteo.")

    condition = WEATHERCODE_TO_CONDITION.get(weathercode, "Unknown condition")

    result = WeatherResponse(
        city=city,
        temperature=temperature,
        condition=condition,
        humidity=int(humidity),
    )
    cache_set(weather_key(city), result, WEATHER_TTL)
    return result
