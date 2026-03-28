import os
import json
import requests
from groq import Groq

# Pull API keys from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

def get_groq_client():
    if not GROQ_API_KEY:
        raise ValueError("GROQ API key is missing. Please add it to .env.")
    return Groq(api_key=GROQ_API_KEY, timeout=12.0)

def get_weather_forecast(destinations: str):
    """Fetches live weather for the primary city. Uses OpenWeather API if available, falls back to wttr.in."""
    import re
    # Extract the very first city name if they provide a multi-city string like "Paris & Rome"
    primary_city = re.split(r'[,&]', destinations)[0].strip()
    
    if OPENWEATHER_API_KEY:
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={primary_city}&appid={OPENWEATHER_API_KEY}&units=metric"
            res = requests.get(url, timeout=4).json()
            if res.get("cod") == 200 or res.get("cod") == "200":
                temp = round(res['main']['temp'])
                desc = res['weather'][0]['description'].capitalize()
                
                # Assign emoji based on conditions
                icon = "☀️"
                d_lower = desc.lower()
                if "rain" in d_lower or "drizzle" in d_lower: icon = "🌧️"
                elif "cloud" in d_lower: icon = "☁️"
                elif "snow" in d_lower: icon = "❄️"
                elif "clear" in d_lower: icon = "☀️"
                elif "thunderstorm" in d_lower: icon = "⛈️"
                elif "mist" in d_lower or "fog" in d_lower: icon = "🌫️"
                
                return {"city": primary_city, "forecast": f"{desc}, {temp}°C", "icon": icon}
            else:
                print(f"OpenWeather API Warning: {res.get('message')}. Falling back to keyless service...")
        except Exception as e:
            print(f"OpenWeather Exception: {e}")
            
    # Real live keyless API via wttr.in
    try:
        headers = {'User-Agent': 'AITripPlanner/1.0'}
        res = requests.get(f"https://wttr.in/{primary_city}?format=j1", headers=headers, timeout=4).json()
        current = res['current_condition'][0]
        temp = current['temp_C']
        desc = current['weatherDesc'][0]['value']
        
        icon = "☀️"
        desc_lower = desc.lower()
        if "rain" in desc_lower or "shower" in desc_lower: icon = "🌧️"
        elif "cloud" in desc_lower or "overcast" in desc_lower: icon = "☁️"
        elif "snow" in desc_lower: icon = "❄️"
        elif "fog" in desc_lower or "mist" in desc_lower: icon = "🌫️"
        elif "storm" in desc_lower or "thunder" in desc_lower: icon = "⛈️"
        
        return {"city": primary_city, "forecast": f"{desc}, {temp}°C", "icon": icon}
    except Exception:
        pass
        
    # Fallback to Mock Data
    return {"city": primary_city, "forecast": f"Sunny, High 28°C", "icon": "☀️"}

def fetch_place_photo(place_name: str, city: str):
    if GOOGLE_MAPS_API_KEY:
        try:
            search_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
            params = {"input": f"{place_name} {city}", "inputtype": "textquery", "fields": "photos", "key": GOOGLE_MAPS_API_KEY}
            res = requests.get(search_url, params=params, timeout=3).json()
            if res.get("status") == "OK" and res.get("candidates") and res["candidates"][0].get("photos"):
                photo_ref = res["candidates"][0]["photos"][0]["photo_reference"]
                return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=600&photo_reference={photo_ref}&key={GOOGLE_MAPS_API_KEY}"
        except:
            pass
    # Fallback to Wikipedia Search API (Strict title matching for perfection)
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query", 
            "generator": "search", 
            "gsrsearch": f'intitle:"{place_name}"', 
            "gsrlimit": 1, 
            "prop": "pageimages", 
            "format": "json", 
            "pithumbsize": 600
        }
        headers = {'User-Agent': 'AITripPlanner/1.0 (info@aitripplanner.local)'}
        res = requests.get(url, params=params, headers=headers, timeout=3).json()
        pages = res.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if "thumbnail" in page_data:
                return page_data["thumbnail"]["source"]
    except:
        pass
    return None

def get_places(city: str, interests: str):
    """Fetches places via Google Places."""
    if GOOGLE_MAPS_API_KEY:
        # TODO: Implement actual Google Maps Place search
        pass
    
    # Return empty to rely entirely on the LLM's vast knowledge of real places!
    return []

