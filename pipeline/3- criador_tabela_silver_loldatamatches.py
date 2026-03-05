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
            
            # Verifica se a coluna 'patch' já existe
            cursor.execute("PRAGMA table_info(match_data_silver)")
            colunas_existentes = [col[1] for col in cursor.fetchall()]
            
            if colunas_existentes and "patch" not in colunas_existentes:
                print("⚠️  Esquema antigo detectado (coluna 'patch' ausente). Recriando tabela Silver...")
                cursor.execute("DROP TABLE match_data_silver")
                colunas_existentes = []

            print("🏗️  Criando estrutura da tabela 'match_data_silver'...")
            
            # Cria a tabela com UNIQUE constraint para upsert
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS match_data_silver (
                    gameid TEXT,
                    participantid INTEGER,
                    patch TEXT,
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
                    inhibitors INTEGER,
                    UNIQUE(gameid, participantid)
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