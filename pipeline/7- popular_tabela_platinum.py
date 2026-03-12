import sqlite3
import os

def popular_tabela_platinum():
    """
    Popula a tabela 'champion_stats_platinum' com agregações estatísticas.
    Calcula métricas como winrate, KDA e ouro por time/campeão,
    além de médias do 'WORLD' (Mundo) e agregações de patches.
    """
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_dir = os.path.join(ROOT_DIR, "data", "db")
    db_file = os.path.join(db_dir, "lol_datamatches.db")
    
    if not os.path.exists(db_file):
        print(f"❌ Erro: O banco de dados '{db_file}' não foi encontrado.")
        return
        
    print("⏳ Populando tabela Platinum...")
    
    try:
        with sqlite3.connect(db_file) as conexao:
            cursor = conexao.cursor()
            
            # Limpa tabela antes de inserir
            cursor.execute("DELETE FROM champion_stats_platinum")
            
            # Helper for inserting aggregated rows
            def inserir_agregacao(group_by_fields, patch_val=None, team_val=None):
                
                # Setup select and group by clauses
                select_team = f"'{team_val}' as teamname" if team_val else "p.teamname"
                select_patch = f"'{patch_val}' as patch" if patch_val else "p.patch"
                
                # Replace unqualified fields in group_by_fields with p. prefixes
                group_by_safe = group_by_fields.replace("teamname", "p.teamname").replace("champion", "p.champion").replace("patch", "p.patch")
                
                query = f"""
                    INSERT INTO champion_stats_platinum 
                    (teamname, champion, patch, matches_played, wins, winrate, 
                     avg_kills, avg_deaths, avg_assists, kda, firstblood_rate,
                     avg_goldat15, avg_csat15, avg_damagetochampions, avg_visionscore,
                     avg_teamkills, avg_team_dragons, avg_team_firstdragon, avg_team_firstherald, avg_team_towers, avg_team_barons, avg_gamelength)
                    SELECT 
                        {select_team},
                        p.champion, 
                        {select_patch},
                        COUNT(*) as matches_played,
                        SUM(CAST(p.result AS INTEGER)) as wins,
                        AVG(CAST(p.result AS INTEGER)) as winrate,
                        AVG(p.kills) as avg_kills,
                        AVG(p.deaths) as avg_deaths,
                        AVG(p.assists) as avg_assists,
                        CAST(SUM(p.kills) + SUM(p.assists) AS REAL) / CASE WHEN SUM(p.deaths) = 0 THEN 1 ELSE SUM(p.deaths) END as kda,
                        AVG(p.firstblood) as firstblood_rate,
                        AVG(p.goldat15) as avg_goldat15,
                        AVG(p.csat15) as avg_csat15,
                        AVG(p.damagetochampions) as avg_damagetochampions,
                        AVG(p.visionscore) as avg_visionscore,
                        AVG(t.teamkills) as avg_teamkills,
                        AVG(t.dragons) as avg_team_dragons,
                        AVG(t.firstdragon) as avg_team_firstdragon,
                        AVG(t.firstherald) as avg_team_firstherald,
                        AVG(t.towers) as avg_team_towers,
                        AVG(t.barons) as avg_team_barons,
                        AVG(t.gamelength) as avg_gamelength
                    FROM match_data_silver p
                    INNER JOIN match_data_silver t
                        ON p.gameid = t.gameid AND p.teamname = t.teamname
                    WHERE p.champion IS NOT NULL AND p.position != 'team' AND t.position = 'team'
                    GROUP BY {group_by_safe}
                """
                cursor.execute(query)

            # 1. Per Team, Per Champion, Per Patch
            print("Inserindo Time x Campeão por Patch...")
            inserir_agregacao("teamname, champion, patch")
            
            # 2. Per Team, Per Champion, ALL Patches
            print("Inserindo Time x Campeão Geral (ALL Patches)...")
            inserir_agregacao("teamname, champion", patch_val='ALL')
            
            # 3. WORLD (all teams), Per Champion, Per Patch
            print("Inserindo Mundo x Campeão por Patch...")
            inserir_agregacao("champion, patch", team_val='WORLD')
            
            # 4. WORLD (all teams), Per Champion, ALL Patches
            print("Inserindo Mundo x Campeão Geral (ALL Patches)...")
            inserir_agregacao("champion", patch_val='ALL', team_val='WORLD')
            
            conexao.commit()
            print("✅ Tabela 'champion_stats_platinum' populada com sucesso!")

    except sqlite3.Error as e:
        print(f"❌ Erro de banco de dados ao popular a tabela: {e}")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    popular_tabela_platinum()
