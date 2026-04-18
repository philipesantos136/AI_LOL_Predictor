import pandas as pd
import sqlite3
import os
import glob
import re

def main():
    print("Iniciando processo de importação do CSV para SQLite...")
    
    # 1. Encontra o CSV mais recente no diretório 'data/raw'
    csv_files = glob.glob(os.path.join("data", "raw", "*loesport_matchdata.csv"))
    if not csv_files:
        print("❌ Erro: Nenhum arquivo CSV de matchdata encontrado no diretório 'data/raw'.")
        return
        
    # Ordena para pegar o mais recente (ex: 2026 > 2025)
    csv_file = sorted(csv_files, reverse=True)[0]
    print(f"📄 Arquivo CSV encontrado: {csv_file}")
    
    # Extrai o ano do nome do arquivo para usar no nome da tabela (fallback para 2025)
    match = re.search(r'(\d{4})', csv_file)
    ano = match.group(1) if match else "2025"
    
    # 2. Configurações
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_dir = os.path.join(ROOT_DIR, "data", "db")
    os.makedirs(db_dir, exist_ok=True)
    db_file = os.path.join(db_dir, "lol_datamatches.db")
    tabela = f"{ano}_lol_matches"
    
    try:
        # 3. Lê o CSV com pandas
        print(f"⏳ Lendo arquivo {csv_file}... (Isso pode demorar alguns segundos)")
        df = pd.read_csv(csv_file, low_memory=False)
        print(f"✅ CSV carregado com sucesso. {len(df)} linhas encontradas.")
        
        # 3.1 Limpeza de Nomes de Times (Ex: Los Grandes com encoding quebrado)
        if 'teamname' in df.columns:
            print("🧹 Limpando nomes de times...")
            # Padrão para pegar Los Grandes com encoding quebrado (LÃ˜S)
            df['teamname'] = df['teamname'].replace(['LÃ˜S', 'LØS'], 'Los Grandes')
            # Fallback para regex caso o encoding no arquivo venha diferente (L followed by non-ascii then S)
            df['teamname'] = df['teamname'].str.replace(r'^L[^a-zA-Z]S$', 'Los Grandes', regex=True)
        
        # 4. Conecta (ou cria) o banco SQLite
        print(f"🔌 Conectando ao banco SQLite '{db_file}'...")
        con = sqlite3.connect(db_file)
        
        # 5. Exporta o DataFrame para uma tabela TEMPORÁRIA
        print(f"💾 Carregando dados temporários para merge...")
        df.to_sql("temp_import_bronze", con, if_exists="replace", index=False)
        
        # 6. Cria a tabela Bronze definitiva se não existir (com chaves primárias para o upsert)
        cursor = con.cursor()
        
        # Verifica se o esquema atual possui a coluna 'patch'
        cursor.execute(f"PRAGMA table_info('{tabela}')")
        colunas_existentes = [col[1] for col in cursor.fetchall()]
        
        if colunas_existentes and "patch" not in colunas_existentes:
            print(f"⚠️  Esquema antigo na Bronze '{tabela}' detectado. Resetando para novo formato...")
            cursor.execute(f"DROP TABLE '{tabela}'")

        colunas_sql = ", ".join([f'"{c}" TEXT' for c in df.columns])
        cursor.execute(f'CREATE TABLE IF NOT EXISTS "{tabela}" ({colunas_sql}, PRIMARY KEY (gameid, participantid))')
        
        # 7. Executa o UPSERT (Merge) da temporária para a definitiva
        print(f"🔄 Realizando Merge (Upsert) na tabela '{tabela}'...")
        colunas_list = ", ".join([f'"{c}"' for c in df.columns])
        cursor.execute(f'INSERT OR REPLACE INTO "{tabela}" ({colunas_list}) SELECT {colunas_list} FROM temp_import_bronze')
        
        # 8. Limpa a tabela temporária
        cursor.execute("DROP TABLE temp_import_bronze")
        
        con.commit()
        print(f"✅ Dados mesclados com sucesso na camada Bronze!")
        
    except Exception as e:
        print(f"❌ Ocorreu um erro durante o processamento: {e}")
        
    finally:
        # 6. Fecha a conexão
        if 'con' in locals():
            con.close()
            print("🔒 Conexão com o banco fechada.")
            
    print("✨ Processo finalizado!")

if __name__ == "__main__":
    main()
