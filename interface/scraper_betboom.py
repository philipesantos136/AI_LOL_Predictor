"""
Módulo de Web Scraping para BetBoom — League of Legends
Extrai odds de partidas ao vivo/próximas do BetBoom para os times selecionados.
Usa Selenium com Chrome headless para renderizar o conteúdo JavaScript.

Tempo alvo: ~20-30 segundos no total.
"""

import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, ElementClickInterceptedException
)
from webdriver_manager.chrome import ChromeDriverManager


# URL base do BetBoom LoL
BETBOOM_LOL_LIVE_URL = "https://betboom.bet.br/esport/live/league-of-legends/"
BETBOOM_LOL_URL = "https://betboom.bet.br/esport/league-of-legends/"


def _create_driver():
    """Cria e retorna uma instância do Chrome WebDriver em modo headless."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    # NÃO usar implicitly_wait — causa bloqueios de 5s em cada find_elements vazio
    driver.implicitly_wait(0)
    return driver


def _dismiss_overlays(driver):
    """Fecha banners de cookies, verificação de idade e modais de registro. Rápido."""
    # Pressionar Escape (fecha a maioria dos modais)
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        body.send_keys(Keys.ESCAPE)
        time.sleep(0.3)
        body.send_keys(Keys.ESCAPE)
    except Exception:
        pass

    # Tenta fechar botões de close visíveis (sem delay entre cada)
    for sel in ["button[class*='closeButton']", "button.styles_closeButton__uG8Es"]:
        try:
            for btn in driver.find_elements(By.CSS_SELECTOR, sel):
                if btn.is_displayed():
                    btn.click()
        except Exception:
            pass
    
    # Aceitar cookies
    try:
        for btn in driver.find_elements(By.XPATH, "//button[contains(text(), 'OK')]"):
            if btn.is_displayed():
                btn.click()
    except Exception:
        pass
    
    # Verificação de idade
    try:
        for btn in driver.find_elements(By.XPATH, "//button[contains(text(), 'Sim') or contains(text(), 'Yes')]"):
            if btn.is_displayed():
                btn.click()
    except Exception:
        pass


def _normalize_team_name(name):
    """Normaliza nome do time para comparação flexível."""
    if not name: return ""
    return re.sub(r'[^a-z0-9]', '', name.lower().strip())


def _find_match_link(driver, team1, team2):
    """
    Procura na página de listagem a partida que contém os dois times.
    Retorna o elemento clicável ou None.
    """
    t1_norm = _normalize_team_name(team1)
    t2_norm = _normalize_team_name(team2)
    
    print(f"  🔍 Buscando: '{t1_norm}' vs '{t2_norm}'")
    
    try:
        # Busca links de partida de LoL
        matches = driver.find_elements(By.CSS_SELECTOR, "a[href*='/esport/league-of-legends/']")

        for match in matches:
            try:
                # Tenta pegar o texto do container pai (inclui nomes dos times)
                try:
                    parent = match.find_element(By.XPATH, "./ancestor::div[contains(@class, 'bb-')]")
                    text = _normalize_team_name(parent.text)
                except Exception:
                    text = _normalize_team_name(match.text)
                
                if t1_norm in text and t2_norm in text:
                    print(f"  🎯 Partida encontrada!")
                    return match
            except Exception:
                continue
                
    except Exception as e:
        print(f"  ⚠️ Erro ao buscar link: {e}")
    
    return None


def _wait_for_content(driver, timeout=8):
    """Espera o conteúdo principal carregar usando WebDriverWait explícito."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button, div.bb-Wa"))
        )
    except TimeoutException:
        print("  ⚠️ Timeout aguardando conteúdo")


def _scrape_tab_odds(driver):
    """
    Extrai todas as odds visíveis na aba atualmente selecionada.
    Foca apenas na área de conteúdo principal.
    """
    markets = {}
    time.sleep(1)  # Aguarda renderização da aba (mínimo necessário)
    
    try:
        # Scroll rápido para carregar lazy content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.5)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)
        
        # Busca cards de mercado
        all_sections = driver.find_elements(By.CSS_SELECTOR, "div.bb-Wa.bb-Ym")
        
        # Lista de ruído a ignorar
        ignore_list = {'CS2', 'LoL', 'Dota 2', 'Valorant', 'KoG', 'Call of Duty', 
                       'AOV', 'Crossfire', 'Favoritos', 'Ao Vivo', 'Todos', 'Americas Cup 2026'}
        
        for section in all_sections:
            try:
                if not section.is_displayed():
                    continue
                
                full_text = section.text.strip()
                if not full_text: 
                    continue

                lines = [l.strip() for l in full_text.split('\n') if l.strip()]
                if len(lines) < 2: 
                    continue
                
                title = lines[0]
                
                # Filtros
                if title in ignore_list:
                    continue
                if any(kw in title for kw in ['1h', '3h', '12h', '1d']):
                    continue
                
                # Busca botões de odds
                buttons = section.find_elements(By.CSS_SELECTOR, "button")
                if not buttons:
                    continue

                odds_data = []
                for btn in buttons:
                    try:
                        btn_text = btn.text.strip()
                        if not btn_text: continue
                        
                        btn_lines = [bl.strip() for bl in btn_text.split('\n') if bl.strip()]
                        
                        entry = {}
                        if len(btn_lines) >= 3:
                            entry = {"label": btn_lines[0], "line": btn_lines[1], "odd": btn_lines[2]}
                        elif len(btn_lines) == 2:
                            l0 = btn_lines[0]
                            if any(c in l0 for c in ['+', '-']) and any(d.isdigit() for d in l0):
                                entry = {"line": l0, "odd": btn_lines[1]}
                            else:
                                entry = {"label": l0, "odd": btn_lines[1]}
                        elif len(btn_lines) == 1:
                            try:
                                float(btn_lines[0])
                                entry = {"odd": btn_lines[0]}
                            except ValueError:
                                continue
                        
                        if entry:
                            odds_data.append(entry)
                    except Exception:
                        continue
                
                if odds_data:
                    markets[title] = odds_data
                    
            except Exception:
                continue
    
    except Exception as e:
        print(f"  ⚠️ Erro: {e}")
    
    return markets


