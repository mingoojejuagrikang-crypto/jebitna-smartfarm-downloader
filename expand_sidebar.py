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
        
        # 2. 햄버거 메뉴 아이콘 클릭 시도 (사이드바 확장)
        log("사이드바 메뉴 버튼(햄버거 아이콘) 탐색 및 클릭 시도...")
        menu_btn = page.locator("button:has(svg[data-testid='MenuIcon']), .MuiIconButton-root:has(svg[data-testid='MenuIcon'])").first
        if menu_btn.is_visible():
            menu_btn.click()
            log("사이드바 메뉴 버튼 클릭 완료! 3초 대기...")
            time.sleep(3.0)
        else:
            log("사이드바 메뉴 버튼을 찾지 못했습니다. 일반 버튼 리스트 중 svg가 포함된 버튼을 찾아 클릭합니다.")
            buttons = page.locator("button")
            clicked = False
            for i in range(buttons.count()):
                btn = buttons.nth(i)
                if btn.locator("svg").count() > 0:
                    btn.click()
                    clicked = True
                    log("svg 포함 버튼 클릭 성공")
                    time.sleep(3.0)
                    break
            if not clicked:
                log("사이드바 메뉴 확장 버튼 클릭에 실패했습니다.")
        
        # 3. 확장된 상태의 DOM 저장
        html_content = page.content()
        html_path = os.path.join(DIAG_DIR, "02_expanded_sidebar.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        page.screenshot(path=os.path.join(DIAG_DIR, "02_expanded_sidebar.png"), full_page=True)
        log(f"확장된 사이드바 DOM 저장 완료: {os.path.basename(html_path)}")
        
        browser.close()

if __name__ == "__main__":
    run()
