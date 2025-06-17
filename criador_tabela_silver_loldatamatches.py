import sqlite3
import os

# Verifica o caminho onde o banco será salvo
db_path = os.path.abspath("lol_datamatches.db")
print(f"📍 Banco será criado/em aberto em: {db_path}")

# Conecta ao banco
conexao = sqlite3.connect("lol_datamatches.db")
cursor = conexao.cursor()

# Cria a tabela
cursor.execute('''
    CREATE TABLE IF NOT EXISTS match_data_silver (
        side TEXT,
        position TEXT,
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

# Confirma a criação
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("✅ Tabelas existentes no banco:", cursor.fetchall())

# Fecha a conexão
conexao.close()