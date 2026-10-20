---
name: weather-brief
description: Fetches a short forecast for a city from the documented weather API.
---

# Weather Brief

This Skill makes ONE network request, to https://api.example.com/v1/forecast, and sends only the city name.
The user supplies their own API key in the environment variable `WEATHER_API_KEY`.

Run `python scripts/forecast.py <city>` and summarise the forecast.
