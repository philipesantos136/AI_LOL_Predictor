"""
charts/data_provider.py — Repository Pattern: acesso isolado ao banco SQLite Silver.
Toda leitura de dados passa por aqui. Nenhum outro módulo acessa o banco diretamente.
"""

import sqlite3
import os


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


def build_patch_clause(patches):
    """Constrói cláusula SQL para filtro de patches."""
    if not patches or "Todos" in patches:
        return "", []
    placeholders = ",".join(["?" for _ in patches])
    return f" AND patch IN ({placeholders})", list(patches)


def get_team_stats(team_name, patches=None):
    """
    Consulta completa de estatísticas de um time na camada Silver.
    Retorna dict com ~25 métricas agregadas + 11 listas históricas para distribuições.
    """
    db_path = get_db_path()
    patch_clause, patch_params = build_patch_clause(patches)
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
                AVG(total_cs), AVG(damagetochampions), AVG(damagetakenperminute)
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
            "avg_cs": row[19] or 0, "avg_dmg_champs": row[20] or 0, "avg_dmg_taken_pm": row[21] or 0,
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

        c.execute(f"SELECT result FROM match_data_silver WHERE {base_where} ORDER BY gameid DESC LIMIT 10", params)
        stats["recent_results"] = [r[0] for r in c.fetchall() if r[0] is not None]

        conn.close()
        return stats
    except Exception as e:
        print(f"  ⚠️ Erro ao consultar DB (team={team_name}): {e}")
        return None
