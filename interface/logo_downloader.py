
import os
import httpx
import re
import asyncio
from pathlib import Path
from bs4 import BeautifulSoup

LOGO_DIR = Path(__file__).parent.parent / "data" / "logos"
LOGO_DIR.mkdir(parents=True, exist_ok=True)

# User-Agent rigoroso seguindo as regras da Liquipedia
LIQUIPEDIA_USER_AGENT = "AI_LoL_Predictor/1.1 (https://github.com/philipesantos136/AI_LOL_Predictor; philipe.santos@example.com)"

async def download_team_logo_liquipedia(team_name: str) -> bool:
    """
    Tenta baixar a logo do time via Liquipedia API + Scraping e salva localmente.
    """
    clean_name = team_name.replace(" ", "_")
    output_path = LOGO_DIR / f"{clean_name}.png"
    
    if output_path.exists():
        return True

    headers = {
        "User-Agent": LIQUIPEDIA_USER_AGENT,
        "Accept-Encoding": "gzip",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    }
    
    try:
        # Tenta pegar o HTML da página via MediaWiki API para evitar alguns filtros de robô no front
        api_url = f"https://liquipedia.net/leagueoflegends/api.php?action=parse&page=Portal:Teams&format=json"
        
        async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
            print(f"🔍 Buscando {team_name} via API Liquipedia...")
            response = await client.get(api_url, timeout=20)
            
            if response.status_code == 403:
                print("⚠️ API bloqueada (403). Tentando acesso direto...")
                response = await client.get("https://liquipedia.net/leagueoflegends/Portal:Teams", timeout=20)
            
            response.raise_for_status()
            
            if "api.php" in str(response.url):
                html_content = response.json().get('parse', {}).get('text', {}).get('*', '')
            else:
                html_content = response.text
                
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Procura pelo link do time
            team_link = soup.find('a', title=re.compile(f"^{re.escape(team_name)}$", re.I))
            if not team_link:
                team_link = soup.find('a', string=re.compile(f"^{re.escape(team_name)}$", re.I))
            
            if not team_link:
                # Tenta buscar pelo nome do time no texto das spans de time
                all_spans = soup.find_all('span', class_='team-template-text')
                for span in all_spans:
                    a = span.find('a')
                    if a and (a.get_text().lower() == team_name.lower() or a.get('title', '').lower() == team_name.lower()):
                        team_link = a
                        break

            if not team_link:
                print(f"❌ Time {team_name} não encontrado no portal.")
                return False
            
            # A partir do link do time, vamos para a página do time para pegar a logo de alta qualidade
            team_path = team_link['href']
            if not team_path.startswith('/leagueoflegends/'):
                # Se for um link relativo estranho
                if not team_path.startswith('/'): team_path = '/' + team_path
            
            team_page_url = f"https://liquipedia.net{team_path}"
            print(f"🔍 Acessando página do time: {team_page_url}")
            team_response = await client.get(team_page_url, timeout=20)
            team_response.raise_for_status()
            
            team_soup = BeautifulSoup(team_response.text, 'html.parser')
            
            # A logo costuma estar na infobox
            logo_img = None
            infobox = team_soup.find('div', class_='infobox-image')
            if infobox:
                logo_img = infobox.find('img')
            
            if not logo_img:
                # Fallback: qualquer imagem grande na infobox
                infobox_v2 = team_soup.find('table', class_='infobox')
                if infobox_v2:
                    logo_img = infobox_v2.find('img')

            if not logo_img:
                print(f"❌ Logo não encontrada na página de {team_name}")
                return False
            
            logo_src = logo_img.get('src')
            if not logo_src:
                logo_src = logo_img.get('data-src') # Lazy load backup
            
            if not logo_src:
                return False

            if logo_src.startswith('/'):
                logo_url = f"https://liquipedia.net{logo_src}"
            else:
                logo_url = logo_src
            
            # Limpa URL de thumbnail para pegar a original
            if '/thumb/' in logo_url:
                # https://liquipedia.net/commons/images/thumb/e/e2/LOUD_2025_full_allmode.png/600px-LOUD_2025_full_allmode.png
                # -> https://liquipedia.net/commons/images/e/e2/LOUD_2025_full_allmode.png
                logo_url = logo_url.replace('/thumb/', '/')
                logo_url = '/'.join(logo_url.split('/')[:-1])

            print(f"⬇️ Baixando logo final: {logo_url}")
            img_res = await client.get(logo_url, timeout=20)
            img_res.raise_for_status()
            
            with open(output_path, "wb") as f:
                f.write(img_res.content)
            
            print(f"✅ Logo de {team_name} salva com sucesso!")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao baixar da Liquipedia: {e}")
        return False
