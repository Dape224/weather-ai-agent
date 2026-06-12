import os
from openai import OpenAI
from dotenv import load_dotenv
import requests
import json

load_dotenv()

weather_api= os.getenv("WEATHER_API_KEY")


def get_weather(location: str):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={weather_api}&units=metric"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        temp = data["main"]["temp"]
        description = data["weather"][0]["description"]

        return f"{location} is {temp}°C with {description}"

    except requests.exceptions.ConnectionError:
        return "❌ Network error: Check your internet or DNS settings"
    
    except requests.exceptions.Timeout:
        return "❌ Request timed out"

    except requests.exceptions.HTTPError:
        return f"❌ API Error: {response.status_code}"

    except Exception as e:
        return f"❌ Unexpected error: {e}"
    
city= get_weather("lagos")
print(city)