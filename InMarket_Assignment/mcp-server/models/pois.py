from pydantic import BaseModel
from typing import List


class POI(BaseModel):
    name: str
    lat: float
    lon: float
    distance_m: float
    type: str


class POIsResponse(BaseModel):
    results: List[POI]
