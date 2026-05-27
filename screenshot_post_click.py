import os
import sys
import time
import datetime
from playwright.sync_api import sync_playwright

DIAG_DIR = os.path.abspath("./diagnostics")

def log(msg):
    print(f"[*] {msg}", flush=True)

def format_date_range(start_str, end_str):
    s_dt = datetime.datetime.strptime(start_str, "%Y-%m-%d")
    e_dt = datetime.datetime.strptime(end_str, "%Y-%m-%d")
    s_formatted = s_dt.strftime("%Y.%m.%d.")
    e_formatted = e_dt.strftime("%Y.%m.%d.")
    return f"{s_formatted} \u2013 {e_formatted}"

def run():
    target_url = "https://jebitna.agri.jeju.kr/"
    username = ""  # 사용자 고유 아이디 입력
    password = ""  # 사용자 고유 비밀번호 입력
    date_range_str = format_date_range("2026-05-11", "2026-05-17")
    
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
        
        # 2. 사이드바 확장 및 이동
        page.locator("button:has(svg[data-testid='MenuIcon'])").first.click()
        time.sleep(1.5)
        page.locator("text=모니터링").first.click()
        time.sleep(2.0)
        page.locator("text=동시계열데이터").first.click()
        time.sleep(6.0)
        
        # 3. 2025년 5월 데이터 조회 테스트 (데이터가 풍부한 과거 기간)
        date_range_str = "2025.05.01. \u2013 2025.05.28."
        log(f"3. 2025년 5월 날짜 주입 시도: {date_range_str}")
        date_input = page.locator("input[placeholder*='YYYY.MM.DD.']").first
        date_input.click()
        page.keyboard.press("Meta+A" if sys.platform == "darwin" else "Control+A")
        page.keyboard.press("Backspace")
        time.sleep(0.5)
        date_input.fill(date_range_str)
        page.keyboard.press("Enter")
        time.sleep(1.0)
        
        # 4. 전체 선택 클릭 및 캡처
        log("4. '전체 선택' 버튼 클릭...")
        page.locator("button:has-text('전체 선택')").first.click()
        time.sleep(1.5)
        page.screenshot(path=os.path.join(DIAG_DIR, "05_after_select_all.png"), full_page=True)
        log("캡처 완료: 05_after_select_all.png")
        
        # 5. 데이터 조회 클릭 및 캡처
        log("5. '데이터 조회' 버튼 클릭...")
        query_btn = page.locator("button:has-text('데이터 조회')").first
        query_btn.click()
        
        # 로딩 애니메이션 또는 데이터가 렌더링되기를 기다림
        log("조회 결과 대기 중 (12초)...")
        time.sleep(12.0)
        page.screenshot(path=os.path.join(DIAG_DIR, "06_after_query.png"), full_page=True)
        log("캡처 완료: 06_after_query.png")
        
        # 6. '테이블' 탭 클릭 및 캡처
        log("6. '테이블' 탭 클릭...")
        page.locator("text=테이블").first.click()
        time.sleep(4.0)
        page.screenshot(path=os.path.join(DIAG_DIR, "07_after_table_tab.png"), full_page=True)
        log("캡처 완료: 07_after_table_tab.png")
        
        # 7. EXCEL 버튼 클릭 및 실제 다운로드 테스트
        log("7. 'EXCEL' 다운로드 버튼 찾기 및 다운로드 시도...")
        excel_btn = page.locator("button:has-text('EXCEL')").first
        if excel_btn.is_visible():
            try:
                log("EXCEL 버튼 발견! 다운로드 스트림 대기...")
                with page.expect_download(timeout=20000) as download_info:
                    excel_btn.click()
                download = download_info.value
                suggested_fn = download.suggested_filename
                log(f"다운로드 성공! 제안된 파일명: {suggested_fn}")
                
                # 테스트 폴더에 다운로드 파일 저장해보기
                test_dir = os.path.abspath("./test_downloads")
                os.makedirs(test_dir, exist_ok=True)
                download_path = os.path.join(test_dir, suggested_fn)
                download.save_as(download_path)
                log(f"테스트 다운로드 파일 저장 완료: {download_path}")
            except Exception as e:
                log(f"다운로드 실행 중 오류 발생: {str(e)}")
        else:
            log("EXCEL 다운로드 버튼이 보이지 않습니다. 데이터가 없는 상태일 수 있습니다.")
            
        browser.close()

if __name__ == "__main__":
    run()
