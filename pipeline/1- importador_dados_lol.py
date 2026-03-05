# Utilizado a biblioteca gdown, pois o wget não consegue acessar arquivos em Google Drive.
# Este script baixa automaticamente o arquivo CSV mais recente da pasta
# "OE Public Match Data" no Google Drive.

import re
import gdown
import os

# URL da pasta pública no Google Drive (OE Public Match Data)
FOLDER_URL = "https://drive.google.com/drive/folders/1gLSw0RLjBbtaNy0dgnGQDAZOHIgCe-HH"

# Padrão dos nomes: YYYY_LoL_esports_match_data_from_OraclesElixir.csv
PADRAO_ANO = re.compile(r"(\d{4})_LoL_esports_match_data")


def baixar_arquivo_mais_recente():
    """
    Lista os arquivos da pasta do Google Drive (sem baixar),
    identifica o mais recente pelo ano no nome,
    e baixa apenas esse arquivo.
    """

    # 1. Lista os arquivos da pasta sem baixar nenhum
    print("📂 Listando arquivos na pasta do Google Drive...")
    arquivos = gdown.download_folder(
        url=FOLDER_URL,
        skip_download=True,
        quiet=True,
        remaining_ok=True,
    )

    if not arquivos:
        raise RuntimeError(
            "Não foi possível listar os arquivos da pasta. "
            "Verifique a URL e sua conexão com a internet."
        )

    # 2. Encontra o arquivo com o ano mais recente no nome
    arquivo_alvo = None
    ano_mais_recente = 0

    for arq in arquivos:
        match = PADRAO_ANO.search(arq.path)
        if match:
            ano = int(match.group(1))
            if ano > ano_mais_recente:
                ano_mais_recente = ano
                arquivo_alvo = arq

    if not arquivo_alvo:
        raise RuntimeError("Nenhum arquivo de match data encontrado na pasta.")

    print(f"📥 Arquivo mais recente: {arquivo_alvo.path} ({ano_mais_recente})")

    # 3. Baixa apenas o arquivo mais recente
    os.makedirs(os.path.join("data", "raw"), exist_ok=True)
    output_filename = os.path.join("data", "raw", f"{ano_mais_recente}loesport_matchdata.csv")
    download_url = f"https://drive.google.com/uc?id={arquivo_alvo.id}"

    print(f"⬇️  Baixando para: {output_filename}")
    gdown.download(download_url, output_filename, quiet=False)

    print(f"✅ Download concluído: {output_filename}")
    return output_filename


if __name__ == "__main__":
    baixar_arquivo_mais_recente()