def generate_itinerary_with_llm(city: str, days: int, budget: str, interests: str):
    """Uses Groq to generate a JSON itinerary."""
    client = get_groq_client()
    weather = get_weather_forecast(city)
    places = get_places(city, interests)
    
    prompt = f"""
    You are an expert travel, logistics, and routing agent. Create an elegant {days}-day multi-destination itinerary for {city}.
    User Budget Level: {budget}
    User Interests: {interests}
    
    Primary Weather Context: {weather['forecast']}

    MULTI-CITY RULES: If the user provided multiple regions or cities (e.g. "Paris & Rome" or "Euro Trip"), you must logically distribute the {days} days between those locations! You MUST allocate realistic travel time between the cities (e.g. flights or high-speed rail) as an actual tracked activity in the itinerary timeline!

    CRITICAL INSTRUCTION: Ensure a full, rich schedule (at least 3-4 distinct activities per day). MANDATORY: You MUST absolutely include ALL globally famous, iconic, "must-see" bucket-list landmarks for {city} somewhere in the itinerary. Specifically, DO NOT skip any famous places related to the city's culture, ancient worship/temples, world-class food, or highly photographic iconic spots! Then, fill any remaining gaps with phenomenal, highly-rated local spots. Do NOT EVER use generic placeholders, and NEVER hallucinate false locations. DO NOT suggest individual prices.
    CRITICAL BUDGET INSTRUCTION: You must strictly calculate the `estimated_budget_inr` using highly realistic, localized pricing for {city}. Compute it logically: (Average {budget} Hotel rate * {days} days) + (Average {budget} Food/Transport rate * {days} days) + (Cross-country Train/Flight transport costs). Do NOT hallucinate extreme outlier prices. Show your basic breakdown in the schema string!

    Return ONLY a valid JSON object matching this exact schema:
    {{
      "estimated_budget_inr": "e.g. ₹12,000 - ₹15,000 (Based on ₹2000/night hotel + ₹1500/day food/travel)",
      "itinerary": [
        {{
          "day": 1,
          "activities": [
             {{"time": "09:00", "place": "Exact Real Place Name", "city": "City where place is located", "description": "Accurate, factual description only", "type": "Sightseeing"}}
          ]
        }}
      ]
    }}
    Do not output markdown blocks, backticks, or text before/after. Just the raw JSON object.
    """

    response = None
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a specialized API that outputs raw JSON objects. Never output markdown format."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.7,
            max_tokens=2500,
        )
        
        import re
        import concurrent.futures

        content = response.choices[0].message.content.strip()
        # Extract JSON object using regex
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            raw_json = match.group(0)
        else:
            raw_json = content
            
        itinerary_data = json.loads(raw_json)
        
        # Gather all activities to fetch images quickly in parallel
        all_activities = []
        for day in itinerary_data.get('itinerary', []):
            for act in day.get('activities', []):
                all_activities.append(act)
                
        def attach_photo(act):
            place = act.get('place', '')
            if place and place != 'Unknown Place':
                act['image_url'] = fetch_place_photo(place, city)
                
        # Execute Wikipedia/Google image searches 5 times faster!
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            list(executor.map(attach_photo, all_activities))
            
        # Get a beautiful thematic background image of the main city
        primary_city = re.split(r'[,&]', city)[0].strip()
        destination_image = fetch_place_photo(primary_city, primary_city)
            
        return itinerary_data, weather, destination_image
    except Exception as e:
        raise ValueError(f"LLM generated invalid JSON or Engine Timeout. Error: {str(e)[:50]}")


def generate_alternative_activity_with_llm(city: str, current_activity: dict, interests: str):
    client = get_groq_client()
    
    prompt = f"""
    You are replacing an activity in a multi-day itinerary for {city}.
    The user wants an alternative for: "{current_activity.get('place')}" at {current_activity.get('time')}.
    User Interests: {interests}

    CRITICAL INSTRUCTION: Suggest a phenomenal, high-quality alternative that is globally famous or highly-recommended in {city}. Do NOT EVER use generic placeholders, and NEVER hallucinate false locations.
    The alternative MUST BE DIFFERENT from "{current_activity.get('place')}".
    
    Return ONLY a valid JSON object matching this exact schema:
    {{
      "time": "{current_activity.get('time', '12:00')}",
      "place": "Exact Real New Place Name",
      "city": "City where place is located",
      "description": "Highly accurate, factual description. No hallucinations.",
      "type": "Category"
    }}
    Do not output markdown blocks, backticks, or text before/after. Just the raw JSON object.
    """

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You output only raw JSON objects. No markdown."},
            {"role": "user", "content": prompt}
        ],
        model="llama-3.1-8b-instant",
        temperature=0.8,
        max_tokens=1000,
    )
    
    import re
    try:
        content = response.choices[0].message.content.strip()
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            raw_json = match.group(0)
        else:
            raw_json = content
            
        act = json.loads(raw_json)
        
        # Enrich with Wikipedia photo
        place = act.get('place', '')
        if place and place != 'Unknown Place':
            act['image_url'] = fetch_place_photo(place, city)
            
        return act
    except Exception as e:
        raise ValueError(f"LLM generated invalid JSON during swap.")
