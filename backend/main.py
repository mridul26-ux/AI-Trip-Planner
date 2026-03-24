from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI(title="AI Trip Planner API")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/health")
async def health_check():
    return {"status": "healthy"}

from pydantic import BaseModel

class TripRequest(BaseModel):
    city: str
    days: int
    budget: str
    interests: str

@app.post("/generate-itinerary")
def build_itinerary(req: TripRequest):
    from services import generate_itinerary_with_llm
    from fastapi import HTTPException
    import traceback
    try:
        itinerary, weather_data, dest_image = generate_itinerary_with_llm(
            city=req.city, 
            days=req.days, 
            budget=req.budget, 
            interests=req.interests
        )
        return {"status": "success", "itinerary": itinerary, "weather": weather_data, "destination_image": dest_image}
    except Exception as e:
        print("\n--- ERROR IN /generate-itinerary ---")
        traceback.print_exc()
        print("------------------------------------\n")
        raise HTTPException(status_code=500, detail=str(e))

class SwapRequest(BaseModel):
    city: str
    current_activity: dict
    interests: str

@app.post("/swap-activity")
def swap_activity(req: SwapRequest):
    from services import generate_alternative_activity_with_llm
    import traceback
    from fastapi import HTTPException
    
    try:
        new_act = generate_alternative_activity_with_llm(
            city=req.city,
            current_activity=req.current_activity,
            interests=req.interests
        )
        return {"status": "success", "activity": new_act}
    except Exception as e:
        print("\n--- ERROR IN /swap-activity ---")
        traceback.print_exc()
        print("------------------------------------\n")
        raise HTTPException(status_code=500, detail=str(e))

# Mount the frontend directory so FastAPI serves the complete HTML web app on the same link!
frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
