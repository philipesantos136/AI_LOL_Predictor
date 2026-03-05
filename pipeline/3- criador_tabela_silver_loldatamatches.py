import sqlite3

def criar_tabela_silver():
    """
    Cria a estrutura da tabela match_data_silver no banco de dados SQLite.
    Esta tabela representa a camada Silver (dados refinados).
    """
    db_file = "lol_datamatches.db"
    
    print("Iniciando criação da tabela Silver...")
    
    # O bloco 'with' garante o fechamento seguro da conexão mesmo em caso de erro
    try:
        with sqlite3.connect(db_file) as conexao:
            cursor = conexao.cursor()
            
            print(f"🔌 Conectado ao banco '{db_file}' com sucesso.")
            print("🏗️  Criando estrutura da tabela 'match_data_silver'...")
            
            # Cria a tabela
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS match_data_silver (
                    league TEXT,
                    split TEXT,
                    side TEXT,
                    position TEXT,
                    teamname TEXT,
                    champion TEXT,
                    result TEXT,
                    kills INTEGER,
                    deaths INTEGER,
                    assists INTEGER,
                    teamkills INTEGER,
                    teamdeaths INTEGER,
                    firstblood INTEGER,
                    firstdragon INTEGER,
                    firstherald INTEGER,
                    firstbaron INTEGER,
                    dragons INTEGER,
                    heralds INTEGER,
                    barons INTEGER,
                    gamelength REAL,
                    kpm REAL,
                    ckpm REAL,
                    totalgold INTEGER,
                    earnedgold INTEGER,
                    goldspent INTEGER,
                    total_cs INTEGER,
                    minionkills INTEGER,
                    damagetochampions INTEGER,
                    damagetakenperminute REAL,
                    towers INTEGER,
                    inhibitors INTEGER
                );
            ''')
            
            print("✅ Tabela 'match_data_silver' verificada/criada com sucesso.")
            
    except sqlite3.Error as e:
        print(f"❌ Erro de banco de dados ao tentar criar a tabela: {e}")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado: {e}")
    finally:
        print("✨ Processo de criação da tabela finalizado!")

if __name__ == "__main__":
    criar_tabela_silver()