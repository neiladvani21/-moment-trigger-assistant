from fastapi import APIRouter, Query
from models.geofence import GeofenceResponse
from services.geofence_service import recommend_geofence

router = APIRouter()


@router.get("/geofence", response_model=GeofenceResponse)
def geofence(
    poi_count: int = Query(..., description="Number of POIs found in the area"),
    radius_m: int = Query(..., description="Radius in metres that was searched"),
):
    return recommend_geofence(poi_count, radius_m)
