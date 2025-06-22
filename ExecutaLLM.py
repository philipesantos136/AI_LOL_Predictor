import csv
import sqlite3
import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

# Configuração da API Key do Gemini
# Cria sua chave do Gemini no google ai studio
# Copie a sua chave, abra um terminal e digite: 
# setx GEMINI_API_KEY your_api_key
# Caso não encontre a variável, lembre de reiniciar o terminal

api_key = os.environ.get('GEMINI_API_KEY')

print(f'Sua chave configurada é: {api_key}')

# Instanciação do LLM através do Gemini
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.8,
    google_api_key=api_key
)

# Criação do parser para a saída do modelo de linguagem
output_parser = StrOutputParser()

# Nome do banco de dados SQLite
db_file = "lol_datamatches.db"
tabela = "match_data_silver"
time1 = "LOUD"
time2 = "paiN Gaming"

def dsa_gera_analises():
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Query para buscar dados do time1
    query_time1 = f"""
        SELECT
            side, position, champion, result, kills, deaths, assists,
            teamkills, teamdeaths, firstblood, firstdragon, firstherald,
            firstbaron, dragons, heralds, barons, gamelength, kpm, ckpm,
            totalgold, earnedgold, goldspent, total_cs, minionkills,
            damagetochampions, damagetakenperminute, towers, inhibitors
        FROM {tabela}
        WHERE teamname == "{time1}"
    """
    
    # Query para buscar dados do time2
    query_time2 = f"""
        SELECT
            side, position, champion, result, kills, deaths, assists,
            teamkills, teamdeaths, firstblood, firstdragon, firstherald,
            firstbaron, dragons, heralds, barons, gamelength, kpm, ckpm,
            totalgold, earnedgold, goldspent, total_cs, minionkills,
            damagetochampions, damagetakenperminute, towers, inhibitors
        FROM {tabela}
        WHERE teamname == "{time2}"
    """
    
    # Executa as queries
    cursor.execute(query_time1)
    dados_time1 = cursor.fetchall()
    
    cursor.execute(query_time2)
    dados_time2 = cursor.fetchall()
    
    # Processa dados do time1
    estatisticas_time1 = []
    for row in dados_time1:
        estatisticas_time1.append({
            'side': row['side'],
            'champion': row['champion'],
            'result': row['result'],
            'kills': row['kills'],
            'deaths': row['deaths'],
            'assists': row['assists'],
            'teamkills': row['teamkills'],
            'teamdeaths': row['teamdeaths'],
            'firstblood': row['firstblood'],
            'firstdragon': row['firstdragon'],
            'firstherald': row['firstherald'],
            'firstbaron': row['firstbaron'],
            'dragons': row['dragons'],
            'heralds': row['heralds'],
            'barons': row['barons'],
            'gamelength': row['gamelength'],
            'kpm': row['kpm'],
            'ckpm': row['ckpm'],
            'totalgold': row['totalgold'],
            'earnedgold': row['earnedgold'],
            'goldspent': row['goldspent'],
            'total_cs': row['total_cs'],
            'minionkills': row['minionkills'],
            'damagetochampions': row['damagetochampions'],
            'damagetakenperminute': row['damagetakenperminute'],
            'towers': row['towers'],
            'inhibitors': row['inhibitors']
        })
    
    # Processa dados do time2
    estatisticas_time2 = []
    for row in dados_time2:
        estatisticas_time2.append({
            'side': row['side'],
            'champion': row['champion'],
            'result': row['result'],
            'kills': row['kills'],
            'deaths': row['deaths'],
            'assists': row['assists'],
            'teamkills': row['teamkills'],
            'teamdeaths': row['teamdeaths'],
            'firstblood': row['firstblood'],
            'firstdragon': row['firstdragon'],
            'firstherald': row['firstherald'],
            'firstbaron': row['firstbaron'],
            'dragons': row['dragons'],
            'heralds': row['heralds'],
            'barons': row['barons'],
            'gamelength': row['gamelength'],
            'kpm': row['kpm'],
            'ckpm': row['ckpm'],
            'totalgold': row['totalgold'],
            'earnedgold': row['earnedgold'],
            'goldspent': row['goldspent'],
            'total_cs': row['total_cs'],
            'minionkills': row['minionkills'],
            'damagetochampions': row['damagetochampions'],
            'damagetakenperminute': row['damagetakenperminute'],
            'towers': row['towers'],
            'inhibitors': row['inhibitors']
        })
    
    # Criação do template de prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"Você é um analista especializado em e-sports de League of Legends. Analise os dados históricos dos dois times e forneça uma análise detalhada em português do Brasil sobre qual time tem maior probabilidade de vencer: {time1} vs {time2}. Considere estatísticas como KDA, objetivos conquistados, economia do jogo, e performance geral."),
        ("user", "Dados dos times para análise: {dados_completos}")
    ])
    
    # Cria a consulta completa com todos os dados
    consulta_completa = f"""
    ANÁLISE COMPARATIVA - {time1} vs {time2}
    
    === DADOS DO {time1} ===
    {estatisticas_time1}
    
    === DADOS DO {time2} ===
    {estatisticas_time2}
    
    analise estes dados e forneça sua previsão sobre qual time tem maior probabilidade de vitória, justificando com base nas estatísticas apresentadas.
    Não repita informações.
    Traga a probabilidade de qual time pegará:
        firsttorre, 
        firstdragon, 
        firstherald, 
        firstbarão, 
        firstblood, 
        firsttower, 
        firstinhibitor    
    
    """
    
    # Definição da cadeia de execução
    chain = prompt | llm | output_parser
    
    # Gera a análise completa
    response = chain.invoke({'dados_completos': consulta_completa})
    
    conn.close()
    return response

# Uso
resultado = dsa_gera_analises()
print(resultado)
