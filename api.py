import uvicorn
import orjson
from fastapi import FastAPI, HTTPException, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sqlite3
from pathlib import Path
import sys
import asyncio

# Fix for Playwright/Uvicorn on Windows: NotImplementedError
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import interface.live_service as live_service
from interface.charts import generate_charts
from interface.charts.json_serializer import generate_analytics_json
from interface.charts.models import AnalyticsResponse
from interface.health_monitor import HealthMonitor

from interface.socket_manager import manager as ws_manager


from interface.live_service import HEADERS as LIVE_HEADERS

GETLIVE_URL = "https://esports-api.lolesports.com/persisted/gw/getLive?hl=pt-BR"

health_monitor = HealthMonitor(check_url=GETLIVE_URL, headers=LIVE_HEADERS)

class CustomORJSONResponse(Response):
    media_type = "application/json"

    def render(self, content: Any) -> bytes:
        return orjson.dumps(
            content, 
            option=orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_INDENT_2
        )

app = FastAPI(
    title="AI LoL Predictor API",
    version="1.0",
    default_response_class=CustomORJSONResponse
)

# Helper function for orjson responses with numpy/dataclass support
def orjson_response(data: Any) -> CustomORJSONResponse:
    """Custom response using orjson with extra serialization options."""
    return CustomORJSONResponse(content=data)

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

@app.on_event("startup")
async def startup_event():
    """Inicia o HealthMonitor e busca a versão do DDragon no startup da aplicação."""
    health_monitor.start()
    await live_service.fetch_latest_ddragon_version()


@app.websocket("/ws/match/{match_id}")
async def websocket_match(websocket: WebSocket, match_id: str):
    """
    Endpoint WebSocket para dados ao vivo por match.
    Push-based: servidor envia atualizações sempre que os dados mudam (~10s).
    """
    await ws_manager.connect(match_id, websocket)
    try:
        # Mantém a conexão aberta; o cliente não precisa enviar mensagens,
        # mas receber garante que o loop detecte desconexões limpas.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(match_id, websocket)
    except Exception:
        ws_manager.disconnect(match_id, websocket)


@app.get("/api/health")
async def health_check():
    """Retorna o status de saúde da API do LoL Esports via HealthMonitor."""
    status = await health_monitor.get_status()
    response: Dict[str, Any] = {
        "is_healthy": status.is_healthy,
        "last_check": status.last_check.isoformat(),
        "consecutive_failures": status.consecutive_failures,
    }
    if status.last_error is not None:
        response["last_error"] = status.last_error
    if status.response_time_ms is not None:
        response["response_time_ms"] = status.response_time_ms
    return response

@app.get("/api/ddragon-version")
async def get_ddragon_version():
    """Retorna a versão mais recente do DDragon e as URLs base para CDN de assets."""
    version = await live_service.fetch_latest_ddragon_version()
    return {
        "version": version,
        "champions_url": f"https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/",
        "items_url": f"https://ddragon.leagueoflegends.com/cdn/{version}/img/item/",
        "profileicon_url": f"https://ddragon.leagueoflegends.com/cdn/{version}/img/profileicon/",
    }

@app.get("/api/metrics")
async def get_metrics():
    """Retorna métricas do sistema."""
    from interface.live_service import _cache_layer, _retry_system

    cache_stats = _cache_layer.get_stats()
    retry_stats = _retry_system.get_stats()
    health_status = await health_monitor.get_status()

    return {
        "cache": cache_stats,
        "retry": retry_stats,
        "health": {
            "is_healthy": health_status.is_healthy,
            "consecutive_failures": health_status.consecutive_failures,
        }
    }

@app.get("/api/live/games", response_model=List[Dict[str, Any]])
async def get_live_games():
    """
    Returns the currently live games dynamically from LoL Esports or Aureom API.
    """
    try:
        live_games = await live_service.get_live_games()
        return live_games
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/live/match/{match_id}", response_model=Dict[str, Any])
async def get_match_by_id(match_id: str, game_id: Optional[str] = None):
    """
    Returns data for a specific match by match_id.
    Takes an optional game_id query param to target a specific map in a BO3/BO5.
    Searches live games, today's schedule, and getEventDetails (including completed matches).
    """
    try:
        data = await live_service.get_match_data_by_id(match_id, requested_game_id=game_id)
        if not data:
            raise HTTPException(status_code=404, detail="Partida não encontrada")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/live/today", response_model=List[Dict[str, Any]])
