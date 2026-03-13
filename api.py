import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

import interface.live_service as live_service

app = FastAPI(title="AI LoL Predictor API", version="1.0")

# Enable CORS for the SvelteKit frontend (typically runs on port 5173 or 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "message": "AI LoL Predictor API is running."}

@app.get("/api/live/games", response_model=List[Dict[str, Any]])
def get_live_games():
    """
    Returns the currently live games dynamically from LoL Esports or Aureom API.
    """
    try:
        live_games = live_service.get_live_games()
        return live_games
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/live/today", response_model=List[Dict[str, Any]])
def get_today_games():
    """
    Returns the scheduled/completed games for today from LoL Esports API.
    """
    try:
        today_games = live_service.get_schedule_today()
        return today_games
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/live/pandascore", response_model=List[Dict[str, Any]])
def get_pandascore_fixtures():
    """
    Returns the Pandascore fixtures for today (free tier).
    """
    try:
        fixtures = live_service.get_pandascore_fixtures()
        return fixtures
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting AI LoL Predictor API on http://localhost:8000")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
