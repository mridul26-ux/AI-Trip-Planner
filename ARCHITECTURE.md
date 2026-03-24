# AI-Powered Trip Planner: System Architecture & Design Document

## 1. System Architecture Overview

The AI Trip Planner follows a modern, decoupled client-server architecture. It leverages a dynamic frontend for user interaction, a robust backend for orchestration, and integrates seamlessly with Large Language Models (LLMs) and external geographic/weather APIs to synthesize personalized travel itineraries.

### Text-Based Architecture Diagram

```text
[ Client / Web Browser ]
      | (REST API / JSON)
      v
[ API Gateway / Backend Server ]
      |
      +-- (1) Auth & Session Management
      |
      +-- (2) Data Aggregation Layer
      |       +--> [ OpenWeather API ] (Forecast context)
      |       +--> [ Google Maps API ] (Geocoding & Travel Times)
      |       +--> [ Google Places API ] (Attractions & Restaurants)
      |
      +-- (3) Prompt Engineering Engine
      |       +--> Formats User Input & Enriched Data
      |
      +-- (4) LLM Orchestration Layer
      |       +--> [ LLM API (Groq/OpenAI) ] (Generates JSON Itinerary)
      |
      +-- (5) Database Access Layer
              +--> [ PostgreSQL / MongoDB ] (Stores Itineraries & Feedback)
```

## 2. Component Breakdown & Tech Stack Suggestions

### 2.1. Frontend (User Interface)
*   **Technologies:** Next.js (React) or Vue.js, Tailwind CSS.
*   **Role:** Captures user constraints (destination, dates, budget, interests) via intuitive forms. Renders the generated chronological itinerary using interactive timeline components and dynamic map views. Captures user feedback for iterative refinement.

### 2.2. Backend (Orchestration & Logic)
*   **Technologies:** Python (FastAPI) or Node.js (Express). *FastAPI is highly recommended for its native async support, Pydantic validation, and excellent integration with Python AI ecosystems.*
*   **Role:** Acts as the central orchestrator. It sanitizes inputs, manages API rate limits, secures API keys, and handles the iterative feedback loop.

### 2.3. LLM Layer
*   **Technologies:** Groq (Llama 3/Mixtral) for ultra low-latency generation, or OpenAI (GPT-4o). LangChain (optional) for complex prompt chaining.
*   **Role:** Parses the combined context (user preferences + real-world data) and generates a structured, culturally aware, and logistically feasible itinerary.

### 2.4. External APIs Layer
*   **Mapping & Location:** Google Maps Platform (Geocoding, Places API, Directions API).
*   **Weather Data:** OpenWeather API (5-Day/3-Hour Forecast).
*   **Role:** Grounds the LLM's imagination in reality. Ensures places actually exist, are open, and that outdoor activities aren't scheduled during thunderstorms.

### 2.5. Database Layer (Optional for MVP)
*   **Technologies:** PostgreSQL (Relational) or MongoDB / Firebase (NoSQL).
*   **Role:** Stores user profiles, saved itineraries, and user feedback history to learn preferences over time.

---

## 3. Step-by-Step Data Flow & Processing Pipeline

### Step 1: User Input Collection
The user enters their constraints on the frontend: Destination (e.g., "Kyoto"), Duration (e.g., "3 Days"), Budget (e.g., "Moderate"), and Interests (e.g., "Temples, Sushi, Photography").

### Step 2: API Enrichment (Pre-Processing)
Before contacting the LLM, the backend fetches real-world constraints via external APIs to enrich the context:
*   Calls **Google Geocoding API** to get exact coordinates for the destination.
*   Calls **OpenWeather API** using those coordinates to get the precise forecast for the selected travel dates.
*   *(Optional)* Calls **Google Places API** to identify top-rated locations matching the user's specific interests.

### Step 3: Prompt Building (Prompt Engineering)
The backend dynamically constructs a strict, system-level prompt. 
*   **Context Injection:** Embeds the user inputs and the enriched real-time API data (weather, accurate places).
*   **Role-Playing:** Commands the LLM to act as a seasoned, elite travel agent constraint-solver.
*   **Schema Enforcement:** Demands the output strictly adhere to a predefined JSON schema (e.g., `[{"day": 1, "activities": [{"time": "09:00", "place": "Fushimi Inari", "type": "Sightseeing"}]}]`).
*   **Logical Routing:** Instructs the LLM to dynamically schedule indoor activities (e.g., museums) on days where the OpenWeather API predicts rain.

### Step 4: LLM Generation
The carefully constructed prompt is sent to the LLM via its API. The model synthesizes the real-world data and user constraints, generating the raw JSON itinerary.

### Step 5: Parsing & Validation
The backend receives the response, strips any markdown formatting, and validates the JSON structure against a strict data model (e.g., a Pydantic schema in FastAPI). If validation fails, an automatic retry or self-correction loop is triggered.

### Step 6: API Post-Enrichment (Logistical Verification)
The backend parses the LLM-generated locations and makes secondary calls to the **Google Directions API / Distance Matrix** to insert accurate travel times between consecutive activities. This ensures the generated schedule is geographically clustered and physically possible.

### Step 7: UI Rendering
The validated, fully enriched JSON payload is transmitted to the frontend. The UI maps the data to a beautiful chronological timeline component and drops geocoded pins onto an embedded interactive Google Map.

### Step 8: Iterative Refinement & Feedback Loop
The platform allows users to act as a "human in the loop". If the user dislikes a specific generated activity (e.g., "I don't eat Sushi"):
*   The user clicks a **"Swap Activity"** button on the UI.
*   The frontend sends a specialized delta-request back to the API.
*   The backend constructs a **Refinement Prompt**: *"Given this existing itinerary, replace the 1:00 PM Sushi lunch with a highly-rated Ramen restaurant physically close to the 10:00 AM Fushimi Inari tour."*
*   The LLM generates the targeted swap, and the UI updates the timeline and map seamlessly without regenerating the entire trip.
