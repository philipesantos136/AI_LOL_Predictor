
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
    Tenta baixar a logo do time via Liquipedia API (Search + Scraping) e salva localmente.
    """
    clean_name = team_name.replace(" ", "_")
    output_path = LOGO_DIR / f"{clean_name}.png"
    
    if output_path.exists():
        return True

    headers = {
        "User-Agent": LIQUIPEDIA_USER_AGENT,
        "Accept-Encoding": "gzip"
    }
    
    async def get_team_page_via_search(name: str, client: httpx.AsyncClient) -> str:
        """Usa API de busca para encontrar o nome correto da página do time."""
        async def _search(q: str):
            try:
                url = f"https://liquipedia.net/leagueoflegends/api.php?action=opensearch&search={q}&limit=5&format=json"
                res = await client.get(url, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    titles, urls = data[1], data[3]
                    for i, title in enumerate(titles):
                        if q.lower() in title.lower(): return urls[i]
                    if urls: return urls[0]
            except: pass
            return None

        # 1. Tenta nome completo
        url = await _search(name)
        if url: return url

        # 2. Tenta sem "Team" no início
        if name.lower().startswith("team "):
            url = await _search(name[5:])
            if url: return url

        # 3. Tenta apenas as duas primeiras palavras (para casos de fusão/patrocínio)
        parts = name.split()
        if len(parts) > 2:
            url = await _search(" ".join(parts[:2]))
            if url: return url
            
        return None

    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
            print(f"🔍 Buscando {team_name} via API Liquipedia...")
            
            # Estratégia 1: Busca Direta via Opensearch (mais robusto)
            team_page_url = await get_team_page_via_search(team_name, client)
            
            # Estratégia 2: Fallback para Portal:Teams se a busca falhar
            if not team_page_url:
                print(f"⚠️ Busca falhou para {team_name}. Tentando portal de times...")
                portal_url = "https://liquipedia.net/leagueoflegends/api.php?action=parse&page=Portal:Teams&format=json"
                response = await client.get(portal_url, timeout=20)
                
                if response.status_code == 200:
                    html_content = response.json().get('parse', {}).get('text', {}).get('*', '')
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Procura pelo link do time
                    team_link = soup.find('a', title=re.compile(f"^{re.escape(team_name)}$", re.I))
                    if not team_link:
                        team_link = soup.find('a', string=re.compile(f"^{re.escape(team_name)}$", re.I))
                    
                    if not team_link:
                        for span in soup.find_all('span', class_='team-template-text'):
                            a = span.find('a')
                            if a and (a.get_text().lower() == team_name.lower() or a.get('title', '').lower() == team_name.lower()):
                                team_link = a
                                break
                    
                    if team_link:
                        path = team_link['href']
                        if not path.startswith('/leagueoflegends/'):
                            if not path.startswith('/'): path = '/' + path
                        team_page_url = f"https://liquipedia.net{path}"

            if not team_page_url:
                print(f"❌ Time {team_name} não encontrado na Liquipedia.")
                return False
            
            print(f"🔍 Acessando página do time: {team_page_url}")
            team_response = await client.get(team_page_url, timeout=20)
            team_response.raise_for_status()
            
            team_soup = BeautifulSoup(team_response.text, 'html.parser')
            infobox = team_soup.find('div', class_='infobox-image') or team_soup.find('table', class_='infobox')
            
            if not infobox:
                print(f"❌ Infobox não encontrada na página de {team_name}")
                return False
                
            logo_img = infobox.find('img')
            if not logo_img:
                print(f"❌ Logo não encontrada na página de {team_name}")
                return False
            
            logo_src = logo_img.get('src') or logo_img.get('data-src')
            if not logo_src:
                return False

            logo_url = f"https://liquipedia.net{logo_src}" if logo_src.startswith('/') else logo_src
            
            # Limpa URL de thumbnail para pegar a original
            if '/thumb/' in logo_url:
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
