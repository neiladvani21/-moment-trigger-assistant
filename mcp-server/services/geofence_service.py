from models.geofence import GeofenceResponse


def recommend_geofence(poi_count: int, radius_m: int) -> GeofenceResponse:
    if poi_count == 0:
        return GeofenceResponse(
            recommended_radius_m=radius_m,
            reasoning="No POIs found. Keeping the requested radius; consider expanding the search area.",
        )

    density = poi_count / max(radius_m, 1)

    if density > 0.05:
        # Dense area — tighten radius to reduce false triggers
        recommended = max(100, radius_m // 2)
        reasoning = (
            f"High POI density ({poi_count} POIs within {radius_m}m). "
            f"Recommend tightening geofence to {recommended}m to reduce false triggers."
        )
    elif density < 0.005:
        # Sparse area — expand radius to improve hit rate
        recommended = min(5000, radius_m * 2)
        reasoning = (
            f"Low POI density ({poi_count} POIs within {radius_m}m). "
            f"Recommend expanding geofence to {recommended}m to improve trigger coverage."
        )
    else:
        # Moderate density — keep as-is
        recommended = radius_m
        reasoning = (
            f"Moderate POI density ({poi_count} POIs within {radius_m}m). "
            f"Current radius of {recommended}m is appropriate."
        )

    return GeofenceResponse(recommended_radius_m=recommended, reasoning=reasoning)