def scrape_match_odds(team1, team2):
    """
    Função principal: Faz o scraping completo das odds de uma partida no BetBoom.
    Tempo alvo: ~20-30 segundos.
    """
    start_time = time.time()
    
    result = {
        "team1": team1,
        "team2": team2,
        "tabs": {},
        "status": "error",
        "message": ""
    }
    
    driver = None
    
    try:
        print(f"🌐 Scraper BetBoom: {team1} vs {team2}")
        driver = _create_driver()
        
        # 1. Navega para a página de LoL (live primeiro)
        print("  📡 Acessando BetBoom LoL Live...")
        driver.get(BETBOOM_LOL_LIVE_URL)
        _wait_for_content(driver, timeout=8)
        _dismiss_overlays(driver)
        
        # 2. Busca a partida
        match_elem = _find_match_link(driver, team1, team2)
        
        # Fallback para página geral
        if not match_elem:
            print("  🔄 Tentando página geral...")
            driver.get(BETBOOM_LOL_URL)
            _wait_for_content(driver, timeout=8)
            _dismiss_overlays(driver)
            match_elem = _find_match_link(driver, team1, team2)
        
        if not match_elem:
            elapsed = time.time() - start_time
            result["message"] = f"❌ Partida não encontrada no BetBoom ({elapsed:.0f}s)"
            return result
        
        # 3. Clica na partida
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", match_elem)
            time.sleep(0.5)
            match_elem.click()
        except Exception:
            driver.execute_script("arguments[0].click();", match_elem)
        
        print("  ⏳ Carregando detalhes...")
        _wait_for_content(driver, timeout=8)
        time.sleep(1)  # Espera extra para JS renderizar
        _dismiss_overlays(driver)
        
        # 4. Detecta quais abas estão disponíveis
        available_tabs = driver.find_elements(By.CSS_SELECTOR, "button.bb-t8")
        tab_texts = [t.text.strip() for t in available_tabs if t.text.strip()]
        print(f"  📋 Abas disponíveis: {tab_texts}")
        
        target_tabs = ["Partida", "Mapa 1", "Mapa 2", "Mapa 3", "Mapa 4", "Mapa 5"]
        
        for name in target_tabs:
            # Pula abas que não existem (sem esperar)
            if name not in tab_texts and name != "Partida":
                continue
            
            print(f"  📊 Extraindo: {name}...")
            
            try:
                # Re-localiza botões (DOM pode mudar)
                tabs = driver.find_elements(By.CSS_SELECTOR, "button.bb-t8")
                target_btn = None
                for t in tabs:
                    if t.text.strip() == name:
                        target_btn = t
                        break
                
                if target_btn:
                    # Clica só se não estiver ativo
                    cls = target_btn.get_attribute("class") or ""
                    if "bb-u8" not in cls:
                        driver.execute_script("arguments[0].click();", target_btn)
                        time.sleep(1)  # Espera render da aba
                    
                    markets = _scrape_tab_odds(driver)
                    if markets:
                        result["tabs"][name] = markets
                        print(f"    ✅ {len(markets)} mercados")
                elif name == "Partida":
                    # "Partida" pode já estar ativa por padrão
                    markets = _scrape_tab_odds(driver)
                    if markets:
                        result["tabs"][name] = markets
                        print(f"    ✅ {len(markets)} mercados")
                        
            except Exception as e:
                print(f"    ❌ Erro aba {name}: {e}")
        
        elapsed = time.time() - start_time
        
        if result["tabs"]:
            result["status"] = "success"
            result["message"] = f"✅ Scraping concluído em {elapsed:.0f}s!"
            print(f"\n🎉 {result['message']}")
        else:
            result["message"] = f"⚠️ Nenhum mercado encontrado ({elapsed:.0f}s)"
            
    except Exception as e:
        elapsed = time.time() - start_time
        result["message"] = f"❌ Erro: {str(e)} ({elapsed:.0f}s)"
        print(f"❌ Erro: {e}")
    
    finally:
        if driver:
            driver.quit()
    
    return result


# Para testes diretos
if __name__ == "__main__":
    import json
    data = scrape_match_odds("Cloud9", "RED Canids")
    print("\n" + "="*60)
    print(json.dumps(data, indent=2, ensure_ascii=False))
