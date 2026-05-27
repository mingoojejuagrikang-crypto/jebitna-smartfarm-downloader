import os
import sys
import time
from playwright.sync_api import sync_playwright

DIAG_DIR = os.path.abspath("./diagnostics")

def log(msg):
    print(f"[*] {msg}", flush=True)

def run():
    target_url = "https://jebitna.agri.jeju.kr/"
    username = ""  # 사용자 고유 아이디 입력
    password = ""  # 사용자 고유 비밀번호 입력
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # 1. 로그인
        log("로그인 페이지 접속 중...")
        page.goto(target_url, wait_until="networkidle")
        time.sleep(2.0)
        
        id_input = page.locator("input[type='text'], input[placeholder*='아이디'], input[name*='id'], #userId").first
        pw_input = page.locator("input[type='password'], input[placeholder*='비밀번호'], input[name*='pw'], #userPw").first
        
        id_input.fill(username)
        pw_input.fill(password)
        pw_input.press("Enter")
        
        log("로그인 완료, 대시보드 로딩 대기...")
        time.sleep(8.0)
        
        # 2. 사이드바 확장 (햄버거 클릭)
        log("사이드바 햄버거 메뉴 버튼 클릭 시도...")
        menu_btn = page.locator("button:has(svg[data-testid='MenuIcon']), .MuiIconButton-root:has(svg[data-testid='MenuIcon'])").first
        if menu_btn.is_visible():
            menu_btn.click()
            time.sleep(1.5)
            
        # 3. '모니터링' 대메뉴 클릭 (서브메뉴 확장)
        log("'모니터링' 대메뉴 클릭 시도...")
        monitoring_menu = page.locator("text=모니터링").first
        if monitoring_menu.is_visible():
            monitoring_menu.click()
            log("'모니터링' 클릭 완료! 2초 대기...")
            time.sleep(2.0)
            
        # 4. '동시계열데이터' 서브메뉴 클릭
        log("'동시계열데이터' 서브메뉴 클릭 시도...")
        timeseries_btn = page.locator("text=동시계열데이터").first
        if timeseries_btn.is_visible():
            timeseries_btn.click()
            log("'동시계열데이터' 클릭 완료! 페이지 로딩 대기 (6초)...")
            time.sleep(6.0)
        else:
            log("[!] '동시계열데이터' 버튼을 찾지 못했습니다.")
            
        # 5. 동시계열 데이터 페이지 DOM 저장
        html_content = page.content()
        html_path = os.path.join(DIAG_DIR, "04_timeseries_loaded.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        page.screenshot(path=os.path.join(DIAG_DIR, "04_timeseries_loaded.png"), full_page=True)
        log(f"동시계열 데이터 페이지 DOM 저장 완료: {os.path.basename(html_path)}")
        
        browser.close()

if __name__ == "__main__":
    run()
