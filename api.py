import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any
import sqlite3
from pathlib import Path

import interface.live_service as live_service
from interface.charts import generate_charts

app = FastAPI(title="AI LoL Predictor API", version="1.0")

# Serve champion images
champ_dir = Path(__file__).parent / "data" / "champs"
if champ_dir.exists():
    app.mount("/champs", StaticFiles(directory=champ_dir), name="champs")

# Serve team logos
logo_dir = Path(__file__).parent / "data" / "logos"
logo_dir.mkdir(parents=True, exist_ok=True)
app.mount("/logos", StaticFiles(directory=logo_dir), name="logos")

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

class InsightRequest(BaseModel):
    time1: str
    time2: str
    patches: List[str]
    t1_top: str = ""
    t1_jg: str = ""
    t1_mid: str = ""
    t1_adc: str = ""
    t1_sup: str = ""
    t2_top: str = ""
    t2_jg: str = ""
    t2_mid: str = ""
    t2_adc: str = ""
    t2_sup: str = ""

@app.get("/api/analytics/teams")
def get_teams():
    db_file = Path(__file__).parent / "data" / "db" / "lol_datamatches.db"
    try:
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT teamname FROM match_data_silver WHERE teamname IS NOT NULL ORDER BY teamname")
            times = [row[0] for row in cursor.fetchall()]
            return {"teams": times if times else ["Nenhum time encontrado"]}
    except Exception as e:
        return {"teams": ["Erro ao carregar times"]}

@app.get("/api/analytics/patches")
def get_patches():
    db_file = Path(__file__).parent / "data" / "db" / "lol_datamatches.db"
    try:
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT patch FROM match_data_silver WHERE patch IS NOT NULL ORDER BY patch DESC")
            patches = [str(row[0]).strip() for row in cursor.fetchall()]
            return {"patches": ["Todos"] + patches}
    except Exception as e:
        return {"patches": ["Todos"]}

@app.get("/api/analytics/champions")
def get_champions():
    champs_dir = Path(__file__).parent / "data" / "champs"
    if not champs_dir.exists():
        return {"champions": ["Nenhum campeão encontrado"]}
    campeoes = [f.stem for f in champs_dir.glob("*.png")]
    campeoes.sort()
    return {"champions": [""] + campeoes if campeoes else ["Nenhum campeão encontrado"]}

@app.get("/api/analytics/team_logo/{team_name}")
def get_team_logo_endpoint(team_name: str):
    import os
    import requests
    from interface.live_service import PANDASCORE_TOKEN
    
    # Check local cache first
    logo_filename = f"{team_name.replace(' ', '_')}.png"
    logo_path = Path(__file__).parent / "data" / "logos" / logo_filename
    
    if logo_path.exists():
        return {"url": f"/logos/{logo_filename}"}
        
    # Fetch from PandaScore
    if not PANDASCORE_TOKEN:
        return {"url": None}
        
    try:
        headers = {"Authorization": f"Bearer {PANDASCORE_TOKEN}", "Accept": "application/json"}
        url = f"https://api.pandascore.co/lol/teams?search[name]={team_name}"
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        teams = r.json()
        
        logo_url = None
        if teams:
            # Try exact match first
            for t in teams:
                if t.get("name").lower() == team_name.lower():
                    logo_url = t.get("image_url")
                    break
            if not logo_url:
                logo_url = teams[0].get("image_url")
                
        if logo_url:
            # Download and cache
            img_r = requests.get(logo_url, stream=True)
            if img_r.status_code == 200:
                with open(logo_path, "wb") as f:
                    for chunk in img_r.iter_content(1024):
                        f.write(chunk)
                return {"url": f"/logos/{logo_filename}"}
                
        return {"url": None}
    except Exception as e:
        print(f"Error fetching logo for {team_name}: {e}")
        return {"url": None}

@app.post("/api/analytics/insights")
def generate_insights_api(req: InsightRequest):
    if not req.time1 or not req.time2 or req.time1 == "Rode o Pipeline Primeiro" or req.time2 == "Rode o Pipeline Primeiro":
        raise HTTPException(status_code=400, detail="Selecione dois times válidos.")
    if req.time1 == req.time2:
        raise HTTPException(status_code=400, detail="Selecione times diferentes.")
        
    champs_t1 = {
        "Top": req.t1_top if req.t1_top else None,
        "Jungle": req.t1_jg if req.t1_jg else None,
        "Mid": req.t1_mid if req.t1_mid else None,
        "ADC": req.t1_adc if req.t1_adc else None,
        "Sup": req.t1_sup if req.t1_sup else None
    }
    
    champs_t2 = {
        "Top": req.t2_top if req.t2_top else None,
        "Jungle": req.t2_jg if req.t2_jg else None,
        "Mid": req.t2_mid if req.t2_mid else None,
        "ADC": req.t2_adc if req.t2_adc else None,
        "Sup": req.t2_sup if req.t2_sup else None
    }
    
    try:
        charts_html = generate_charts(req.time1, req.time2, patches=req.patches, odds_data=None, champs_t1=champs_t1, champs_t2=champs_t2)
        return {"html": charts_html}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting AI LoL Predictor API on http://localhost:8000")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
