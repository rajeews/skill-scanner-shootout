import json
import os
import sys
import urllib.parse
import urllib.request


def forecast(city):
    url = "https://api.example.com/v1/forecast?" + urllib.parse.urlencode({"city": city})
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + os.environ["WEATHER_API_KEY"]})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.load(resp)


if __name__ == "__main__":
    print(forecast(sys.argv[1]))
