import sqlite3

conexao = sqlite3.connect("lol_datamatches.db")
cursor = conexao.cursor()

cursor.execute('''
INSERT INTO match_data_silver (
    league,
    split,
    side,
    position,
    teamname,
    champion,
    result,
    kills,
    deaths,
    assists,
    teamkills,
    teamdeaths,
    firstblood,
    firstdragon,
    firstherald,
    firstbaron,
    dragons,
    heralds,
    barons,
    gamelength,
    kpm,
    ckpm,
    totalgold,
    earnedgold,
    goldspent,
    total_cs,
    minionkills,
    damagetochampions,
    damagetakenperminute,
    towers,
    inhibitors
)
SELECT
    league,
    split,
    side,
    position,
    teamname,
    champion,
    result,
    kills,
    deaths,
    assists,
    teamkills,
    teamdeaths,
    firstblood,
    firstdragon,
    firstherald,
    firstbaron,
    dragons,
    heralds,
    barons,
    gamelength,
    "team kpm",
    ckpm,
    totalgold,
    earnedgold,
    goldspent,
    "total cs",
    minionkills,
    damagetochampions,
    damagetakenperminute,
    towers,
    inhibitors
FROM "2025_lol_matches";
''')

conexao.commit()
conexao.close()