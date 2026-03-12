import sqlite3
import os

def criar_tabelas_gold():
    """
    Agrupa dados da camada Silver (match_data_silver) e cria
    as tabelas gold_team_metrics e gold_player_metrics.
    Foco em indicadores preditivos para apostas em League of Legends.
    """
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_dir = os.path.join(ROOT_DIR, "data", "db")
    db_file = os.path.join(db_dir, "lol_datamatches.db")

    print("Iniciando criação das tabelas Gold...")

    try:
        with sqlite3.connect(db_file) as conexao:
            cursor = conexao.cursor()

            print(f"🔌 Conectado ao banco '{db_file}' com sucesso.")

            # --- Criação da Tabela GOLD TEAM METRICS ---
            print("🏗️  Criando estrutura da tabela 'gold_team_metrics'...")
            cursor.execute("DROP TABLE IF EXISTS gold_team_metrics")
            
            # Nota sobre First Blood/Dragon: os valores na tabela silver são inteiros (1 ou 0).
            # O AVG() deles retornará a porcentagem (ex: 0.6 = 60%).
            
            # Nota sobre as Wards por Objetivo: usamos MAX(1, feature) para evitar divisão por zero 
            # no cálculo nos casos em que a equipe tenha 0 abates/dragões/barões, etc.
            
            query_gold_team = '''
                CREATE TABLE gold_team_metrics AS
                SELECT 
                    teamname,
                    COUNT(DISTINCT gameid) as games_played,
                    
                    -- Early Game Dominance Index (EGDI = Média de Diferença de Gold, XP, CS @15)
                    AVG(golddiffat15) as avg_golddiffat15,
                    AVG(xpdiffat15) as avg_xpdiffat15,
                    AVG(csdiffat15) as avg_csdiffat15,
                    (AVG(golddiffat15) + AVG(xpdiffat15) * 2 + AVG(csdiffat15) * 20) / 3 AS egdi_score, -- Ponderação simples
                    
                    -- Pace & Bloodiness
                    AVG(gamelength) as avg_gamelength,
                    AVG(kpm) as avg_kpm,
                    AVG(ckpm) as avg_ckpm,
                    
                    -- Objective Rates (Frequência de conquistar o primeiro objetivo)
                    AVG(firstblood) as first_blood_rate,
                    AVG(firstdragon) as first_dragon_rate,
                    AVG(firstherald) as first_herald_rate,
                    AVG(firstbaron) as first_baron_rate,
                    
                    -- Vision Control & Ratios
                    AVG(visionscore / (gamelength / 60.0)) as vision_score_per_minute,
                    AVG(wardskilled) as avg_wards_killed,
                    AVG(wardsplaced) as avg_wards_placed,
                    
                    -- Wards required per objective/kill (Eficiência de visão)
                    AVG(CAST(wardsplaced AS REAL) / MAX(1, teamkills)) as wards_per_kill,
                    AVG(CAST(wardsplaced AS REAL) / MAX(1, dragons)) as wards_per_dragon,
                    AVG(CAST(wardsplaced AS REAL) / MAX(1, barons)) as wards_per_baron,
                    AVG(CAST(wardsplaced AS REAL) / MAX(1, heralds)) as wards_per_herald,
                    
                    -- Throw Rate / Comeback (Vitórias condicionadas a vantagem aos 15)
                    -- Definimos 'Throw' como ter >1000 de vantagem e perder.
                    -- Definimos 'Comeback' como ter < -1000 de desvantagem e ganhar.
                    SUM(CASE WHEN golddiffat15 > 1000 AND result = '0' THEN 1 ELSE 0 END) * 1.0 / NULLIF(SUM(CASE WHEN golddiffat15 > 1000 THEN 1 ELSE 0 END), 0) as throw_rate,
                    SUM(CASE WHEN golddiffat15 < -1000 AND result = '1' THEN 1 ELSE 0 END) * 1.0 / NULLIF(SUM(CASE WHEN golddiffat15 < -1000 THEN 1 ELSE 0 END), 0) as comeback_rate,
                    
                    -- General Winrate
                    AVG(CAST(result AS INTEGER)) as win_rate
                    
                FROM match_data_silver
                WHERE position = 'team'
                GROUP BY teamname
                HAVING COUNT(DISTINCT gameid) >= 5; -- Apenas times com amostra mínima (5+ jogos)
            '''
            cursor.execute(query_gold_team)
            print("✅ Tabela 'gold_team_metrics' criada.")

            # --- Criação da Tabela GOLD PLAYER METRICS ---
            print("🏗️  Criando estrutura da tabela 'gold_player_metrics'...")
            cursor.execute("DROP TABLE IF EXISTS gold_player_metrics")
            
            # Foco em KDA, Kill Participation e Carry Potential
            query_gold_player = '''
                CREATE TABLE gold_player_metrics AS
                SELECT 
                    playername,

                    teamname,
                    position,
                    COUNT(DISTINCT gameid) as games_played,
                    
                    -- Carry Potential (Dano por Ouro e Participação)
                    AVG(earnedgoldshare) as avg_earned_gold_share,
                    AVG(damagetochampions / MAX(1, earnedgold)) as damage_per_gold,
                    AVG(cspm) as avg_cspm,
                    
                    -- KDA & Kill Participation
                    SUM(kills) as total_kills,
                    SUM(deaths) as total_deaths,
                    SUM(assists) as total_assists,
                    CAST(SUM(kills) + SUM(assists) AS REAL) / MAX(1, SUM(deaths)) as kda_ratio,
                    AVG(CAST(kills + assists AS REAL) / MAX(1, teamkills)) as kill_participation,
                    
                    -- Vision Individual
                    AVG(visionscore / (gamelength / 60.0)) as vision_score_per_minute,
                    AVG(controlwardsbought) as avg_control_wards,
                    
                    AVG(CAST(result AS INTEGER)) as win_rate
                FROM match_data_silver
                WHERE position != 'team'
                GROUP BY playername, teamname, position
                HAVING COUNT(DISTINCT gameid) >= 3; -- Jogadores com amostra mínima
            '''
            cursor.execute(query_gold_player)
            print("✅ Tabela 'gold_player_metrics' criada.")
            
    except sqlite3.Error as e:
        print(f"❌ Erro de banco de dados: {e}")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado: {e}")
    finally:
        print("✨ Processo Gold finalizado!")

if __name__ == "__main__":
    criar_tabelas_gold()
