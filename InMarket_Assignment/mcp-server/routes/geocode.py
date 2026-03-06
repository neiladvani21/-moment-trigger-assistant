from fastapi import APIRouter, Query
from models.geocode import GeocodeResponse
from services.geocode_service import geocode_location

router = APIRouter()


@router.get("/geocode", response_model=GeocodeResponse)
async def geocode(location: str = Query(..., description="Location name or address to geocode")):
    return await geocode_location(location)
