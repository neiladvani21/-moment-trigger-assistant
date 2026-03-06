from pydantic import BaseModel


class GeofenceResponse(BaseModel):
    recommended_radius_m: int
    reasoning: str
