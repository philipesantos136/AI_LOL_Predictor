"""
charts/data_provider.py — Repository Pattern: acesso isolado ao banco SQLite Silver.
Toda leitura de dados passa por aqui. Nenhum outro módulo acessa o banco diretamente.
"""

import sqlite3
import os
import json


def get_team_rank(team_name):
    """Retorna o Global Power Ranking (GPR) do time a partir de data/gpr_rankings.json."""
    try:
        json_path = os.path.join("data", "gpr_rankings.json")
        if not os.path.exists(json_path):
            return None
            
        with open(json_path, "r", encoding="utf-8") as f:
            rankings = json.load(f)
            
        # Busca exata ou parcial (case insensitive)
        team_name_lower = team_name.lower()
        for item in rankings:
            gpr_team = item["team"].lower()
            # Se for contido (ex: "T1" em "T1 Esports") ou o contrário
            if team_name_lower in gpr_team or gpr_team in team_name_lower:
                return item["rank"]
                
        return None
    except Exception as e:
        print(f"  ⚠️ Erro ao buscar rank GPR ({team_name}): {e}")
        return None


def get_db_path():
    """Localiza o banco SQLite no filesystem."""
    candidates = [
        os.path.join("data", "db", "lol_datamatches.db"),
        os.path.join("..", "data", "db", "lol_datamatches.db"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]


def build_patch_clause(patches, tournaments=None):
    """Constrói cláusula SQL para filtro de patches e torneios."""
    clause = ""
    params = []
    if patches and "Todos" not in patches:
        placeholders = ",".join(["?" for _ in patches])
        clause += f" AND patch IN ({placeholders})"
        params.extend(patches)
    if tournaments and "Todos" not in tournaments:
        placeholders = ",".join(["?" for _ in tournaments])
        clause += f" AND league IN ({placeholders})"
        params.extend(tournaments)
    return clause, params


def get_team_stats(team_name, patches=None, tournaments=None):
    """
    Consulta completa de estatísticas de um time na camada Silver.
    Retorna dict com ~25 métricas agregadas + 11 listas históricas para distribuições.
    """
    db_path = get_db_path()
    patch_clause, patch_params = build_patch_clause(patches, tournaments)
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        base_where = f"position='team' AND teamname = ?{patch_clause}"
        params = [team_name] + patch_params

        # Média e valores principais
        c.execute(f"""
            SELECT 
                COUNT(DISTINCT gameid),
                SUM(CASE WHEN result='1' THEN 1 ELSE 0 END),
                AVG(teamkills), AVG(teamdeaths),
                AVG(dragons), AVG(towers), AVG(barons), AVG(heralds), AVG(inhibitors),
                AVG(gamelength),
                AVG(CASE WHEN firstblood=1 THEN 1.0 ELSE 0.0 END),
                AVG(CASE WHEN firstdragon=1 THEN 1.0 ELSE 0.0 END),
                AVG(CASE WHEN firstbaron=1 THEN 1.0 ELSE 0.0 END),
                AVG(CASE WHEN firstherald=1 THEN 1.0 ELSE 0.0 END),
                AVG(kpm), AVG(ckpm),
                AVG(totalgold), AVG(earnedgold), AVG(goldspent),
                AVG(total_cs), AVG(minionkills), AVG(damagetochampions), AVG(damagetakenperminute),
                AVG(goldat10), AVG(goldat15), AVG(goldat20), AVG(goldat25),
                AVG(golddiffat10), AVG(golddiffat15), AVG(golddiffat20), AVG(golddiffat25),
                AVG(csat10), AVG(csat15), AVG(csat20), AVG(csat25),
                AVG(csdiffat10), AVG(csdiffat15), AVG(csdiffat20), AVG(csdiffat25),
                AVG(wardsplaced), AVG(wardskilled), AVG(controlwardsbought), AVG(visionscore),
                AVG(cspm), AVG(earnedgoldshare),
                AVG(xpat10), AVG(xpat15), AVG(xpat20), AVG(xpat25),
                AVG(xpdiffat10), AVG(xpdiffat15), AVG(xpdiffat20), AVG(xpdiffat25),
                AVG(CASE WHEN firsttower=1 THEN 1.0 ELSE 0.0 END),
                AVG(CASE WHEN firstinhib=1 THEN 1.0 ELSE 0.0 END)
            FROM match_data_silver WHERE {base_where}
        """, params)

        row = c.fetchone()
        if not row or not row[0]:
            conn.close()
            return None

        stats = {
            "total_games": row[0], "wins": row[1],
            "win_rate": (row[1] / row[0] * 100) if row[0] else 0,
            "avg_kills": row[2] or 0, "avg_deaths": row[3] or 0,
            "avg_dragons": row[4] or 0, "avg_towers": row[5] or 0,
            "avg_barons": row[6] or 0, "avg_heralds": row[7] or 0, "avg_inhibitors": row[8] or 0,
            "avg_duration_s": row[9] or 0, "avg_duration_min": (row[9] or 0) / 60,
            "fb_rate": (row[10] or 0) * 100, "fd_rate": (row[11] or 0) * 100,
            "fbaron_rate": (row[12] or 0) * 100, "fherald_rate": (row[13] or 0) * 100,
            "avg_kpm": row[14] or 0, "avg_ckpm": row[15] or 0,
            "avg_totalgold": row[16] or 0, "avg_earnedgold": row[17] or 0, "avg_goldspent": row[18] or 0,
            "avg_cs": row[19] or 0, "avg_minionkills": row[20] or 0, 
            "avg_dmg_champs": row[21] or 0, "avg_dmg_taken_pm": row[22] or 0,
            
            # Timelines
            "goldat10": row[23] or 0, "goldat15": row[24] or 0, "goldat20": row[25] or 0, "goldat25": row[26] or 0,
            "golddiffat10": row[27] or 0, "golddiffat15": row[28] or 0, "golddiffat20": row[29] or 0, "golddiffat25": row[30] or 0,
            "csat10": row[31] or 0, "csat15": row[32] or 0, "csat20": row[33] or 0, "csat25": row[34] or 0,
            "csdiffat10": row[35] or 0, "csdiffat15": row[36] or 0, "csdiffat20": row[37] or 0, "csdiffat25": row[38] or 0,
            
            # Vision & Economy extra
            "wardsplaced": row[39] or 0, "wardskilled": row[40] or 0, 
            "controlwardsbought": row[41] or 0, "visionscore": row[42] or 0,
            "cspm": row[43] or 0, "earnedgoldshare": row[44] or 0,
            
            # XP
            "xpat10": row[45] or 0, "xpat15": row[46] or 0, "xpat20": row[47] or 0, "xpat25": row[48] or 0,
            "xpdiffat10": row[49] or 0, "xpdiffat15": row[50] or 0, "xpdiffat20": row[51] or 0, "xpdiffat25": row[52] or 0,
            
            # First Tower / Inhib
            "ft_rate": (row[53] or 0) * 100, "fi_rate": (row[54] or 0) * 100,
        }

        # Históricos para distribuições
        history_queries = {
            "kills_history": "teamkills",
            "dragons_history": "dragons",
            "towers_history": "towers",
            "barons_history": "barons",
            "heralds_history": "heralds",
            "inhibitors_history": "inhibitors",
            "kill_diff_history": "teamkills - teamdeaths",
            "ckpm_history": "ckpm",
            "kpm_history": "kpm",
            "earnedgold_pm_history": "earnedgold / (gamelength / 60.0)",   # EGPM
            "dmg_pm_history": "damagetochampions / (gamelength / 60.0)",   # DPM
        }
        for key, col in history_queries.items():
            safe_col = col.replace("gamelength", "NULLIF(gamelength, 0)")
            c.execute(f"SELECT {safe_col} FROM match_data_silver WHERE {base_where} ORDER BY gameid DESC", params)
            stats[key] = [r[0] for r in c.fetchall() if r[0] is not None]

        c.execute(f"SELECT gamelength / 60.0 FROM match_data_silver WHERE {base_where} ORDER BY gameid DESC", params)
        stats["duration_history"] = [r[0] for r in c.fetchall() if r[0] is not None]

        query_recent = f"""
            SELECT m1.result, m2.teamname 
            FROM match_data_silver m1
            JOIN match_data_silver m2 ON m1.gameid = m2.gameid AND m2.position = 'team' AND m1.teamname != m2.teamname
            WHERE m1.position='team' AND m1.teamname = ?{patch_clause.replace(' patch ', ' m1.patch ').replace(' league ', ' m1.league ')}
            ORDER BY m1.gameid DESC LIMIT 10
        """
        c.execute(query_recent, params)
        stats["recent_results"] = [{"result": r[0], "opponent": r[1]} for r in c.fetchall() if r[0] is not None]

        conn.close()
        return stats
    except Exception as e:
        print(f"  ⚠️ Erro ao consultar DB (team={team_name}): {e}")
        return None

def get_gold_team_stats(team_name, patches=None, tournaments=None):
    """
    Busca as métricas preditivas avançadas da camada Gold para um time.
    Versão dinâmica: calcula na hora para respeitar o filtro de patches.
    Threshold de Throw/Comeback aumentado para 2000g (vantagem real).
    """
    db_path = get_db_path()
    patch_clause, patch_params = build_patch_clause(patches, tournaments)
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        base_where = f"position='team' AND teamname = ?{patch_clause}"
        params = [team_name] + patch_params

        query = f"""
            SELECT 
                COUNT(DISTINCT gameid) as games_played,
                AVG(golddiffat15) as avg_golddiffat15,
                AVG(xpdiffat15) as avg_xpdiffat15,
                AVG(csdiffat15) as avg_csdiffat15,
                COALESCE((AVG(golddiffat15) + AVG(xpdiffat15) * 2 + AVG(csdiffat15) * 20) / 3, 0) AS egdi_score,
                
                -- Throw Rate (Perder jogo com > 2000g de vantagem aos 15)
                COALESCE(SUM(CASE WHEN golddiffat15 > 2000 AND result = '0' THEN 1.0 ELSE 0.0 END) / 
                NULLIF(SUM(CASE WHEN golddiffat15 > 2000 THEN 1.0 ELSE 0.0 END), 0) * 100.0, 0) as throw_rate,
                
                -- Comeback Rate (Ganhar jogo com < -2000g de desvantagem aos 15)
                COALESCE(SUM(CASE WHEN golddiffat15 < -2000 AND result = '1' THEN 1.0 ELSE 0.0 END) / 
                NULLIF(SUM(CASE WHEN golddiffat15 < -2000 THEN 1.0 ELSE 0.0 END), 0) * 100.0, 0) as comeback_rate,
                
                AVG(CAST(result AS INTEGER)) * 100.0 as win_rate
            FROM match_data_silver
            WHERE {base_where}
        """
        c.execute(query, params)
        row = c.fetchone()
        conn.close()
        return dict(row) if row and row['games_played'] > 0 else None
    except Exception as e:
        print(f"  ⚠️ Erro ao calcular Gold Team Stats dinâmico ({team_name}): {e}")
        return None

def get_gold_player_stats(team_name):
    """
    Busca as métricas individuais dos jogadores de um time na camada Gold.
    Retorna uma lista de dicionários.
    """
    db_path = get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM gold_player_metrics WHERE teamname = ?", (team_name,))
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"  ⚠️ Erro ao consultar Gold Player DB ({team_name}): {e}")
        return []