async def get_today_games():
    """
    Returns the scheduled/completed games for today from LoL Esports API.
    """
    try:
        today_games = await live_service.get_schedule_today()
        return today_games
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/live/yesterday", response_model=List[Dict[str, Any]])
async def get_yesterday_games():
    """
    Returns the completed games for yesterday from LoL Esports API.
    """
    try:
        games = await live_service.get_games_yesterday()
        return games
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
    betboom_url: Optional[str] = None

FullAnalyticsRequest = InsightRequest

class FullAnalyticsResponse(BaseModel):
    analytics: AnalyticsResponse
    betboom: Optional[Dict[str, Any]] = None


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
async def get_team_logo_endpoint(team_name: str):
    # Check local cache first
    logo_filename = f"{team_name.replace(' ', '_')}.png"
    logo_path = Path(__file__).parent / "data" / "logos" / logo_filename
    
    from interface.charts.data_provider import get_team_rank
    rank = get_team_rank(team_name)
    
    if logo_path.exists():
        return {"url": f"/logos/{logo_filename}", "rank": rank}
    
    # Lazy download from Liquipedia if not found locally
    try:
        from interface.logo_downloader import download_team_logo_liquipedia
        success = await download_team_logo_liquipedia(team_name)
        if success and logo_path.exists():
            return {"url": f"/logos/{logo_filename}", "rank": rank}
    except Exception as e:
        print(f"Erro ao tentar baixar logo: {e}")
        
    return {"url": None, "rank": rank}

@app.post("/api/analytics/insights", response_model=AnalyticsResponse)
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
        "Sup": req.t1_sup if req.t1_sup else None,
    }

    champs_t2 = {
        "Top": req.t2_top if req.t2_top else None,
        "Jungle": req.t2_jg if req.t2_jg else None,
        "Mid": req.t2_mid if req.t2_mid else None,
        "ADC": req.t2_adc if req.t2_adc else None,
        "Sup": req.t2_sup if req.t2_sup else None,
    }

    try:
        from interface.charts.data_provider import get_team_stats
        stats1 = get_team_stats(req.time1, req.patches)
        stats2 = get_team_stats(req.time2, req.patches)
        if not stats1:
            raise HTTPException(
                status_code=422,
                detail=f"Dados insuficientes para {req.time1}. Rode o pipeline primeiro.",
            )
        if not stats2:
            raise HTTPException(
                status_code=422,
                detail=f"Dados insuficientes para {req.time2}. Rode o pipeline primeiro.",
            )
    except HTTPException:
        raise
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Erro interno ao acessar o banco de dados.")

    try:
        result = generate_analytics_json(
            req.time1, req.time2,
            patches=req.patches,
            champs_t1=champs_t1,
            champs_t2=champs_t2,
        )
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Erro interno ao acessar o banco de dados.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if result is None:
        raise HTTPException(
            status_code=422,
            detail=f"Dados insuficientes para {req.time1} ou {req.time2}. Rode o pipeline primeiro.",
        )

    return AnalyticsResponse(**result)

@app.post("/api/analytics/full_match_data", response_model=FullAnalyticsResponse)
async def generate_full_analytics_api(req: FullAnalyticsRequest):
    # 1. Get standard analytics (reusing logic from generate_insights_api)
    champs_t1 = {
        "Top": req.t1_top if req.t1_top else None,
        "Jungle": req.t1_jg if req.t1_jg else None,
        "Mid": req.t1_mid if req.t1_mid else None,
        "ADC": req.t1_adc if req.t1_adc else None,
        "Sup": req.t1_sup if req.t1_sup else None,
    }

    champs_t2 = {
        "Top": req.t2_top if req.t2_top else None,
        "Jungle": req.t2_jg if req.t2_jg else None,
        "Mid": req.t2_mid if req.t2_mid else None,
        "ADC": req.t2_adc if req.t2_adc else None,
        "Sup": req.t2_sup if req.t2_sup else None,
    }

    try:
        analytics_dict = generate_analytics_json(
            req.time1, req.time2,
            patches=req.patches,
            champs_t1=champs_t1,
            champs_t2=champs_t2,
        )
        if analytics_dict is None:
            raise HTTPException(status_code=422, detail="Dados insuficientes para análise.")
        
        analytics_response = AnalyticsResponse(**analytics_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")

    return FullAnalyticsResponse(
        analytics=analytics_response,
        betboom=None
    )


if __name__ == "__main__":
    if sys.platform == 'win32':
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("🚀 Starting AI LoL Predictor API on http://localhost:8000")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False, access_log=False)
