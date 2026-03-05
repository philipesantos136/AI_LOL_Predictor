import pandas as pd
import sqlite3
import os
import glob
import re

def main():
    print("Iniciando processo de importação do CSV para SQLite...")
    
    # 1. Encontra o CSV mais recente no diretório 'data'
    csv_files = glob.glob(os.path.join("data", "*loesport_matchdata.csv"))
    if not csv_files:
        print("❌ Erro: Nenhum arquivo CSV de matchdata encontrado no diretório 'data'.")
        return
        
    # Ordena para pegar o mais recente (ex: 2026 > 2025)
    csv_file = sorted(csv_files, reverse=True)[0]
    print(f"📄 Arquivo CSV encontrado: {csv_file}")
    
    # Extrai o ano do nome do arquivo para usar no nome da tabela (fallback para 2025)
    match = re.search(r'(\d{4})', csv_file)
    ano = match.group(1) if match else "2025"
    
    # 2. Configurações
    db_file = "lol_datamatches.db"
    tabela = f"{ano}_lol_matches"
    
    try:
        # 3. Lê o CSV com pandas
        print(f"⏳ Lendo arquivo {csv_file}... (Isso pode demorar alguns segundos)")
        df = pd.read_csv(csv_file, low_memory=False)
        print(f"✅ CSV carregado com sucesso. {len(df)} linhas encontradas.")
        
        # 4. Conecta (ou cria) o banco SQLite
        print(f"🔌 Conectando ao banco SQLite '{db_file}'...")
        con = sqlite3.connect(db_file)
        
        # 5. Exporta o DataFrame para o SQLite (substituindo se já existir)
        print(f"💾 Salvando dados na tabela '{tabela}' (camada Bronze)...")
        df.to_sql(tabela, con, if_exists="replace", index=False)
        print("✅ Dados salvos com sucesso no banco de dados!")
        
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