def get_global_baseline_stats(patches=None, tournaments=None):
    """
    Busca a média estrita do Mundial (World Average Baseline) 
    sem filtro de campeão. Usado como denominador para criar fatores preditivos.
    """
    db_path = get_db_path()
    patch_clause, patch_params = build_patch_clause(patches, tournaments)
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        base_where = f"position='team'{patch_clause}"
        query = f"""
            SELECT 
                AVG(teamkills) as avg_teamkills,
                AVG(dragons) as avg_team_dragons,
                AVG(firstblood) as avg_team_firstblood,
                AVG(firstdragon) as avg_team_firstdragon,
                AVG(firstherald) as avg_team_firstherald,
                AVG(towers) as avg_team_towers,
                AVG(barons) as avg_team_barons,
                AVG(gamelength) as avg_gamelength
            FROM match_data_silver
            WHERE {base_where}
        """
        c.execute(query, patch_params)
        row = c.fetchone()
        conn.close()
        
        return dict(row) if row else None
    except Exception as e:
        print(f"  ⚠️ Erro ao consultar Baselines Globais: {e}")
        return None

def get_platinum_champion_stats(team_name, champion):
    """
    Busca as estatísticas na camada Platinum de um determinado campeão para um time específico,
    além das estatísticas globais (Mundo) para o mesmo campeão como comparação.
    Como o sample size por patch é pequeno, busca a agregação geral ('ALL').
    """
    db_path = get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Team stats with this champion
        c.execute("SELECT * FROM champion_stats_platinum WHERE teamname = ? AND champion = ? AND patch = 'ALL'", (team_name, champion))
        team_row = c.fetchone()
        
        # World stats with this champion
        c.execute("SELECT * FROM champion_stats_platinum WHERE teamname = 'WORLD' AND champion = ? AND patch = 'ALL'", (champion,))
        world_row = c.fetchone()
        
        conn.close()
        
        return {
            "team_stats": dict(team_row) if team_row else None,
            "world_stats": dict(world_row) if world_row else None
        }
    except Exception as e:
        print(f"  ⚠️ Erro ao consultar Platinum DB ({team_name}, {champion}): {e}")
        return {"team_stats": None, "world_stats": None}





