import asyncio
from playwright.async_api import async_playwright
import os
from pathlib import Path
from dotenv import load_dotenv
import json

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

        # Handle modals first
        try:
            # Age verification
            age_btn = page.locator('button:has-text("Sim, eu tenho 18 anos ou mais")')
            if await age_btn.is_visible():
                await age_btn.click()
            
            # Cookies
            cookie_btn = page.locator('button:has-text("OK")')
            if await cookie_btn.is_visible():
                await cookie_btn.click()
        except:
            pass

        # Click login button
        try:
            # New selectors from subagent
            # 1. Login button on main page
            login_btn = page.locator('a[href*="modal=%7B%22type%22%3A%22auth%22"], button:has-text("Fazer login"), .bb-y_')
            await login_btn.first.wait_for(state="visible", timeout=10000)
            await login_btn.first.click(force=True)
            
            # small delay for modal
            await asyncio.sleep(2)

            # 2. Email tab
            email_tab = page.locator('div.styles_labelText__BqfmI:has-text("Por e-mail"), div:has-text("Por e-mail"), button:has-text("Por e-mail")')
            if await email_tab.count() > 0:
                await email_tab.first.click()
            
            # Handle possible registration modal redirect
            reg_modal_login = page.locator('text="Eu tenho uma conta Entrar"')
            if await reg_modal_login.is_visible():
                await page.click('span:has-text("Entrar"), a:has-text("Entrar"), .bb-V_')
                # Try clicking email tab again if it changed
                if await email_tab.count() > 0:
                    await email_tab.first.click()

            # 3. Fill credentials
            email_input = page.locator('input[placeholder="Insira seu e-mail"], input[type="text"], input[placeholder*="email"]')
            await email_input.wait_for(state="visible", timeout=10000)
            await email_input.fill(BETBOOM_EMAIL)
            
            password_input = page.locator('input[placeholder="Senha"], input[type="password"], input[placeholder*="senha"]')
            await password_input.fill(BETBOOM_PASSWORD)
            
            # 4. Submit button
            submit_btn = page.locator('button.styles_submitBtn__OyhuH, button[type="submit"]:has-text("Entrar"), .bb-V_ >> text="Entrar"')
            if await submit_btn.is_visible():
                await submit_btn.click()
            else:
                await page.keyboard.press("Enter")
            
            # 5. Wait for login to complete (Success indicator)
            await page.wait_for_selector("div.styles_controlBtn__TH_0O span, .bb-A__, .bb-F__, .bb-G__", timeout=20000)
            
            # Save state
            await self.context.storage_state(path=str(STORAGE_STATE))
            print("Login successful and state saved.")
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
        
        # Click "Todos" to expand all markets
        try:
            todos_button = page.get_by_text("Todos", exact=True)
            if await todos_button.is_visible():
                await todos_button.click()
        except:
            pass

        # Give some time for markets to load
        await asyncio.sleep(2)

        # Extract odds
        odds_data = {}
        
        # Helper to find market groups and their buttons
        # Markets are in containers with titles
        market_containers = await page.query_selector_all(".bb-_c.bb-as")
        
        for container in market_containers:
            title_node = await container.query_selector(".bb-X_") # Header of the market group
            if not title_node: continue
            
            title = (await title_node.inner_text()).strip()
            
            buttons = await container.query_selector_all("button.bb-N_.bb-Ms.bb-Ps")
            market_odds = []
            for btn in buttons:
                try:
                    labels = await btn.query_selector_all("div")
                    if len(labels) >= 2:
                        label = (await labels[0].inner_text()).strip()
                        value = (await labels[1].inner_text()).strip()
                        market_odds.append({"label": label, "value": value})
                except:
                    continue
            
            if market_odds:
                odds_data[title] = market_odds

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
    scraper = BetBoomScraper()
    try:
        await scraper.init_browser()
        await scraper.login()
        
        if not url:
            url = await scraper.find_match_url(team1, team2)
        
        if url:
            odds = await scraper.scrape_match(url)
            return {"url": url, "odds": odds}
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
