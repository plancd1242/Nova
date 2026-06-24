from __future__ import annotations

import requests

from nova.config import settings


def weather_report() -> str:
    if not settings.openweather_api_key or settings.openweather_api_key.startswith("put_"):
        return "Weather is not set up yet. Add OPENWEATHER_API_KEY to .env.local."
    query = f"{settings.city},{settings.state},{settings.country}"
    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": query, "appid": settings.openweather_api_key, "units": "imperial"},
            timeout=8,
        )
        if response.status_code != 200:
            return "I could not get the weather right now."
        data = response.json()
        temp = round(data["main"]["temp"])
        description = data["weather"][0]["description"]
        return f"The weather in {settings.city} is {temp} degrees and {description}."
    except Exception:
        return "I could not reach the weather service right now."

