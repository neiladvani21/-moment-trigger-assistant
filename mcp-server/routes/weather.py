from fastapi import APIRouter, Query
from models.weather import WeatherResponse
from services.weather_service import get_weather

router = APIRouter()


@router.get("/weather", response_model=WeatherResponse)
async def weather(city: str = Query(..., description="City name to fetch weather for")):
    return await get_weather(city)
