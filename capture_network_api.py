import os
import sys
import time
import json
from playwright.sync_api import sync_playwright

DIAG_DIR = os.path.abspath("./diagnostics")
os.makedirs(DIAG_DIR, exist_ok=True)

captured_requests = []

def log(msg):
    print(f"[*] {msg}", flush=True)

def handle_request(request):
    url = request.url
    # 관심 있는 API 요청만 상세 수집 (정적 파일 및 폰트 등은 필터링)
    if any(k in url for k in ["/api/", "download", "excel", "xlsx", "data", "growing", "monitoring", "timeseries", "time-series"]):
        req_info = {
            "url": url,
            "method": request.method,
            "headers": request.headers,
            "post_data": request.post_data,
            "resource_type": request.resource_type,
            "stage": "request"
        }
        captured_requests.append(req_info)
        log(f"[API Request] {request.method} -> {url}")

def handle_response(response):
    url = response.url
    if any(k in url for k in ["/api/", "download", "excel", "xlsx", "data", "growing", "monitoring", "timeseries", "time-series"]):
        res_info = {
            "url": url,
            "status": response.status,
            "headers": response.headers,
            "stage": "response"
        }
        captured_requests.append(res_info)
        log(f"[API Response] {response.status} <- {url}")

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
        
        # 네트워크 핸들러 등록
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        # 1. 로그인
        log("1. 로그인 페이지 접속 및 로그인 시도...")
        page.goto(target_url, wait_until="networkidle")
        time.sleep(2.0)
        page.locator("input[type='text']").first.fill(username)
        page.locator("input[type='password']").first.fill(password)
        page.locator("input[type='password']").first.press("Enter")
        time.sleep(8.0)
        
        # 2. 사이드바 네비게이션
        log("2. 사이드바 확장 및 동시계열데이터 페이지 이동...")
        page.locator("button:has(svg[data-testid='MenuIcon'])").first.click()
        time.sleep(1.5)
        page.locator("text=모니터링").first.click()
        time.sleep(2.0)
        page.locator("text=동시계열데이터").first.click()
        time.sleep(6.0)
        
        # 3. 날짜 설정 및 전체 선택
        log("3. 날짜 입력 및 센서 전체 선택...")
        date_range_str = "2026.05.15. \u2013 2026.05.22."
        date_input = page.locator("input[placeholder*='YYYY.MM.DD.']").first
        date_input.click()
        page.keyboard.press("Meta+A" if sys.platform == "darwin" else "Control+A")
        page.keyboard.press("Backspace")
        time.sleep(0.5)
        date_input.fill(date_range_str)
        page.keyboard.press("Enter")
        time.sleep(1.0)
        
        page.locator("button:has-text('전체 선택')").first.click()
        time.sleep(1.5)
        
        # 4. 데이터 조회 클릭
        log("4. 데이터 조회 클릭...")
        page.locator("button:has-text('데이터 조회')").first.click()
        time.sleep(12.0) # 데이터 패치 네트워크 대기
        
        # 5. 테이블 탭으로 이동
        log("5. 테이블 탭 클릭...")
        page.locator("text=테이블").first.click()
        time.sleep(3.0)
        
        # 6. EXCEL 버튼 클릭 및 실제 다운로드 진행
        log("6. EXCEL 버튼 클릭 및 다운로드 API 감시...")
        excel_btn = page.locator("button:has-text('EXCEL')").first
        if excel_btn.is_visible():
            try:
                with page.expect_download(timeout=20000) as download_info:
                    excel_btn.click()
                download = download_info.value
                log(f"성공적으로 수신한Suggested 파일명: {download.suggested_filename}")
            except Exception as e:
                log(f"다운로드 실행 중 오류: {str(e)}")
        else:
            log("EXCEL 다운로드 버튼이 미노출 상태입니다.")
            
        time.sleep(3.0)
        
        # 7. 수집된 모든 네트워크 로그 저장
        log("7. 네트워크 가로채기 결과 JSON 파일로 저장 중...")
        with open(os.path.join(DIAG_DIR, "api_requests.json"), "w", encoding="utf-8") as f:
            json.dump(captured_requests, f, indent=2, ensure_ascii=False)
        log("네트워크 수집 완료! (api_requests.json 저장 완료)")
        
        browser.close()

if __name__ == "__main__":
    run()
