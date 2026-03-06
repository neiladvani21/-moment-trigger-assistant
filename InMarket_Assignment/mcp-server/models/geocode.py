from pydantic import BaseModel


class GeocodeResponse(BaseModel):
    lat: float
    lon: float
    display_name: str
