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
        page.goto(target_url, wait_until="networkidle")
        time.sleep(2.0)
        page.locator("input[type='text']").first.fill(username)
        page.locator("input[type='password']").first.fill(password)
        page.locator("input[type='password']").first.press("Enter")
        time.sleep(8.0)
        
        # 2. 사이드바 이동
        page.locator("button:has(svg[data-testid='MenuIcon'])").first.click()
        time.sleep(1.5)
        page.locator("text=모니터링").first.click()
        time.sleep(2.0)
        page.locator("text=동시계열데이터").first.click()
        time.sleep(6.0)
        
        # 3. '작물' 입력 필드 클릭 (MUI Autocomplete dropdown 열기)
        log("3. '작물' 입력창 클릭 시도...")
        crop_input = page.locator("input[placeholder*='작물']").first
        if crop_input.is_visible():
            crop_input.click()
            time.sleep(2.5) # 드롭다운 애니메이션 대기
            
            # 드롭다운 옵션 DOM 저장 및 캡처
            page.screenshot(path=os.path.join(DIAG_DIR, "07_crop_dropdown.png"), full_page=True)
            log("캡처 완료: 07_crop_dropdown.png")
            
            with open(os.path.join(DIAG_DIR, "07_crop_dropdown.html"), "w", encoding="utf-8") as f:
                f.write(page.content())
            log("작물 드롭다운 DOM 저장 완료")
        else:
            log("[!] '작물' 입력창을 찾지 못했습니다.")
            
        browser.close()

if __name__ == "__main__":
    run()
