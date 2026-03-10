import sqlite3
import os

def criar_tabela_platinum():
    """
    Cria a estrutura da tabela champion_stats_platinum no banco de dados SQLite.
    Esta tabela representa a camada Platinum (dados de agregação para Machine Learning e Insights Avançados).
    """
    db_dir = os.path.join("data", "db")
    os.makedirs(db_dir, exist_ok=True)
    db_file = os.path.join(db_dir, "lol_datamatches.db")
    
    print("Iniciando criação da tabela Platinum...")
    
    try:
        with sqlite3.connect(db_file) as conexao:
            cursor = conexao.cursor()
            
            print(f"🔌 Conectado ao banco '{db_file}' com sucesso.")
            
            print("⚠️ Re-criando tabela Platinum para garantir schema atualizado...")
            cursor.execute("DROP TABLE IF EXISTS champion_stats_platinum")

            print("🏗️  Criando estrutura da tabela 'champion_stats_platinum'...")
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS champion_stats_platinum (
                    teamname TEXT,
                    champion TEXT,
                    patch TEXT,
                    matches_played INTEGER,
                    wins INTEGER,
                    winrate REAL,
                    avg_kills REAL,
                    avg_deaths REAL,
                    avg_assists REAL,
                    kda REAL,
                    firstblood_rate REAL,
                    avg_goldat15 REAL,
                    avg_csat15 REAL,
                    avg_damagetochampions REAL,
                    avg_visionscore REAL,
                    avg_teamkills REAL,
                    avg_team_dragons REAL,
                    avg_team_firstdragon REAL,
                    avg_team_firstherald REAL,
                    avg_team_towers REAL,
                    avg_team_barons REAL,
                    avg_gamelength REAL,
                    UNIQUE(teamname, champion, patch)
                );
            ''')
            
            print("✅ Tabela 'champion_stats_platinum' criada com sucesso.")
            
    except sqlite3.Error as e:
        print(f"❌ Erro de banco de dados ao tentar criar a tabela: {e}")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado: {e}")
    finally:
        print("✨ Processo de criação da tabela finalizado!")

if __name__ == "__main__":
    criar_tabela_platinum()
