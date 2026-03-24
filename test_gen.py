import sys
import os
import traceback
from dotenv import load_dotenv

env_path = os.path.join(os.getcwd(), 'backend', '.env')
load_dotenv(env_path)

sys.path.append(os.path.join(os.getcwd(), 'backend'))
from services import generate_itinerary_with_llm

city = 'Shimla, Himachal Pradesh'
days = 3
budget = 'Moderate'
interests = 'food, photography, culture'

try:
    print(f"Loaded GROQ Key: {os.getenv('GROQ_API_KEY')[:10]}...")
    print("Starting LLM generation...")
    itinerary, weather = generate_itinerary_with_llm(city, days, budget, interests)
    print("Generation successful!")
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()
