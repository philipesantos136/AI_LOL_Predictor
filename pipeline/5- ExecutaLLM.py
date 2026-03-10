import sqlite3
import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

# Carrega as variáveis do arquivo .env
load_dotenv()

def obter_dados_time(cursor, time_nome, patches=None):
    """
    Busca os dados de um time específico na tabela Silver de forma segura
    utilizando query parametrizada para evitar SQL Injection.
    """
    query = """
        SELECT
            patch, split, side, position, champion, result, kills, deaths, assists,
            teamkills, teamdeaths, firstblood, firstdragon, firstherald,
            firstbaron, dragons, heralds, barons, gamelength, kpm, ckpm,
            totalgold, earnedgold, goldspent, total_cs, minionkills,
            damagetochampions, damagetakenperminute, towers, inhibitors
        FROM match_data_silver
        WHERE teamname = ?
    """
    
    params = [time_nome]
    
    if patches and "Todos" not in patches:
        # Adiciona o filtro de patches se não for "Todos"
        placeholders = ", ".join(["?" for _ in patches])
        query += f" AND patch IN ({placeholders})"
        params.extend(patches)
        
    cursor.execute(query, tuple(params))
    return cursor.fetchall()

def formatar_estatisticas(linhas_db):
    """
    Converte as linhas do banco em um formato CSV compacto para economizar tokens.
    """
    colunas = [
        'patch', 'split', 'side', 'champion', 'result', 'kills', 'deaths', 'assists',
        'teamkills', 'teamdeaths', 'firstblood', 'firstdragon', 'firstherald',
        'firstbaron', 'dragons', 'heralds', 'barons', 'gamelength', 'kpm', 'ckpm',
        'totalgold', 'earnedgold', 'goldspent', 'total_cs', 'minionkills',
        'damagetochampions', 'damagetakenperminute', 'towers', 'inhibitors'
    ]
    
    header = ",".join(colunas)
    linhas = []
    for row in linhas_db:
        # Converte cada linha em uma string separada por vírgula
        valores = [str(row[col]) for col in colunas]
        linhas.append(",".join(valores))
    
    return header + "\n" + "\n".join(linhas)

def dsa_gera_analises(time1, time2, patches=None):
    # 1. Configuração do LLM (Gemini via API Key)
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("❌ Erro: GEMINI_API_KEY não encontrada no arquivo .env")
        
    print(f"🤖 Iniciando motor de IA do Google Gemini...")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        temperature=0.0,
        google_api_key=api_key
    )
    
    # 2. Conexão com o Banco de Dados
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_file = os.path.join(ROOT_DIR, "data", "db", "lol_datamatches.db")
    if not os.path.exists(db_file):
        raise FileNotFoundError(f"❌ Banco de dados '{db_file}' não encontrado. Execute o pipeline de importação primeiro.")
        
    print("🔌 Buscando estatísticas dos times no banco de dados...")
    with sqlite3.connect(db_file) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Busca os dados usando queries seguras (evita SQL Injection)
        dados_time1_brutos = obter_dados_time(cursor, time1, patches)
        dados_time2_brutos = obter_dados_time(cursor, time2, patches)
        
    print(f"📊 Registros encontrados: {time1} ({len(dados_time1_brutos)} partidas), {time2} ({len(dados_time2_brutos)} partidas).")

    # 3. Formatação dos dados
    estatisticas_time1 = formatar_estatisticas(dados_time1_brutos)
    estatisticas_time2 = formatar_estatisticas(dados_time2_brutos)
    
    output_parser = StrOutputParser()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"Você é um analista especializado em e-sports de League of Legends. Analise os dados históricos dos dois times e forneça uma análise detalhada em português do Brasil sobre qual time tem maior probabilidade de vencer: {time1} vs {time2}. Considere estatísticas como KDA, objetivos conquistados, economia do jogo, e performance geral."),
        ("user", "Dados dos times para análise: {dados_completos}")
    ])
    
    consulta_completa = f"""
    ANÁLISE COMPARATIVA - {time1} vs {time2}
    
    === DADOS DO {time1} ===
    {estatisticas_time1}
    
    === DADOS DO {time2} ===
    {estatisticas_time2}
    
    Analise estes dados e forneça sua previsão sobre qual time tem maior probabilidade de vitória, justificando com base nas estatísticas apresentadas.
    Não repita informações.
    Sempre traga estatísticas de cada time.
    Traga a probabilidade de qual time pegará primeiro:
        firstdragon, 
        firstherald, 
        firstbarão, 
        firstblood, 
        towers, 
        inhibitors    
    Priorize o split mais recente, mas caso não haja dados suficientes, use splits passados, mas ainda assim dê peso maior ao split mais recente (quanto maior o número associado a palavra split 'numero" indica que é mais recenete. Ex: Split 2 é mais recente que Split 1)
    Resuma suas respostas.
    """
    
    chain = prompt | llm | output_parser
    
    print("⏳ Gerando relatório preditivo (Isso pode demorar um pouco)...\n")
    response = chain.invoke({'dados_completos': consulta_completa})
    
    return response

if __name__ == "__main__":
    # Nomes dos times a serem analisados
    TIME_1 = "FURIA"
    TIME_2 = "paiN Gaming"
    
    try:
        resultado = dsa_gera_analises(TIME_1, TIME_2)
        print("="*60)
        print("🏆 RESULTADO DA ANÁLISE PREDITIVA 🏆".center(60))
        print("="*60)
        print(resultado)
        print("="*60)
    except Exception as e:
        print(f"\n❌ Erro durante a execução: {e}")
