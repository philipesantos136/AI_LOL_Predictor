import os
import requests
import json

def scrape_champion_squares_ddragon(output_dir="data/champs"):
    """
    Downloads Champion Square Images from Riot's official Data Dragon API.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    print("Obtendo a última versão do Data Dragon...")
    try:
        versions_url = "https://ddragon.leagueoflegends.com/api/versions.json"
        versions_response = requests.get(versions_url)
        versions_response.raise_for_status()
        latest_version = versions_response.json()[0]
        print(f"Última versão: {latest_version}")
        
        champions_url = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/pt_BR/champion.json"
        print(f"Obtendo lista de campeões...")
        champions_response = requests.get(champions_url)
        champions_response.raise_for_status()
        champions_data = champions_response.json()['data']
        
        downloaded = 0
        skipped = 0
        
        print(f"Encontrados {len(champions_data)} campeões. Iniciando download...")
        for champ_id, champ_info in champions_data.items():
            # O nome do arquivo na Data Dragon é o image.full
            image_filename = champ_info['image']['full']
            # Mas vamos renomear para o nome do campeão (champ_info['name']) para ser amigável
            friendly_name = champ_info['name']
            
            # Limpar nome para arquivo (remover caracteres especiais se houver, ex: Nunu & Willump -> Nunu)
            clean_name = friendly_name.replace("'", "").replace(" & ", "_").replace(".", "").replace(" ", "")
            
            filepath = os.path.join(output_dir, f"{clean_name}.png")
            
            if os.path.exists(filepath):
                skipped += 1
                continue
                
            img_url = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/img/champion/{image_filename}"
            
            try:
                img_response = requests.get(img_url, stream=True)
                img_response.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in img_response.iter_content(1024):
                        f.write(chunk)
                downloaded += 1
            except Exception as e:
                print(f"Erro ao baixar {friendly_name} ({img_url}): {e}")
                
        print(f"\n--- Scraping finalizado ---")
        print(f"Imagens baixadas: {downloaded}")
        print(f"Imagens ignoradas (já existiam): {skipped}")
        
    except Exception as e:
        print(f"Erro fatal: {e}")

if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    output_dir = os.path.join(project_root, "data", "champs")
    scrape_champion_squares_ddragon(output_dir)
