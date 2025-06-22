import sqlite3


# Conecta ao banco
conexao = sqlite3.connect("lol_datamatches.db")
cursor = conexao.cursor()

# Cria a tabela
cursor.execute('''
    CREATE TABLE IF NOT EXISTS match_data_silver (
        league TEXT,
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

# Fecha a conexão
conexao.close()