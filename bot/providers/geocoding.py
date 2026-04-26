import httpx

from bot.providers.weather_base import GeocodingCandidate


class GeocodingClient:
    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def search(self, query: str, count: int = 5) -> list[GeocodingCandidate]:
        response = await self._http.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": query, "count": count, "language": "ru", "format": "json"},
        )
        response.raise_for_status()
        payload = response.json()
        return [
            GeocodingCandidate(
                name=item["name"],
                country=item.get("country", ""),
                latitude=float(item["latitude"]),
                longitude=float(item["longitude"]),
                timezone=item.get("timezone", "UTC"),
            )
            for item in payload.get("results", [])
        ]
