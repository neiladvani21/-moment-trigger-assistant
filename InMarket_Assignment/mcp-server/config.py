import os
from dotenv import load_dotenv

load_dotenv()

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_USER_AGENT = "InMarket-MCP-Server/1.0"

HTTP_TIMEOUT = 30.0
