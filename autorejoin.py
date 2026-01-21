import time, os, subprocess, requests, psutil, sys, re, json, io, platform, glob
from datetime import datetime
import pyautogui

# ==========================================================
# HÀM HỖ TRỢ ĐƯỜNG DẪN (QUAN TRỌNG CHO .EXE)
# ==========================================================
def get_script_dir():
    """Lấy đường dẫn thư mục chứa file chạy (.py hoặc .exe)"""
    if getattr(sys, 'frozen', False):
        # Nếu đang chạy dạng .exe (PyInstaller)
        return os.path.dirname(sys.executable)
    # Nếu đang chạy dạng script .py
    return os.path.dirname(os.path.abspath(__file__))

# ==========================================================
# CẤU HÌNH AUTO UPDATE
# ==========================================================
CURRENT_VERSION = "1.1"
REPO_ROOT = "https://raw.githubusercontent.com/tranduyminh493-coder/rejoin-tool/refs/heads/main"
VERSION_URL = f"{REPO_ROOT}/version.txt"
CODE_URL    = f"{REPO_ROOT}/autorejoin.py"
EXE_URL     = f"{REPO_ROOT}/autorejoin.exe"

def check_for_updates():
    """Kiểm tra và tự động cập nhật tool (Hỗ trợ cả .py và .exe)"""
    if "LINK_RAW" in VERSION_URL: return

    print(f"   ☁️  Đang kiểm tra bản cập nhật... (v{CURRENT_VERSION})")
    try:
        response = requests.get(VERSION_URL, timeout=5)
        if response.status_code != 200: return
        
        new_version = response.text.strip()
        
        if new_version == CURRENT_VERSION:
            print(f"   ✅  Bạn đang dùng phiên bản mới nhất.")
            return

        print(f"   🚀  Phát hiện bản mới: v{new_version}")
        print("   📥  Đang tải xuống bản cập nhật...")

        is_exe = getattr(sys, 'frozen', False)
        download_url = EXE_URL if is_exe else CODE_URL
        
        r = requests.get(download_url, stream=True, timeout=15)
        if r.status_code == 200:
            current_file = os.path.abspath(sys.argv[0]) if is_exe else os.path.abspath(__file__)
            dir_path = os.path.dirname(current_file)
            
            if is_exe:
                new_file_name = "update_temp.exe"
                new_file_path = os.path.join(dir_path, new_file_name)
                with open(new_file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                print("   📦  Đã tải xong. Đang chuẩn bị cài đặt...")
                
                bat_script = f"""
@echo off
timeout /t 2 /nobreak > NUL
del "{current_file}"
ren "{new_file_name}" "{os.path.basename(current_file)}"
start "" "{current_file}"
del "%~f0"
"""
                bat_path = os.path.join(dir_path, "updater.bat")
                with open(bat_path, "w") as f:
                    f.write(bat_script)
                
                print("   🔄  Tool sẽ tự khởi động lại ngay bây giờ...")
                os.startfile(bat_path)
                sys.exit(0)
            else:
                with open(current_file, "wb") as f:
                    f.write(r.content)
                print("   ✅  Cập nhật Code thành công!")
                print("   🔁  Vui lòng khởi động lại tool.")
                input("Nhấn Enter để thoát...")
                sys.exit(0)
        else:
            print(f"   ❌  Lỗi tải file: Status {r.status_code}")
    except Exception as e:
        print(f"   ⚠️  Lỗi Update: {e}")

# ==========================================================
# CẤU HÌNH CONFIG FILE
# ==========================================================
def load_config():
    config = {}
    script_dir = get_script_dir()
    config_path = os.path.join(script_dir, "config.txt")
    
    if not os.path.exists(config_path):
        print(f"-> Chưa thấy file config. Đang tạo mới tại: {config_path}")
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                f.write("# Cấu hình Tool Auto Rejoin Roblox\n")
                f.write("# Điền thông tin vào sau dấu =\n")
                f.write("COOKIE=\n")
                f.write("PLACE_ID=\n")
                f.write("WEBHOOK_URL=\n")
                f.write("# Dán Link Server VIP (SVV) hoặc Code VIP vào dưới\n")
                f.write("VIP_CODE=\n")
            
            print("----------------------------------------------------------------")
            print("ĐÃ TẠO FILE CONFIG.TXT THÀNH CÔNG!")
            print("Vui lòng mở file config.txt và điền đầy đủ thông tin:")
            print(" - COOKIE")
            print(" - PLACE_ID (ID game)")
            print(" - WEBHOOK_URL (Link Webhook Discord)")
            print(" - VIP_CODE (Link Server VIP)")
            print("Sau khi điền xong, hãy lưu file và chạy lại tool.")
            print("----------------------------------------------------------------")
        except Exception as e:
            print(f"Lỗi khi tạo file config: {e}")
            
        input("Nhấn Enter để thoát...")
        sys.exit(1)
    
    with open(config_path, "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.strip().split("=", 1)
                config[key.strip()] = value.strip()
    return config

config = load_config()

COOKIE_CUA_BAN = config.get("COOKIE", "")
VIP_CODE = config.get("VIP_CODE", "")
if "privateServerLinkCode" in VIP_CODE:
    match = re.search(r'privateServerLinkCode=([^&]+)', VIP_CODE)
    if match:
        VIP_CODE = match.group(1)

PLACE_ID = config.get("PLACE_ID", "")
DISCORD_WEBHOOK_URL = config.get("WEBHOOK_URL", "")
IMAGE_FILE = "disconnect_alert.png" 
LOBBY_FILE = "lobby.png"

if not COOKIE_CUA_BAN or not PLACE_ID:
    print("Lỗi: config.txt thiếu COOKIE hoặc PLACE_ID!")
    sys.exit(1)

count_rejoin = 0
start_time = datetime.now()

def hien_thi_bang(trang_thai):
    os.system('cls' if os.name == 'nt' else 'clear')
    uptime = str(datetime.now() - start_time).split('.')[0]
    if os.name == 'nt':
        os.system(f"title CAO TUẤN ANH AUTO REJOIN - Uptime: {uptime} - Rejoined: {count_rejoin}")

    CYAN = "\033[96m" 
    MAGENTA = "\033[95m"
    GREEN = "\033[92m" 
    YELLOW = "\033[93m"
    WHITE = "\033[97m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    print(f"{CYAN}{'='*62}{RESET}")
    print(f"{MAGENTA}{BOLD}   CAO TUẤN ANH AUTO REJOIN   {RESET} | {GREEN} Ultimate Roblox Tool {RESET}")
    print(f"{CYAN}{'='*62}{RESET}")
    print(f"  {YELLOW}⏳ Thời gian chạy :{RESET} {WHITE}{uptime}{RESET}")
    print(f"  {YELLOW}🔄 Đã Rejoin      :{RESET} {WHITE}{count_rejoin} lần{RESET}")
    print(f"  {YELLOW}📢 Trạng thái     :{RESET} {WHITE}{trang_thai}{RESET}")
    print(f"{CYAN}{'='*62}{RESET}")

def check_roblox_log_status():
    try:
        log_path = os.path.expandvars(r"%LocalAppData%\Roblox\logs")
        if not os.path.exists(log_path): return False
        list_of_files = glob.glob(os.path.join(log_path, '0.*_Player_*.log'))
        if not list_of_files: return False
        latest_file = max(list_of_files, key=os.path.getmtime)
        with open(latest_file, 'rb') as f:
            try: f.seek(-5000, 2) 
            except OSError: f.seek(0)
            content = f.read().decode('utf-8', errors='ignore')
            disconnect_keywords = ["Connection lost", "Time to disconnect", "Disconnect event received", "Client initiated disconnect", "Connection closed"]
            for kw in disconnect_keywords:
                if kw in content:
                    last_disconnect = content.rfind(kw)
                    last_connect = content.rfind("Connecting to")
                    if last_disconnect > last_connect: return True
    except: pass
    return False

def get_authenticated_user_id(session):
    try:
        response = session.get("https://users.roblox.com/v1/users/authenticated", timeout=10)
        if response.status_code == 200: return response.json().get("id")
    except: pass
    return None

def check_presence_status(session, user_id):
    try:
        url = "https://presence.roblox.com/v1/presence/users"
        payload = {"userIds": [user_id]}
        response = session.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            user_presences = response.json().get("userPresences", [])
            if user_presences: return user_presences[0].get("userPresenceType")
    except: pass
    return None

def kiem_tra_roblox_treo():
    if not os.path.exists(IMAGE_FILE): return False
    try:
        pos = pyautogui.locateOnScreen(IMAGE_FILE, confidence=0.8, grayscale=True)
        if pos: return True
    except: pass
    return False

def bypass_launch():
    hien_thi_bang("Error detected! Rejoining...")
    print("   -> Closing old Roblox...")
    os.system("taskkill /F /IM RobloxPlayerBeta.exe /T >nul 2>&1")
    time.sleep(2)

    global count_rejoin
    clean_cookie = re.sub(r'\s+', '', COOKIE_CUA_BAN)
    session = requests.Session()
    session.cookies.set(".ROBLOSECURITY", clean_cookie, domain="roblox.com")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": f"https://www.roblox.com/games/{PLACE_ID}/",
        "Origin": "https://www.roblox.com",
        "Content-Type": "application/json"
    }
    
    try:
        print("   -> Đang kết nối lấy Authentication Ticket...")
        r1 = session.post("https://auth.roblox.com/v1/authentication-ticket", headers=headers, json={}, timeout=15)
        csrf_token = r1.headers.get("x-csrf-token")
        if not csrf_token:
            print(f"Warning: x-csrf-token not found (Status: {r1.status_code})")
            print("   -> Retrying in 5s...")
            return False

        headers["x-csrf-token"] = csrf_token
        r2 = session.post("https://auth.roblox.com/v1/authentication-ticket", headers=headers, json={}, timeout=15)
        ticket = r2.headers.get("rbx-authentication-ticket")
        
        if ticket:
            print("   -> Ticket obtained! Preparing to launch...")
            launch_cmd = f"roblox-player:1+launchmode:play+gameinfo:{ticket}+launchtime:{int(time.time()*1000)}+placelauncherurl:https%3A%2F%2Fassetgame.roblox.com%2Fgame%2FPlaceLauncher.ashx%3Frequest%3DPlugin%26placeId%3D{PLACE_ID}%26linkCode%3D{VIP_CODE}"
            os.system(f'start "" "{launch_cmd}"')
            count_rejoin += 1
            hien_thi_bang(f"Rejoin Success #{count_rejoin}!")
            return True
        else:
            print(f"Failed to get Ticket. Status: {r2.status_code}")
            if r2.status_code == 401: print("   -> Cookie expired or invalid.")
    except Exception as e:
        print(f"Unknown Error: {e}")
    return False

def kiem_tra_o_lobby():
    if not os.path.exists(LOBBY_FILE): return False
    try:
        pos = pyautogui.locateOnScreen(LOBBY_FILE, confidence=0.8, grayscale=True)
        if pos: return True
    except: pass
    return False

def send_screenshot_to_discord():
    try:
        pc_name = platform.node()
        cpu_name = platform.processor()
        logical_cores = psutil.cpu_count(logical=True)
        physical_cores = psutil.cpu_count(logical=False)
        ram = psutil.virtual_memory()
        total_ram_gb = f"{ram.total / (1024**3):.2f} GB"
        ram_percent = ram.percent
        platform_info = platform.platform()
        
        roblox_count = 0
        for p in psutil.process_iter(['name']):
            try:
                if p.info['name'] == 'RobloxPlayerBeta.exe': roblox_count += 1
            except: pass

        screenshot = pyautogui.screenshot()
        img_buffer = io.BytesIO()
        screenshot.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        embed = {
            "title": "🖥️ PC STATUS",
            "description": "**System Information**",
            "color": 3066993, 
            "fields": [
                {"name": "👤 PC Name", "value": f"`{pc_name}`", "inline": True},
                {"name": "🪟 Platform", "value": f"`{platform_info}`", "inline": True},
                {"name": "\u200b", "value": "\u200b", "inline": False},
                {"name": "🧠 CPU", "value": f"`{cpu_name}`", "inline": False},
                {"name": "⚙️ Cores/Threads", "value": f"`{physical_cores} Cores` | `{logical_cores} Threads`", "inline": True},
                {"name": "💾 Total RAM", "value": f"`{total_ram_gb}`", "inline": True},
                {"name": "\u200b", "value": "\u200b", "inline": False}, 
                {"name": "📼 RAM Usage", "value": f"```\n{ram_percent}%\n```", "inline": True},
                {"name": "🎮 Roblox Active", "value": f"```\n{roblox_count} process(es)\n```", "inline": True},
            ],
            "image": {"url": "attachment://screenshot.png"},
            "footer": {"text": f"| https://VuHaiBinh11A1.gg | {datetime.now().strftime('%H:%M - %d/%m/%Y')}", "icon_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Octicons-mark-github.svg/600px-Octicons-mark-github.svg.png"}
        }

        files = {'file': ('screenshot.png', img_buffer, 'image/png')}
        data = {"payload_json": json.dumps({"embeds": [embed]})}
        requests.post(DISCORD_WEBHOOK_URL, data=data, files=files)
        masked_url = DISCORD_WEBHOOK_URL[-20:] if len(DISCORD_WEBHOOK_URL) > 20 else "..."
        print(f"✅ Screenshot sent to Webhook (...{masked_url})")
    except Exception as e:
        print(f"Webhook Error: {e}")

def check_key():
    """Yêu cầu nhập Work.ink Token để sử dụng tool"""
    script_dir = get_script_dir()
    key_file = os.path.join(script_dir, "key.txt")
    
    def check_token_validity(token):
        try:
            url = f"https://work.ink/_api/v2/token/isValid/{token}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) python-requests/2.31.0"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200: return False, f"Server Error {response.status_code}"
            data = response.json()
            if data.get("valid") == True: return True, "Valid"
            else: return False, data.get("message", "Token validation failed")
        except Exception as e: return False, str(e)

    if os.path.exists(key_file):
        print("\n   ⏳ Đang kiểm tra Key đã lưu...")
        try:
            with open(key_file, "r", encoding="utf-8") as f:
                saved_token = f.read().strip()
            if saved_token:
                is_valid, msg = check_token_validity(saved_token)
                if is_valid:
                    print(f"   ✅ \033[92mKey đã lưu hợp lệ! ({saved_token[:8]}...)\033[0m")
                    time.sleep(1)
                    return 
                else:
                    print(f"   ❌ \033[91mKey đã lưu hết hạn hoặc lỗi: {msg}\033[0m")
                    print("   👉 Vui lòng lấy Key mới.")
                    time.sleep(2)
        except Exception as e: print(f"   ⚠️  Lỗi đọc key file: {e}")

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"\033[96m{'='*60}\033[0m")
        print(f"\033[93m{'🔒 HỆ THỐNG BẢO MẬT - WORK.INK KEY SYSTEM':^60}\033[0m")
        print(f"\033[96m{'='*60}\033[0m")
        print("\n")
        print("   👉 Link lấy Key mới: https://work.ink/2a0V/ctatool")
        print("   (Copy link và dán vào trình duyệt web)")
        print("\n")
        
        try:
            user_input = input("   🔑 Nhập Token: ").strip()
            if not user_input: continue
            print("   ⏳ Đang kiểm tra Token...")
            is_valid, msg = check_token_validity(user_input)
            if is_valid:
                print("\n   ✅ \033[92mToken hợp lệ! Đang truy cập...\033[0m")
                try:
                    with open(key_file, "w", encoding="utf-8") as f: f.write(user_input)
                    print("   💾 Đã lưu Key vào máy (key.txt).")
                except Exception as e: print(f"   ⚠️  Lỗi lưu key: {e}")
                time.sleep(1)
                break
            else:
                print(f"\n   ❌ \033[91mLỗi: {msg}\033[0m")
                time.sleep(2)
        except KeyboardInterrupt: sys.exit()

