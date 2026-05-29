import os
import sys
import json
import subprocess
import threading
import queue
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler

# -------------------------------------------------------------
# macOS .app 패키지 더블클릭 기동 시 CWD가 '/'로 고정되는 문제 해결
# -------------------------------------------------------------
if getattr(sys, 'frozen', False):
    bundle_dir = os.path.dirname(sys.executable)
    if "Contents/MacOS" in bundle_dir:
        # .app 파일이 존재하는 외부 부모 디렉토리를 작업 폴더로 지정
        base_dir = os.path.abspath(os.path.join(bundle_dir, "../../../"))
    else:
        base_dir = bundle_dir
    try:
        os.chdir(base_dir)
    except Exception as e:
        pass

PORT = 8080
active_process = None
log_queue = queue.Queue()
process_running = False

HTML_CONTENT = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SmartFarm Bulk Downloader Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            --glass-bg: rgba(30, 41, 59, 0.45);
            --glass-border: rgba(255, 255, 255, 0.08);
            --accent-primary: #8b5cf6;
            --accent-glow: rgba(139, 92, 246, 0.4);
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Inter', sans-serif;
            -webkit-font-smoothing: antialiased;
        }

        body {
            background: var(--bg-gradient);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 2rem;
            overflow-x: hidden;
        }

        .container {
            width: 100%;
            max-width: 1200px;
            display: grid;
            grid-template-columns: 1fr 1.5fr;
            gap: 2rem;
            height: 90vh;
            max-height: 900px;
        }

        /* Glassmorphism Panel styles */
        .glass-panel {
            background: var(--glass-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--glass-border);
            border-radius: 24px;
            padding: 2.5rem;
            display: flex;
            flex-direction: column;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            overflow: hidden;
            position: relative;
        }

        .glass-panel::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--accent-primary), #ec4899);
            border-radius: 24px 24px 0 0;
        }

        h1 {
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
            font-size: 2rem;
            letter-spacing: -0.03em;
            background: linear-gradient(to right, #ffffff, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }

        .subtitle {
            color: var(--text-muted);
            font-size: 0.9rem;
            margin-bottom: 2rem;
        }

        .form-group {
            margin-bottom: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        label {
            color: var(--text-main);
            font-weight: 500;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        input {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            padding: 0.85rem 1rem;
            color: var(--text-main);
            font-size: 0.95rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        input:focus {
            outline: none;
            border-color: var(--accent-primary);
            box-shadow: 0 0 12px var(--accent-glow);
        }

        .row-inputs {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }

        .btn-container {
            margin-top: auto;
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 1rem;
        }

        button {
            border: none;
            border-radius: 14px;
            padding: 1rem;
            font-weight: 600;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }

        .btn-start {
            background: var(--accent-primary);
            color: #fff;
            box-shadow: 0 4px 20px var(--accent-glow);
        }

        .btn-start:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 6px 24px rgba(139, 92, 246, 0.6);
            filter: brightness(1.1);
        }

        .btn-stop {
            background: rgba(239, 68, 68, 0.2);
            color: var(--danger);
            border: 1px solid rgba(239, 68, 68, 0.4);
        }

        .btn-stop:hover:not(:disabled) {
            background: var(--danger);
            color: #fff;
            box-shadow: 0 4px 16px rgba(239, 68, 68, 0.4);
        }

        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none !important;
            box-shadow: none !important;
        }

        /* Right Dashboard layout */
        .dashboard-content {
            display: grid;
            grid-template-rows: auto 1fr;
            gap: 1.5rem;
            height: 100%;
            min-height: 0;
        }

        /* Progress Card */
        .status-card {
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            min-height: 0;
        }

        .progress-circle-container {
            position: relative;
            width: 80px;
            height: 80px;
        }

        .progress-circle {
            transform: rotate(-90deg);
        }

        .progress-circle-bg {
            fill: none;
            stroke: rgba(255, 255, 255, 0.05);
            stroke-width: 8;
        }

        .progress-circle-bar {
            fill: none;
            stroke: var(--accent-primary);
            stroke-width: 8;
            stroke-dasharray: 226;
            stroke-dashoffset: 226;
            stroke-linecap: round;
            transition: stroke-dashoffset 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .progress-text {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-main);
        }

        .status-info {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
            flex: 1;
            margin-left: 1.5rem;
        }

        .status-label {
            font-size: 0.8rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .status-val {
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--text-main);
        }

        /* Terminal Console */
        .terminal {
            background: rgba(10, 15, 30, 0.75);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.8);
            min-height: 0;
        }

        .terminal-header {
            background: rgba(15, 23, 42, 0.8);
            padding: 0.75rem 1.25rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--glass-border);
        }

        .dots {
            display: flex;
            gap: 6px;
        }

        .dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }

        .dot-red { background: var(--danger); }
        .dot-yellow { background: var(--warning); }
        .dot-green { background: var(--success); }

        .terminal-title {
            color: var(--text-muted);
            font-size: 0.75rem;
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.1em;
        }

        .terminal-body {
            padding: 1.5rem;
            flex: 1;
            overflow-y: auto;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.85rem;
            line-height: 1.5;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .log-entry {
            display: flex;
            gap: 0.75rem;
            animation: fadeIn 0.25s ease-out forwards;
        }

        .log-time {
            color: var(--accent-primary);
            flex-shrink: 0;
        }

        .log-msg {
            color: var(--text-main);
            word-break: break-all;
        }

        .log-success { color: var(--success); }
        .log-warning { color: var(--warning); }
        .log-error { color: var(--danger); font-weight: 600; }
        .log-progress { color: #38bdf8; font-weight: 500; }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(4px); }
            to { opacity: 1; transform: translateY(0); }
        }

        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.1);
        }

        ::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: rgba(255, 255, 255, 0.2);
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Configuration Panel -->
        <div class="glass-panel">
            <h1>시계열 다운로더</h1>
            <p class="subtitle">3개년 주차별 스마트팜 데이터 자동 추출</p>
            
            <div class="form-group">
                <label>접속 대상 URL</label>
                <input type="text" id="target_url" value="https://jebitna.agri.jeju.kr/">
            </div>

            <div class="row-inputs">
                <div class="form-group">
                    <label>포털 ID</label>
                    <input type="text" id="username" placeholder="아이디 입력" value="">
                </div>
                <div class="form-group">
                    <label>포털 비밀번호</label>
                    <input type="password" id="password" placeholder="비밀번호 입력" value="">
                </div>
            </div>

            <div class="row-inputs">
                <div class="form-group">
                    <label>수집 시작일</label>
                    <input type="date" id="start_date" value="2026-04-27">
                </div>
                <div class="form-group">
                    <label>수집 종료일</label>
                    <input type="date" id="end_date" value="2026-05-27">
                </div>
            </div>

            <div class="form-group">
                <label>다운로드 경로</label>
                <input type="text" id="download_dir" value="./downloads">
            </div>

            <div class="btn-container">
                <button class="btn-start" id="btn-start" onclick="startDownload()">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                    다운로드 자동화 시작
                </button>
                <button class="btn-stop" id="btn-stop" onclick="stopDownload()" disabled>
                    중지
                </button>
            </div>
        </div>

        <!-- Dashboard Console -->
        <div class="dashboard-content">
            <!-- Progress Tracker -->
            <div class="status-card">
                <div class="progress-circle-container">
                    <svg class="progress-circle" width="80" height="80">
                        <circle class="progress-circle-bg" cx="40" cy="40" r="36"/>
                        <circle class="progress-circle-bar" id="progress-bar" cx="40" cy="40" r="36"/>
                    </svg>
                    <div class="progress-text" id="progress-percent">0%</div>
                </div>
                <div class="status-info">
                    <div class="status-label">현재 다운로드 상태</div>
                    <div class="status-val" id="status-title">대기 중</div>
                </div>
            </div>

            <!-- Beautiful Logger Terminal -->
            <div class="terminal">
                <div class="terminal-header">
                    <div class="dots">
                        <div class="dot dot-red"></div>
                        <div class="dot dot-yellow"></div>
                        <div class="dot dot-green"></div>
                    </div>
                    <div class="terminal-title">자동화 동작 실시간 콘솔</div>
                    <div></div>
                </div>
                <div class="terminal-body" id="console-logs">
                    <div class="log-entry">
                        <span class="log-time">[00:00:00]</span>
                        <span class="log-msg">스마트팜 3개년 데이터 추출 대시보드가 성공적으로 열렸습니다. 설정을 맞추고 '시작' 버튼을 누르세요.</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let eventSource = null;

        function updateProgress(percent) {
            const circle = document.getElementById("progress-bar");
            const text = document.getElementById("progress-percent");
            const r = 36;
            const c = 2 * Math.PI * r;
            
            circle.style.strokeDasharray = c;
            circle.style.strokeDashoffset = c - (percent / 100) * c;
            text.innerText = `${Math.round(percent)}%`;
        }

        function appendLog(time, msg, type = "info") {
            const consoleLogs = document.getElementById("console-logs");
            const entry = document.createElement("div");
            entry.className = "log-entry";
            
            let classColor = "log-msg";
            if (type === "success") classColor = "log-success";
            else if (type === "warning") classColor = "log-warning";
            else if (type === "error") classColor = "log-error";
            else if (type === "progress") classColor = "log-progress";

            entry.innerHTML = `
                <span class="log-time">[${time}]</span>
                <span class="${classColor}">${msg}</span>
            `;
            consoleLogs.appendChild(entry);
            consoleLogs.scrollTop = consoleLogs.scrollHeight;
        }

        function startDownload() {
            const btnStart = document.getElementById("btn-start");
            const btnStop = document.getElementById("btn-stop");
            
            btnStart.disabled = true;
            btnStop.disabled = false;
            
            document.getElementById("status-title").innerText = "동작 준비 중...";
            
            const config = {
                target_url: document.getElementById("target_url").value,
                username: document.getElementById("username").value,
                password: document.getElementById("password").value,
                start_date: document.getElementById("start_date").value,
                end_date: document.getElementById("end_date").value,
                download_dir: document.getElementById("download_dir").value
            };

            fetch("/api/start", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(config)
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === "started") {
                    document.getElementById("status-title").innerText = "로그인 및 사이트 접속 중";
                    connectStream();
                } else {
                    alert(`시작 실패: ${data.message}`);
                    resetUI();
                }
            })
            .catch(err => {
                alert(`오류 발생: ${err}`);
                resetUI();
            });
        }

        function stopDownload() {
            fetch("/api/stop", { method: "POST" })
            .then(res => res.json())
            .then(data => {
                appendLog(new Date().toLocaleTimeString(), "사용자에 의해 자동화가 강제 중지되었습니다.", "error");
                resetUI();
            });
        }

        function resetUI() {
            document.getElementById("btn-start").disabled = false;
            document.getElementById("btn-stop").disabled = true;
            document.getElementById("status-title").innerText = "중지됨 / 대기 중";
            if (eventSource) {
                eventSource.close();
                eventSource = null;
            }
        }

        function connectStream() {
            if (eventSource) eventSource.close();
            
            eventSource = new EventSource("/api/stream");
            
            eventSource.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    
                    // 무의미한 heartbeat 빈 객체 {} 필터링
                    if (!data.message && !data.status) return;
                    
                    if (data.status === "complete") {
                        document.getElementById("status-title").innerText = "전체 수집 완료";
                        updateProgress(100);
                        appendLog(data.timestamp, data.message, "success");
                        resetUI();
                        return;
                    }

                    if (data.status === "progress") {
                        // "현재 [X/Y] 주차 시작" 로그 구조 파싱
                        const match = data.message.match(/\[(\d+)\/(\d+)\]/);
                        if (match) {
                            const cur = parseInt(match[1]);
                            const tot = parseInt(match[2]);
                            const pct = (cur / tot) * 100;
                            updateProgress(pct);
                            document.getElementById("status-title").innerText = `진행 중 (${cur}/${tot} 주차)`;
                        }
                        appendLog(data.timestamp, data.message, "progress");
                    } else {
                        appendLog(data.timestamp, data.message, data.status);
                    }
                    
                } catch (e) {
                    // JSON 형식이 아닌 원본 문자열일 경우
                    if (event.data && event.data.trim() !== "") {
                        appendLog(new Date().toLocaleTimeString(), event.data, "info");
                    }
                }
            };

            eventSource.onerror = function() {
                // 접속 해제되었을 때 로직
                resetUI();
            };
        }

        // 브라우저 탭/창 종료 시 파이썬 백엔드 서버도 함께 종료하도록 신호 전송
        window.addEventListener("beforeunload", function() {
            navigator.sendBeacon("/api/shutdown");
        });
    </script>
