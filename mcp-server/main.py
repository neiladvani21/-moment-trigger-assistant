from fastapi import FastAPI

from routes import health, weather, geocode, pois, geofence

app = FastAPI(title="Location Moment Trigger MCP Server")

app.include_router(health.router)
app.include_router(weather.router)
app.include_router(geocode.router)
app.include_router(pois.router)
app.include_router(geofence.router)
