import os
import time
from openai import OpenAI
from dotenv import load_dotenv
import requests
import json

load_dotenv()

api_key=os.getenv("MISTRAL_API_KEY")
if not api_key:
    raise ValueError("MISTRAL_API_KEY is missing")

weather_api= os.getenv("WEATHER_API_KEY")
if not weather_api:
    raise ValueError("WEATHER_API_KEY is missing")

client = OpenAI(
    base_url="https://api.mistral.ai/v1",
    api_key=api_key,
    timeout=60
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "location name"
                    }
                },
                "required": ["location"]
            }
        }
    },
     {
        "type": "function",
        "function": {
            "name": "get_weather_forecast",
            "description": "Get the weather forecast for a location (next few days)",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "location name"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

results = []

last_location = None

def get_weather(location: str):
    url = url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={weather_api}&units=metric"
    try:
        response= requests.get(url, timeout= 60)
        data = response.json()

        if response.status_code != 200:
            return f"Error fetching weather for {location}"

        temp = data["main"]["temp"]
        description = data["weather"][0]["description"]

        return f"{location} is {temp}°C with {description}"
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to the weather service. Check your internet connection or DNS settings."
    except requests.exceptions.Timeout:
        return "Error: The weather service request timed out."
    except requests.exceptions.HTTPError as err:
        return f"Error: HTTP request failed ({err})"
    except Exception as e:
        return f"Unexpected error: {e}"

def get_weather_forecast(location: str):
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={location}&appid={weather_api}&units=metric"
    
    try:
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200:
            return f"Error fetching forecast for {location}"

        forecast_list = data["list"]

        result = f"Weather forecast for {location}:\n"

        for item in forecast_list[:5]:
            time = item["dt_txt"]
            temp = item["main"]["temp"]
            desc = item["weather"][0]["description"]

            result += f"{time}: {temp}°C, {desc}\n"
        return result
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to the weather forecast service. Check your internet connection or DNS settings."
    except requests.exceptions.Timeout:
        return "Error: The weather forecast service request timed out."
    except requests.exceptions.HTTPError as err:
        return f"Error: HTTP request failed ({err})"
    except Exception as e:
        return f"Unexpected error: {e}"

def safe_llm_call(**kwargs):
    for attempts in range(3):
        try:
             response = client.chat.completions.create(**kwargs)
             return response
        except Exception as e:
            print(f"Retrying... Attempt {attempts + 1} failed, error: ", e)
            time.sleep(2)
    return None

def summarize_messages(messages):
    try:
        response = safe_llm_call(
            model="mistral-medium-3.5",
            messages=[
                {"role": "system", "content": "Summarize this conversation briefly."},
                {"role": "user", "content": str(messages)}
            ]
        )
        return response.choices[0].message.content
    except:
        return "Summary failed"
     
messages = [
    {"role": "system", "content": 
"You are a helpful weather assistant. Use get_weather for current weather. Use get_weather_forecast when user asks about future weather, forecast, tomorrow, next days. Always extract ALL locations from user queries. If multiple locations are mentioned, call the tool multiple times."}
    ]

tool_functions = {
    "get_weather": get_weather,
    "get_weather_forecast": get_weather_forecast
}

print("☁ Weather Agent Ready (type 'exit' to quit)")

while True:
    user_input= input("\n Ask: ")

    if user_input in ['exit', 'quit']:
        break
    messages.append({"role":"user", "content": user_input})

    MAX_MESSAGES = 20

    if len(messages) > MAX_MESSAGES:
        old_messages = messages[:-10]   
        summary = summarize_messages(old_messages)

        messages = [
            messages[0],  
            {"role": "system", "content": f"Conversation summary: {summary}"}
        ] + messages[-10:]

    try:   
        response = safe_llm_call(
                    model="mistral-medium-3.5",
                    messages=messages,
                    tools=tools 
                    
                )
        message= response.choices[0].message
    except Exception as e:
        print(f"LLM Error: {e}")
        continue

    if message.tool_calls:
        
        messages.append(message)

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            print("\n [DEBUG] Tool needed: ", tool_name)

            try:
                args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                print("Invalid JSON argument")
                continue

            if "location" in args:
                last_location = args["location"]

            if "location" not in args or not args["location"]:
                if last_location:
                    args["location"] = last_location

            if tool_name in tool_functions:
                try:
                    result = tool_functions[tool_name](**args)
                except TypeError:
                    result = 'Error: Invalid argument for tool'
                except Exception as e:
                    result = f'Tool Execution error: {e}'              
            else:
                result = f"Tool {tool_name} not implemented"


            print("[DEBUG] Arguments: ", args)

            print("[DEBUG] Tool result:", result)

            

            messages.append(
                {
                    "role": "tool", 
                    "tool_call_id": tool_call.id,
                    "content": result
                }
            )

        final_response = safe_llm_call(
        model="mistral-medium-3.5",
        messages=messages,
        stream= True
        )
        print('Assistant: ', end= "", flush= True)
        final_text = ""

        try:
            for chunk in final_response:
                content = chunk.choices[0].delta.content
                if content:
                    print(content, end="", flush=True)
                    final_text += content
        except Exception as e:
            print(f"Streaming error: {e}")    
                
                

        messages.append({"role": "assistant", "content": final_text})
    else:
        print("\nAssistant:", message.content)
        messages.append({"role": "assistant", "content": message.content})