def get_side_stats(team_name, patches=None, tournaments=None):
    """Retorna vitórias e jogos por lado (Blue/Red) para um time."""
    db_path = get_db_path()
    patch_clause, patch_params = build_patch_clause(patches, tournaments)
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        base_where = f"position='team' AND teamname = ?{patch_clause}"
        params = [team_name] + patch_params

        query = f"""
            SELECT 
                side,
                COUNT(*) as games,
                SUM(CASE WHEN result='1' THEN 1 ELSE 0 END) as wins
            FROM match_data_silver
            WHERE {base_where}
            GROUP BY side
        """
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"  ⚠️ Erro ao consultar Side Stats ({team_name}): {e}")
        return []


def get_league_context(league_name):
    """Busca o baseline da liga (média de abates, side bias)."""
    db_path = get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        query = """
            SELECT 
                AVG(teamkills + teamdeaths) as avg_total_kills,
                AVG(CASE WHEN side='Blue' AND result='1' THEN 1.0 WHEN side='Blue' THEN 0.0 END) * 100 as blue_win_rate,
                AVG(gamelength) / 60.0 as avg_duration,
                COUNT(*) / 2 as total_games
            FROM match_data_silver
            WHERE position='team' AND league = ?
        """
        c.execute(query, (league_name,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row and row['total_games'] > 0 else None
    except Exception as e:
        print(f"  ⚠️ Erro ao consultar League Context ({league_name}): {e}")
        return None


def get_objective_win_correlations(patches=None, tournaments=None):
    """Calcula a correlação global entre o primeiro objetivo e a vitória final."""
    db_path = get_db_path()
    patch_clause, patch_params = build_patch_clause(patches, tournaments)
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Win rates por primeiro objetivo
        query1 = f"""
            SELECT 
                AVG(CASE WHEN firstblood = 1 AND result = '1' THEN 1.0 WHEN firstblood = 1 THEN 0.0 END) * 100 as fb_wr,
                AVG(CASE WHEN firstdragon = 1 AND result = '1' THEN 1.0 WHEN firstdragon = 1 THEN 0.0 END) * 100 as fd_wr,
                AVG(CASE WHEN firstbaron = 1 AND result = '1' THEN 1.0 WHEN firstbaron = 1 THEN 0.0 END) * 100 as fbaron_wr,
                AVG(CASE WHEN firstherald = 1 AND result = '1' THEN 1.0 WHEN firstherald = 1 THEN 0.0 END) * 100 as fherald_wr
            FROM match_data_silver
            WHERE position='team'{patch_clause}
        """
        c.execute(query1, patch_params)
        row1 = dict(c.fetchone())
        
        # Conversão de Vantagem de Ouro (Large Lead > 2k aos 15m)
        query2 = f"""
            SELECT AVG(CASE WHEN golddiffat15 > 2000 AND result = '1' THEN 1.0 WHEN golddiffat15 > 2000 THEN 0.0 END) * 100 as large_lead_wr
            FROM match_data_silver
            WHERE position='team'{patch_clause} AND golddiffat15 IS NOT NULL
        """
        c.execute(query2, patch_params)
        row2 = c.fetchone()
        
        # Soul Win Rate (4 dragões)
        query3 = f"""
            SELECT AVG(CASE WHEN dragons >= 4 AND result = '1' THEN 1.0 WHEN dragons >= 4 THEN 0.0 END) * 100 as soul_wr
            FROM match_data_silver
            WHERE position='team'{patch_clause}
        """
        c.execute(query3, patch_params)
        row3 = c.fetchone()
        
        conn.close()
        
        # Merge results
        res = row1
        res['large_lead_wr'] = row2['large_lead_wr'] if row2 else 0
        res['soul_wr'] = row3['soul_wr'] if row3 else 0
        return res
    except Exception as e:
        print(f"  ⚠️ Erro ao consultar Correlações de Objetivos: {e}")
        return None


def get_player_kill_stats(team_name, patches=None, tournaments=None):
    """
    Retorna estatísticas de kills/deaths/assists por jogador de um time.
    Usado para mercados de Over/Under de abates por jogador.
    """
    db_path = get_db_path()
    patch_clause, patch_params = build_patch_clause(patches, tournaments)
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        query = f"""
            SELECT 
                playername,
                position,
                teamname,
                AVG(kills) as avg_kills,
                AVG(deaths) as avg_deaths,
                AVG(assists) as avg_assists,
                MIN(kills) as min_kills,
                MAX(kills) as max_kills,
                COUNT(*) as games
            FROM match_data_silver
            WHERE position != 'team' AND teamname = ?{patch_clause}
            GROUP BY playername, position
            ORDER BY avg_kills DESC
        """
        params = [team_name] + patch_params
        c.execute(query, params)
        rows = c.fetchall()
        
        # Também busca o histórico de kills por jogador
        result = []
        for row in rows:
            player_data = dict(row)
            c.execute(f"""
                SELECT kills FROM match_data_silver
                WHERE playername = ? AND teamname = ?{patch_clause}
                ORDER BY gameid DESC
            """, [player_data['playername'], team_name] + patch_params)
            player_data['kills_history'] = [r[0] for r in c.fetchall() if r[0] is not None]
            result.append(player_data)
        
        conn.close()
        return result
    except Exception as e:
        print(f"  ⚠️ Erro ao consultar Player Kill Stats ({team_name}): {e}")
        return []


def get_top_ckpm_teams(min_games=10, limit=10):
    """
    Retorna os top N times por CKPM (Combined Kills Per Minute).
    Usado como referência no Pace Context.
    """
    db_path = get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        query = """
            SELECT 
                teamname,
                AVG(ckpm) as avg_ckpm,
                COUNT(DISTINCT gameid) as games
            FROM match_data_silver 
            WHERE position='team'
            GROUP BY teamname
            HAVING games >= ?
            ORDER BY avg_ckpm DESC
            LIMIT ?
        """
        c.execute(query, (min_games, limit))
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"  ⚠️ Erro ao consultar Top CKPM Teams: {e}")
        return []



def get_first_inhib_proxy(team_name, patches=None, tournaments=None):
    """
    Proxy para First Inhibitor usando inhibitors > 0 como indicador,
    já que a coluna firstinhib é sempre 0 no banco de dados atual.
    Retorna a % de jogos onde o time destruiu pelo menos 1 inibidor.
    """
    db_path = get_db_path()
    patch_clause, patch_params = build_patch_clause(patches, tournaments)
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        query = f"""
            SELECT 
                COUNT(*) as total_games,
                SUM(CASE WHEN inhibitors > 0 THEN 1 ELSE 0 END) as games_with_inhib,
                AVG(CASE WHEN inhibitors > 0 THEN 1.0 ELSE 0.0 END) * 100 as inhib_rate,
                AVG(inhibitors) as avg_inhibitors
            FROM match_data_silver
            WHERE position='team' AND teamname = ?{patch_clause}
        """
        params = [team_name] + patch_params
        c.execute(query, params)
        row = c.fetchone()
        conn.close()
        
        if not row or not row[0]:
            return None
        
        return {
            "total_games": row[0],
            "games_with_inhib": row[1],
            "inhib_rate": row[2] or 0,
            "avg_inhibitors": row[3] or 0,
        }
    except Exception as e:
        print(f"  ⚠️ Erro ao consultar First Inhib Proxy ({team_name}): {e}")
        return None
