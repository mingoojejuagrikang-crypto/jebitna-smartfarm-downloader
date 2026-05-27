import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

DIAG_DIR = os.path.abspath("./diagnostics")
os.makedirs(DIAG_DIR, exist_ok=True)

def log(msg):
    print(f"[*] {msg}", flush=True)

def save_diagnostic(page, step_name):
    """현재 브라우저 페이지의 HTML DOM과 스크린샷을 로컬 파일로 저장하는 유틸리티"""
    html_path = os.path.join(DIAG_DIR, f"{step_name}.html")
    png_path = os.path.join(DIAG_DIR, f"{step_name}.png")
    
    # 1. HTML DOM 덤프
    html_content = page.content()
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    # 2. 스크린샷 캡처
    page.screenshot(path=png_path, full_page=True)
    log(f"진단 아티팩트 저장 완료: {step_name} (HTML: {os.path.basename(html_path)}, PNG: {os.path.basename(png_path)})")

def run_diagnostics():
    target_url = "https://jebitna.agri.jeju.kr/"
    username = ""  # 사용자 고유 아이디 입력
    password = ""  # 사용자 고유 비밀번호 입력
    
    log(f"스마트팜 포털 진단을 시작합니다: {target_url}")
    
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
        
        # 1. 로그인 페이지 로드
        log("1. 로그인 페이지 접속 중...")
        page.goto(target_url, wait_until="networkidle")
        time.sleep(3.0)
        save_diagnostic(page, "01_login_page")
        
        # 2. 로그인 수행
        log("2. 로그인 입력 시도...")
        try:
            id_selectors = ["input[type='text']", "input[placeholder*='아이디']", "input[name*='id']", "#userId", "#loginId"]
            id_input = None
            for sel in id_selectors:
                if page.locator(sel).first.is_visible():
                    id_input = page.locator(sel).first
                    break
                    
            pw_selectors = ["input[type='password']", "input[placeholder*='비밀번호']", "input[name*='pw']", "#userPw", "#password"]
            pw_input = None
            for sel in pw_selectors:
                if page.locator(sel).first.is_visible():
                    pw_input = page.locator(sel).first
                    break
                    
            if id_input and pw_input:
                id_input.fill(username)
                time.sleep(0.5)
                pw_input.fill(password)
                time.sleep(0.5)
                pw_input.press("Enter")
                log("로그인 정보 입력 및 전송 완료")
            else:
                log("[!] 아이디/비밀번호 입력 요소를 식별할 수 없습니다.")
        except Exception as e:
            log(f"[!] 로그인 입력 중 에러 발생: {str(e)}")
            
        # 페이지 이동 및 세션 로드 대기
        log("로그인 성공 및 페이지 이동을 대기합니다 (8초)...")
        time.sleep(8.0)
        save_diagnostic(page, "02_after_login")
        
        # 3. '동시계열' 메뉴 접근
        log("3. '동시계열' 메뉴 클릭 시도...")
        menu_clicked = False
        try:
            menu_selectors = ["text=동시계열", "a:has-text('동시계열')", "span:has-text('동시계열')", "[class*='menu']:has-text('동시계열')"]
            for sel in menu_selectors:
                loc = page.locator(sel).first
                if loc.is_visible():
                    loc.click()
                    menu_clicked = True
                    log(f"메뉴 클릭 성공 (셀렉터: {sel})")
                    break
        except Exception as e:
            log(f"[!] 메뉴 클릭 중 에러 발생: {str(e)}")
            
        if not menu_clicked:
            log("[!] '동시계열' 메뉴 요소를 자동으로 식별하지 못했습니다.")
            log("[!] 브라우저 창에서 직접 '동시계열' 메뉴를 수동 클릭해 주시기 바랍니다 (10초 대기)...")
            time.sleep(10.0)
            
        # 이동 대기
        time.sleep(5.0)
        log("4. '동시계열' 페이지 로딩 완료 및 DOM 수집...")
        save_diagnostic(page, "03_time_series_page")
        
        log("진단이 완료되었습니다. 브라우저를 종료합니다.")
        context.close()
        browser.close()

if __name__ == "__main__":
    run_diagnostics()
