import os
import sys
import time
import datetime
import random
from playwright.sync_api import sync_playwright

def log(msg):
    print(f"[*] {msg}", flush=True)

def format_date_range(start_str, end_str):
    s_dt = datetime.datetime.strptime(start_str, "%Y-%m-%d")
    e_dt = datetime.datetime.strptime(end_str, "%Y-%m-%d")
    s_formatted = s_dt.strftime("%Y.%m.%d.")
    e_formatted = e_dt.strftime("%Y.%m.%d.")
    return f"{s_formatted} \u2013 {e_formatted}"

def run_test():
    target_url = "https://jebitna.agri.jeju.kr/"
    username = ""  # 사용자 고유 아이디 입력
    password = ""  # 사용자 고유 비밀번호 입력
    
    # 1주일 테스트 범위
    test_start = "2026-05-11"
    test_end = "2026-05-17"
    date_range_str = format_date_range(test_start, test_end)
    log(f"변환된 날짜 입력값: '{date_range_str}'")
    
    download_dir = os.path.abspath("./test_downloads")
    os.makedirs(download_dir, exist_ok=True)
    
    with sync_playwright() as p:
        log("브라우저를 기동합니다...")
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
        log("로그인 페이지 접속...")
        page.goto(target_url, wait_until="networkidle")
        time.sleep(2.0)
        
        id_input = page.locator("input[type='text'], input[placeholder*='아이디'], input[name*='id'], #userId").first
        pw_input = page.locator("input[type='password'], input[placeholder*='비밀번호'], input[name*='pw'], #userPw").first
        
        id_input.fill(username)
        pw_input.fill(password)
        pw_input.press("Enter")
        
        log("로그인 성공 대기...")
        time.sleep(8.0)
        
        # 2. 사이드바 메뉴 열기 및 이동
        log("사이드바 햄버거 클릭...")
        menu_btn = page.locator("button:has(svg[data-testid='MenuIcon']), .MuiIconButton-root:has(svg[data-testid='MenuIcon'])").first
        if menu_btn.is_visible():
            menu_btn.click()
            time.sleep(1.5)
            
        log("'모니터링' 아코디언 메뉴 클릭...")
        monitoring_menu = page.locator("text=모니터링").first
        if monitoring_menu.is_visible():
            monitoring_menu.click()
            time.sleep(2.0)
            
        log("'동시계열데이터' 클릭...")
        timeseries_btn = page.locator("text=동시계열데이터").first
        if timeseries_btn.is_visible():
            timeseries_btn.click()
            log("동시계열데이터 페이지 로딩 대기...")
            time.sleep(6.0)
            
        # 3. 날짜 입력창 제어
        log("날짜 입력창을 탐색합니다...")
        date_input = page.locator("input[placeholder*='YYYY.MM.DD.']").first
        if date_input.is_visible():
            log("날짜 입력창 발견. 날짜 주입 중...")
            date_input.click()
            
            # 기존 날짜 지우기
            page.keyboard.press("Meta+A" if sys.platform == "darwin" else "Control+A")
            page.keyboard.press("Backspace")
            time.sleep(0.5)
            
            # 새 날짜 범위 주입
            date_input.fill(date_range_str)
            time.sleep(0.5)
            log(f"날짜 범위 주입 완료: {date_range_str}")
        else:
            log("[!] 날짜 입력창을 발견하지 못했습니다.")
            
        # 4. 장치 선택 (전체 선택)
        log("'전체 선택' 버튼 클릭 시도...")
        select_all_btn = page.locator("button:has-text('전체 선택')").first
        if select_all_btn.is_visible():
            select_all_btn.click()
            log("전체 선택 완료! 1.5초 대기...")
            time.sleep(1.5)
        else:
            log("[!] '전체 선택' 버튼을 발견하지 못했습니다.")
            
        # 5. 데이터 조회 클릭
        log("'데이터 조회' 버튼 클릭 시도...")
        query_btn = page.locator("button:has-text('데이터 조회')").first
        if query_btn.is_visible():
            query_btn.click()
            log("데이터 조회 완료! 차트 로딩 및 다운로드 활성화 대기 (6초)...")
            time.sleep(6.0)
        else:
            log("[!] '데이터 조회' 버튼을 발견하지 못했습니다.")
            
        # 6. 자료 다운로드 클릭
        log("'자료 다운로드' 버튼 클릭 시도...")
        download_btn = page.locator("button:has-text('자료 다운로드')").first
        if download_btn.is_visible() and not download_btn.is_disabled():
            log("다운로드 버튼 클릭 및 저장...")
            with page.expect_download(timeout=30000) as download_info:
                download_btn.click()
            download = download_info.value
            
            # 농가명 획득
            try:
                farm_name = page.locator("label:has-text('농장') + div input").get_attribute("value").strip().replace("/", "_")
            except Exception:
                farm_name = "기본농가"
                
            save_path = os.path.join(download_dir, f"{farm_name}_test_W01.xlsx")
            download.save_as(save_path)
            log(f"[✔] 테스트 수집 성공: {save_path}")
        else:
            log("[!] '자료 다운로드' 버튼을 발견하지 못했거나 비활성화 상태입니다.")
            
        browser.close()

if __name__ == "__main__":
    run_test()
