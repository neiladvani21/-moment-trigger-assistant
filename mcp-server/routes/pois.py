from typing import List, Optional

from fastapi import APIRouter, Query
from models.pois import POI
from services.pois_service import get_pois

router = APIRouter()


@router.get("/pois", response_model=List[POI])
async def pois(
    lat: float = Query(..., description="Latitude of the search centre"),
    lon: float = Query(..., description="Longitude of the search centre"),
    radius_m: int = Query(1000, description="Search radius in metres"),
    brand: Optional[str] = Query(None, description="Brand name (e.g. Target, Walmart)"),
    category: Optional[str] = Query(None, description="POI category: gym, pharmacy, grocery, coffee, fast_food"),
):
    return await get_pois(lat, lon, radius_m, brand, category)
