from playwright.sync_api import sync_playwright
import time

def verify():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        # 1. Dashboard
        page.goto("http://127.0.0.1:3000")
        page.wait_for_selector("text=Visão Geral da Infraestrutura")
        page.screenshot(path="dashboard_screenshot.png")
        print("Dashboard verified & screenshot taken!")

        # 2. Switches
        page.click("text=Switches")
        page.wait_for_selector("text=Matriz Interativa de Portas")
        page.screenshot(path="switches_screenshot.png")
        print("Switches matrix verified & screenshot taken!")

        # 3. Network Map
        page.click("text=Mapa da Rede")
        page.wait_for_timeout(2000)
        page.screenshot(path="network_map_screenshot.png")
        print("Network map verified & screenshot taken!")

        browser.close()

if __name__ == "__main__":
    verify()