def check_multiple_instances():
    current_pid = os.getpid()
    count = 0
    script_name = "roblox_manager" 
    print(f"🔒 Checking for background instances... (Current PID: {current_pid})")
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if p.info['pid'] == current_pid: continue
            if "python" in p.info['name'].lower() or "autorejoin" in p.info['name'].lower():
                cmdline = p.info['cmdline']
                if cmdline:
                    cmd_str = " ".join(cmdline).lower()
                    if script_name in cmd_str:
                         print(f"⚠️  PHÁT HIỆN TOOL CHẠY NGẦM (PID: {p.info['pid']})")
                         count += 1
        except: pass
    if count > 0:
        print(f"⚠️  CẢNH BÁO: Có {count} bản khác của tool đang chạy!")
        print("👉 Điều này gây ra việc gửi 2 Webhook cùng lúc.")
        time.sleep(3)

if __name__ == "__main__":
    if os.name == 'nt': os.system("color") 
    check_for_updates()
    check_key()
    check_multiple_instances()
    hien_thi_bang("Đang khởi động...")
    print("Dang kiem tra thu vien...")
    try:
        import cv2
    except ImportError: pass

    clean_cookie = re.sub(r'\s+', '', COOKIE_CUA_BAN)
    main_session = requests.Session()
    main_session.cookies.set(".ROBLOSECURITY", clean_cookie, domain="roblox.com")
    
    current_user_id = get_authenticated_user_id(main_session)
    if not current_user_id:
        print("Failed to get User ID. Check Cookie!")
        time.sleep(3)
        
    last_webhook_time = time.time() - 301

    while True:
        try:
            current_time = time.time()
            if current_time - last_webhook_time > 300:
                send_screenshot_to_discord()
                last_webhook_time = current_time

            need_rejoin = False
            if current_user_id:
                presence = check_presence_status(main_session, current_user_id)
                if presence == 2:
                    hien_thi_bang("Detected In Game (Web API). Waiting...")
                    time.sleep(8)
                    continue
                elif presence is not None:
                    hien_thi_bang(f"Web Status: {presence} (Offline/Online). Need Rejoin...")
                    need_rejoin = True
                else: pass
            
            if not need_rejoin and not current_user_id:
                is_running = False
                for p in psutil.process_iter(['name', 'cmdline']):
                    try:
                        if p.info['name'] == "RobloxPlayerBeta.exe":
                            cmdline = p.info['cmdline']
                            if cmdline:
                                cmd_str = " ".join(cmdline).lower()
                                if "--app" in cmd_str: continue
                                if "--play" in cmd_str or "roblox-player:" in cmd_str:
                                    is_running = True
                                    break
                    except: pass
                
                if not is_running:
                    hien_thi_bang("Game Closed (Check Process).")
                    need_rejoin = True
                elif kiem_tra_roblox_treo():
                    hien_thi_bang("Disconnect Banner Detected.")
                    need_rejoin = True
            
            if need_rejoin:
                if bypass_launch():
                    count_seconds = 45 
                    for i in range(count_seconds, 0, -1):
                        hien_thi_bang(f"Waiting for game load... {i}s")
                        time.sleep(1)
                else:
                    for i in range(20, 0, -1):
                        hien_thi_bang(f"Rejoin failed. Retry in {i}s...")
                        time.sleep(1)
            else:
                hien_thi_bang("Monitoring...")
                time.sleep(5)
        except KeyboardInterrupt:
            print("\nTool stopped.")
            break
        except Exception as e:
            print(f"Error Loop: {e}")
            time.sleep(5)
