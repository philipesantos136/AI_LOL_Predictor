import asyncio
from playwright.async_api import async_playwright
import os
from pathlib import Path
from dotenv import load_dotenv
import json
import sys

load_dotenv("c:/Projetos/AI_LOL_Predictor/.env")

BETBOOM_EMAIL = os.getenv("BETBOOM_EMAIL", "philipeconexao@gmail.com")
BETBOOM_PASSWORD = os.getenv("BETBOOM_PASSWORD", "Imbetter301!")

STORAGE_STATE = Path(__file__).parent / "betboom_state.json"

class BetBoomScraper:
    def __init__(self):
        self.browser = None
        self.context = None

    async def init_browser(self, headless=True):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        
        if STORAGE_STATE.exists():
            self.context = await self.browser.new_context(storage_state=str(STORAGE_STATE))
        else:
            self.context = await self.browser.new_context()

    async def login(self):
        page = await self.context.new_page()
        await page.goto("https://betboom.bet.br/esport/league-of-legends/")
        
        # Check if already logged in (e.g., look for balance or profile)
        try:
            await page.wait_for_selector(".bb-A__", timeout=5000) # Selector for balance or logged in state
            print("Already logged in.")
            await page.close()
            return
        except:
            print("Not logged in. Proceeding to login...")

        # Handlers for initial state
        try:
            # First, check if there's a logout button or profile to see if we're ALREADY logged in
            # This is faster than trying to login
            balance_selector = "div.styles_controlBtn__TH_0O span, .bb-A__, .bb-F__, .bb-G__"
            try:
                await page.wait_for_selector(balance_selector, timeout=3000)
                print("✅ Já está logado. Pulando login.")
                return
            except:
                pass

            # If not logged in, proceed. Check for modals first
            age_btn = page.locator('button:has-text("Sim, eu tenho 18 anos ou mais")')
            if await age_btn.is_visible():
                await age_btn.click()
            
            cookie_btn = page.locator('button:has-text("OK")')
            if await cookie_btn.is_visible():
                await cookie_btn.click()
        except Exception as e:
            print(f"⚠️ Erro ao tratar modais iniciais: {e}")

        # Click login button
        try:
            print("🔍 Procurando botão de login...")
            login_btn = page.locator('a[href*="modal=%7B%22type%22%3A%22auth%22"], button:has-text("Fazer login"), .bb-y_')
            await login_btn.first.wait_for(state="visible", timeout=15000)
            await login_btn.first.click(force=True)
            print("👆 Clique no botão de login realizado.")
            
            await page.wait_for_timeout(3000) # Wait for animation

            # 2. Email tab
            print("📧 Selecionando aba de e-mail...")
            email_tab = page.locator('div.styles_labelText__BqfmI:has-text("Por e-mail"), button:has-text("Por e-mail")')
            
            # Check if modal redirect happened (registration modal instead of login)
            reg_modal_login = page.locator('text="Eu tenho uma conta Entrar"')
            if await reg_modal_login.is_visible():
                print("🔄 Detectado modal de registro. Mudando para login...")
                await page.click('span:has-text("Entrar"), a:has-text("Entrar"), .bb-V_')
                await page.wait_for_timeout(2000)

            await email_tab.first.wait_for(state="attached", timeout=10000)
            await email_tab.first.click(force=True)
            
            # 3. Fill credentials
            print("📝 Preenchendo credenciais...")
            email_input = page.locator('input[placeholder="Insira seu e-mail"], input[type="text"], input[placeholder*="email"]')
            await email_input.first.wait_for(state="visible", timeout=10000)
            await email_input.first.fill(BETBOOM_EMAIL)
            
            password_input = page.locator('input[placeholder="Senha"], input[type="password"], input[placeholder*="senha"]')
            await password_input.first.fill(BETBOOM_PASSWORD)
            
            # 4. Submit button
            print("🚀 Enviando formulário...")
            submit_btn = page.locator('button.styles_submitBtn__OyhuH, button[type="submit"]:has-text("Entrar"), .bb-V_ >> text="Entrar"')
            await submit_btn.first.click(force=True)
            
            # 5. Wait for login to complete (Success indicator)
            print("⏳ Aguardando confirmação de login (saldo/perfil)...")
            await page.wait_for_selector(balance_selector, timeout=25000)
            print("🎉 Login confirmado com sucesso!")
            
            # Save state
            await self.context.storage_state(path=str(STORAGE_STATE))
            print("💾 Estado da sessão salvo.")
        except Exception as e:
            print(f"❌ Falha no processo de login: {e}")
            await page.screenshot(path="login_error.png")
            # Salvar HTML para depuração se falhar
            try:
                html_content = await page.content()
                with open("login_error_debug.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
            except: pass
            raise e
        except Exception as e:
            print(f"Login failure: {e}")
            await page.screenshot(path="login_error.png")
            raise e
        
        await page.close()

    async def scrape_match(self, url: str):
        if not self.context:
            await self.init_browser()
            await self.login()

        page = await self.context.new_page()
        await page.goto(url)
        
    async def get_available_tabs(self, page):
        """Retorna uma lista de nomes de abas disponíveis (Partida, Mapa 1, etc)"""
        tabs_elements = await page.locator('button[role="radio"]').all()
        tabs = []
        for el in tabs_elements:
            text = await el.inner_text()
            if text:
                tabs.append(text.strip())
        return tabs

    async def extract_current_tab_odds(self, page):
        """Extrai as odds da aba atualmente selecionada"""
        return await page.evaluate("""
            () => {
                const results = {};
                // Market headers have this class
                const headers = document.querySelectorAll('.bb-_c.bb-as');
                
                headers.forEach(header => {
                    const title = header.innerText.trim();
                    const market_odds = [];
                    let next = header.nextElementSibling;
                    
                    while (next && !next.classList.contains('bb-as')) {
                        const buttons = next.querySelectorAll('button.bb-N_');
                        buttons.forEach(btn => {
                            const divs = btn.querySelectorAll('div');
                            if (divs.length >= 2) {
                                let label = divs[0].innerText.trim();
                                const value = divs[1].innerText.trim();
                                market_odds.push({ label, value });
                            }
                        });
                        
                        const lineElements = next.querySelectorAll('div.bb-M_');
                        lineElements.forEach(le => {
                            const lineText = le.innerText.trim();
                            if (lineText && !isNaN(parseFloat(lineText))) {
                                market_odds.push({ type: 'line', value: lineText });
                            }
                        });

                        next = next.nextElementSibling;
                        if (!next) break;
                    }
                    
                    if (market_odds.length > 0) {
                        results[title] = market_odds;
                    }
                });
                return results;
            }
        """)

    async def scrape_match(self, url: str):
        if not self.context:
            await self.init_browser()
            await self.login()

        page = await self.context.new_page()
        await page.goto(url)
        
        # Aguardar carregamento inicial
        try:
            await page.wait_for_selector('button[role="radio"]', timeout=15000)
        except:
            print("⚠️ Abas de mercado não encontradas.")
            await page.screenshot(path="tabs_not_found.png")
            await page.close()
            return {}

        all_odds = {}
        available_tabs = await self.get_available_tabs(page)
        print(f"📋 Abas detectadas: {available_tabs}")

        # 1. Extrair aba "Partida"
        if "Partida" in available_tabs:
            print("🎯 Extraindo odds da aba 'Partida'...")
            partida_tab = page.locator('button[role="radio"]').filter(has_text="Partida")
            await partida_tab.click()
            await asyncio.sleep(1.5)
            partida_odds = await self.extract_current_tab_odds(page)
            all_odds.update(partida_odds)
        
        # 2. Extrair "Próximo Mapa"
        # Identificar o menor mapa disponível (Mapa 1, Mapa 2, etc.)
        map_tabs = [t for t in available_tabs if "Mapa" in t]
        if map_tabs:
            # Ordenar para pegar o primeiro (ex: Mapa 1)
            map_tabs.sort()
            next_map = map_tabs[0]
            print(f"🗺️ Extraindo odds do próximo mapa: {next_map}...")
            mapa_tab = page.locator('button[role="radio"]').filter(has_text=next_map)
            await mapa_tab.click()
            await asyncio.sleep(1.5)
            mapa_odds = await self.extract_current_tab_odds(page)
            
            # Adicionar prefixo do mapa nas chaves para não sobrescrever Partida
            for k, v in mapa_odds.items():
                all_odds[f"[{next_map}] {k}"] = v

        await page.close()
        return all_odds

        await page.close()
        return odds_data

    async def find_match_url(self, team1: str, team2: str):
        if not self.context:
            await self.init_browser()
            await self.login()

        page = await self.context.new_page()
        await page.goto("https://betboom.bet.br/esport/league-of-legends/")
        
        # Click "Todos" to see upcoming games
        try:
            todos_tab = page.locator(".bb-f__").filter(has_text="Todos")
            await todos_tab.click()
        except:
            pass
        
        await asyncio.sleep(2)
        
        # Look for match links that contain either team name
        links = await page.query_selector_all("a[href*='/esport/league-of-legends/']")
        found_url = None
        for link in links:
            text = await link.inner_text()
            if team1.lower() in text.lower() or team2.lower() in text.lower():
                found_url = await link.get_attribute("href")
                if found_url and not found_url.startswith("http"):
                    found_url = "https://betboom.bet.br" + found_url
                break
        
        await page.close()
        return found_url

    async def close(self):
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

async def get_betboom_data(team1: str, team2: str, url: str = None):
    # Ensure Proactor loop on Windows for subprocess support
    if sys.platform == 'win32':
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    scraper = BetBoomScraper()
    try:
        await scraper.init_browser()
        await scraper.login()
        
        if not url:
            url = await scraper.find_match_url(team1, team2)
        
        if url:
            odds = await scraper.scrape_match(url)
            result = {"url": url, "odds": odds}
            
            # Save the result to a file as requested
            # Sanitize team names for filename
            s_t1 = team1.replace(" ", "_").replace("/", "-")
            s_t2 = team2.replace(" ", "_").replace("/", "-")
            filename = f"Odds_{s_t1}vs{s_t2}.json"
            output_path = Path("data") / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"📄 Odds salvas em: {output_path}")
            
            return result
        else:
            return {"error": "Match URL not found"}
    finally:
        await scraper.close()

if __name__ == "__main__":
    # Test
    async def test():
        data = await get_betboom_data("Bilibili Gaming", "G2 Esports", "https://betboom.bet.br/esport/league-of-legends/30603/4229073/")
        print(json.dumps(data, indent=2))
    
    asyncio.run(test())