</body>
</html>
"""

class DashboardServer(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # 터미널에 불필요한 HTTP GET/POST 로그가 과도하게 쌓이지 않도록 뮤트 처리
        return

    def do_GET(self):
        global process_running
        if self.path in ["/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode("utf-8"))
            
        elif self.path == "/api/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            # SSE 스트림 파이프 연결
            while process_running or not log_queue.empty():
                try:
                    # 로그 큐에서 데이터를 받아 웹페이지로 흘려보냄
                    log_data = log_queue.get(timeout=0.5)
                    self.wfile.write(f"data: {log_data}\n\n".encode("utf-8"))
                    self.wfile.flush()
                except queue.Empty:
                    # 무동작 중에도 연결이 유지되도록 ping/보온 데이터 송신
                    try:
                        self.wfile.write("data: {}\n\n".encode("utf-8"))
                        self.wfile.flush()
                    except Exception:
                        break
                except Exception:
                    break

        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        global active_process, process_running
        
        # CORS 사전 정의
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        
        if self.path == "/api/start":
            content_length = int(self.headers["Content-Length"])
            body = self.rfile.read(content_length)
            config = json.loads(body.decode("utf-8"))
            
            if process_running:
                self.wfile.write(json.dumps({"status": "error", "message": "이미 자동화가 진행 중입니다."}).encode("utf-8"))
                return
                
            # 큐 리셋
            while not log_queue.empty():
                log_queue.get()
                
            # 자동화 서브프로세스(Playwright 스크립트) 시작
            process_running = True
            threading.Thread(target=self.run_subprocess, args=(config,), daemon=True).start()
            
            self.wfile.write(json.dumps({"status": "started"}).encode("utf-8"))
            
        elif self.path == "/api/stop":
            process_running = False
            self.wfile.write(json.dumps({"status": "stopped"}).encode("utf-8"))

        elif self.path == "/api/shutdown":
            process_running = False
            self.wfile.write(json.dumps({"status": "shutdown"}).encode("utf-8"))
            # Shutdown the server in a separate thread so this request can complete
            threading.Thread(target=self.server.shutdown, daemon=True).start()

    def run_subprocess(self, config):
        global process_running
        
        try:
            # 1. automation_runner 모듈을 동적 임포트하여 인메모리로 실행!
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import automation_runner
            
            # 2. 실시간 SSE 전송을 위한 로깅 콜백 구현
            def sse_log_callback(log_data):
                log_queue.put(json.dumps(log_data))
                
            # 3. 중지 상태 확인용 콜백
            def check_stop_flag():
                return not process_running
                
            # 4. 인메모리 기동
            automation_runner.run_automation(config, callback=sse_log_callback, check_stop=check_stop_flag)
            
        except Exception as e:
            err_data = {
                "timestamp": time.strftime("%H:%M:%S"),
                "status": "error",
                "message": f"자동화 실행 중 에러 발생: {str(e)}"
            }
            log_queue.put(json.dumps(err_data))
        finally:
            process_running = False

def start_server():
    server = HTTPServer(("localhost", PORT), DashboardServer)
    print(f"===========================================================")
    print(f"   [SmartFarm Downloader Server] http://localhost:{PORT}   ")
    print(f"===========================================================")
    
    # 자동으로 사용자 브라우저를 열어 UI 제공
    threading.Thread(target=lambda: (time.sleep(1), webbrowser.open(f"http://localhost:{PORT}")), daemon=True).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n서버를 종료합니다.")
        server.server_close()

if __name__ == "__main__":
    start_server()
